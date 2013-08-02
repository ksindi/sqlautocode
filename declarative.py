import sys, re, inspect, operator
import logging
from util import emit, name2label, plural, singular
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import sqlalchemy
from sqlalchemy import exc, and_
from sqlalchemy import MetaData, ForeignKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
try:
    from sqlalchemy.ext.declarative import _deferred_relationship
except ImportError:
    #SA 0.5 support
    # from sqlalchemy.ext.declarative import _deferred_relation as _deferred_relationship
    try:
        from sqlalchemy.ext.declarative import _deferred_relation as _deferred_relationship
    except ImportError:
        #SA 0.8 support
        from sqlalchemy.ext.declarative.clsregistry import _deferred_relationship
    
from sqlalchemy.orm import relation, backref, class_mapper, Mapper

try:
    #SA 0.5 support
    from sqlalchemy.orm import RelationProperty
except ImportError:
    #SA 0.7 support
    try:
        from sqlalchemy.orm.properties import RelationshipProperty, RelationProperty
    except ImportError:
        RelationProperty = None


import config
import constants
from formatter import _repr_coltype_as, foreignkeyconstraint_repr

log = logging.getLogger('saac.decl')
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
log.addHandler(handler)

def by_name(a, b):
    if a.name>b.name:
        return 1
    return -1
def by__name__(a, b):
    if a.__name__ > b.__name__:
        return 1
    return -1

def column_repr(self):

    kwarg = []
    if self.key != self.name:
        kwarg.append( 'key')

    if hasattr(self, 'primary_key') and self.primary_key:
        self.primary_key = True
        kwarg.append( 'primary_key')

    # Kamil edit so we don't get errors when adding objects
    # without columns that have server defaults
    # see: http://docs.sqlalchemy.org/en/rel_0_8/core/schema.html#column-table-metadata-api
    if self.server_default:
        kwarg.append( 'server_default')
        setattr(self, 'server_default', "true")

    if not self.nullable:
        kwarg.append( 'nullable')
    if self.onupdate:
        kwarg.append( 'onupdate')
    if self.default:
        kwarg.append( 'default')
    ks = ', '.join('%s=%r' % (k, getattr(self, k)) for k in kwarg)

    name = self.name

    if not hasattr(config, 'options') and self.config.options.generictypes:
        coltype = repr(self.type)
    elif type(self.type).__module__ == 'sqlalchemy.types':
        coltype = repr(self.type)
    else:
        # Try to 'cast' this column type to a cross-platform type
        # from sqlalchemy.types, dropping any database-specific type
        # arguments.
        for base in type(self.type).__mro__:
            if (base.__module__ == 'sqlalchemy.types' and
                base.__name__ in sqlalchemy.__all__):
                coltype = _repr_coltype_as(self.type, base)
                break
        # FIXME: if a dialect has a non-standard type that does not
        # derive from an ANSI type, there's no choice but to ignore
        # generic-types and output the exact type. However, import
        # headers have already been output and lack the required
        # dialect import.
        else:
            coltype = repr(self.type)

    data = {'name': self.name,
            'type': coltype,
            'constraints': ', '.join(["ForeignKey('%s')"%cn.target_fullname for cn in self.foreign_keys]),
            'args': ks and ks or '',
            }

    if data['constraints']:
        if data['constraints']: data['constraints'] = ', ' + data['constraints']
    if data['args']:
        if data['args']: data['args'] = ', ' + data['args']

    return constants.COLUMN % data

class ModelFactory(object):

    def __init__(self, config):
        self.config = config
        self.used_model_names = []
        self.used_table_names = []
        self.table_model_dict = {} # Kamil Edit
        schema = getattr(self.config, 'schema', None)
        self._metadata = MetaData(bind=config.engine)
        self._foreign_keys = {}
        kw = {}
        self.schemas = None
        if schema:
            if isinstance(schema, (list, tuple)):
                self.schemas = schema
            else:
                self.schemas = (schema, )
            for schema in self.schemas:
                log.info('Reflecting database... schema:%s'%schema)
                self._metadata.reflect(schema=schema)
        else:
            log.info('Reflecting database...')
            self._metadata.reflect()

        self.DeclarativeBase = declarative_base(metadata=self._metadata)

    def _table_repr(self, table):
        s = "Table(u'%s', metadata,\n"%(table.name)
        for column in table.c:
            s += "    %s,\n"%column_repr(column)
        if table.schema:
            s +="    schema='%s'\n"%table.schema
        s+=")"
        return s

    def __repr__(self):
        tables = self.get_many_to_many_tables()
        tables.extend(self.get_tables_with_no_pks())
        models = self.models

        s = StringIO()
        engine = self.config.engine
        if not isinstance(engine, basestring):
            engine = str(engine.url)
        s.write(constants.HEADER_DECL%engine)
        if 'postgres' in engine:
            s.write(constants.PG_IMPORT)

        self.used_table_names = []
        self.used_model_names = []
        self.table_model_dict = {} # Kamil Edit
        for table in tables:
            if table not in self.tables:
                continue
            table_name = self.find_new_name(table.name, self.used_table_names)
            self.used_table_names.append(table_name)
            s.write('%s = %s\n\n'%(table_name, self._table_repr(table)))

        for model in models:
            s.write(model.__repr__())
            s.write("\n\n")

        if self.config.example or self.config.interactive:
            s.write(constants.EXAMPLE_DECL%(models[0].__name__,models[0].__name__))
        if self.config.interactive:
            s.write(constants.INTERACTIVE%([model.__name__ for model in models], models[0].__name__))
        return s.getvalue()

    @property
    def tables(self):
        if self.config.options.tables:
            tables = set(self.config.options.tables)
            return [self._metadata.tables[t] for t in set(self._metadata.tables.keys()).intersection(tables)]
        return self._metadata.tables.values()

    @property
    def table_names(self):
        return [t.name for t in self.tables]
    
    @property
    def models(self):
        if hasattr(self, '_models'):
            return self._models
        self.used_model_names = []
        self.used_table_names = []
        self.table_model_dict = {} # Kamil Edit
        self._models = []
        for table in self.get_non_many_to_many_tables():
            try:
                self._models.append(self.create_model(table))
            except exc.ArgumentError:
                log.warning("Table with name %s ha no primary key. No ORM class created"%table.name)
        self._models.sort(by__name__)
        return self._models
    
    def get_tables_with_no_pks(self):
        r = []
        for table in self.get_non_many_to_many_tables():
            if not [c for c in table.columns if c.primary_key]:
                r.append(table)
        return r
    
    def model_table_lookup(self):
        if hasattr(self, '_model_table_lookup'):
            return self._model_table_lookup
        self._model_table_lookup = dict(((m.__table__.name, m.__name__) for m in self.models))
        return self._model_table_lookup

    def find_new_name(self, prefix, used, i=0):
        if i!=0:
            prefix = "%s%d"%(prefix, i)
        if prefix in used:
            prefix = prefix
            return self.find_new_name(prefix, used, i+1)
        return prefix


    def create_model(self, table):
        #partially borrowed from Jorge Vargas' code
        #http://dpaste.org/V6YS/
        log.debug('Creating Model from table: %s'%table.name)

        model_name = self.find_new_name(singular(name2label(table.name)), self.used_model_names)
        self.used_model_names.append(model_name)
        is_many_to_many_table = self.is_many_to_many_table(table)
        table_name = self.find_new_name(table.name, self.used_table_names)
        self.used_table_names.append(table_name)
        self.table_model_dict[table_name] = model_name # Kamil Edit

        mtl = self.model_table_lookup

            
        class Temporal(self.DeclarativeBase):
            __table__ = table
            
            @classmethod
            def _relation_repr(cls, rel):
                target = rel.argument
                if target and inspect.isfunction(target):
                    target = target()
                if isinstance(target, Mapper):
                    target = target.class_
                target = target.__name__
                primaryjoin=''
                lookup = mtl()
                foo = rel.key
                if rel.primaryjoin is not None and hasattr(rel.primaryjoin, 'right'):
                    right_lookup = lookup.get(rel.primaryjoin.right.table.name, '%s.c'%rel.primaryjoin.right.table.name)
                    left_lookup = lookup.get(rel.primaryjoin.left.table.name, '%s.c'%rel.primaryjoin.left.table.name)
                    
                    primaryjoin = ", primaryjoin='%s.%s==%s.%s'"%(left_lookup,
                                                                  rel.primaryjoin.left.name,
                                                                  right_lookup,
                                                                  rel.primaryjoin.right.name)
                elif hasattr(rel, '_as_string'):
                    primaryjoin=', primaryjoin="%s"'%rel._as_string
                    
                secondary = ''
                secondaryjoin = ''
                if rel.secondary is not None:
                    """
                    **HACK**: If there is a secondary relationship like between Venue, Event, and Event_Type, then I'm only
                    going show a primary relationship. So that I get the relational definition for security Security 
                    "Events = relationship('Event',  primaryjoin='Venue.id==Event.venue_id')" and not 
                    "Event_Types = relation('EventType', primaryjoin='Venue.id==Event.venue_id', secondary=Event, secondaryjoin='Event.event_type_id==EventType.id')"
                    """
                    if rel.secondary.name in self.table_model_dict:
                        target = self.table_model_dict[rel.secondary.name]
                    else:
                        target = self.find_new_name(singular(name2label(rel.secondary.name)), []) # **HACK**
                    secondary = ''
                    secondaryjoin = ''
                    foo = plural(rel.secondary.name)
                backref=''
#                if rel.backref:
#                    backref=", backref='%s'"%rel.backref.key
                return "%s = relationship('%s'%s%s%s%s)"%(foo, target, primaryjoin, secondary, secondaryjoin, backref)
                
            @classmethod
            def __repr__(cls):
                log.debug('repring class with name %s'%cls.__name__)
                try:
                    mapper = None
                    try:
                        mapper = class_mapper(cls)
                    except exc.InvalidRequestError:
                        log.warn("A proper mapper could not be generated for the class %s, no relations will be created"%model_name)
                    s = ""
                    s += "class "+model_name+'(DeclarativeBase):\n'
                    if is_many_to_many_table:
                        s += "    __table__ = %s\n\n"%table_name
                    else:
                        s += "    __tablename__ = '%s'\n\n"%table_name
                        if hasattr(cls, '__table_args__'):
                            #if cls.__table_args__[0]:
                                #for fkc in cls.__table_args__[0]:
                                #    fkc.__class__.__repr__ = foreignkeyconstraint_repr
                                #    break
                            s+="    __table_args__ = %s\n\n"%cls.__table_args__
                        s += "    #column definitions\n"
                        for column in sorted(cls.__table__.c, by_name):
                            s += "    %s = %s\n"%(column.name, column_repr(column))
                    s += "\n    #relation definitions\n"
                    ess = s
                    # this is only required in SA 0.5
                    if mapper and RelationProperty: 
                        for prop in mapper.iterate_properties:
                            if isinstance(prop, RelationshipProperty):
                                s+='    %s\n'%cls._relation_repr(prop)
                    return s
                    
                except Exception, e:
                    log.error("Could not generate class for: %s"%cls.__name__)
                    from traceback import format_exc
                    log.error(format_exc())
                    return ''
                    

        #hack the class to have the right classname
        Temporal.__name__ = model_name
        
        #set up some blank table args
        Temporal.__table_args__ = {} 
        
        #add in the schema
        if self.config.schema:
            Temporal.__table_args__[1]['schema'] = table.schema

        #trick sa's model registry to think the model is the correct name
        if model_name != 'Temporal':
            Temporal._decl_class_registry[model_name] = Temporal._decl_class_registry['Temporal']
            del Temporal._decl_class_registry['Temporal']

        #add in single relations
        fks = self.get_single_foreign_keys_by_column(table)
        for column, fk in fks.iteritems():
            related_table = fk.column.table
            if related_table not in self.tables:
                continue

            log.info('    Adding <primary> foreign key for:%s'%related_table.name)
            backref_name = plural(table_name)
            rel = relation(singular(name2label(related_table.name, related_table.schema)), 
                           primaryjoin=column==fk.column)#, backref=backref_name)
        
            setattr(Temporal, related_table.name, _deferred_relationship(Temporal, rel))
        
        #add in the relations for the composites
        for constraint in table.constraints:
            if isinstance(constraint, ForeignKeyConstraint):
                if len(constraint.elements) >1:
                    related_table = constraint.elements[0].column.table
                    related_classname = singular(name2label(related_table.name, related_table.schema))
                                    
                    primary_join = "and_(%s)"%', '.join(["%s.%s==%s.%s"%(model_name,
                                                                        k.parent.name,
                                                                        related_classname,
                                                                        k.column.name)
                                                      for k in constraint.elements])
                    rel = relation(related_classname,
                                   primaryjoin=primary_join
#                                   foreign_keys=[k.parent for k in constraint.elements]
                               )
                    
                    rel._as_string = primary_join
                    setattr(Temporal, related_table.name, rel) # _deferred_relationship(Temporal, rel))
                
        
        #add in many-to-many relations
        for join_table in self.get_related_many_to_many_tables(table.name):

            if join_table not in self.tables:
                continue
            primary_column = [c for c in join_table.columns if c.foreign_keys and list(c.foreign_keys)[0].column.table==table][0]
            
            for column in join_table.columns:
                if column.foreign_keys:
                    key = list(column.foreign_keys)[0]
                    if key.column.table is not table:
                        related_column = related_table = list(column.foreign_keys)[0].column
                        related_table = related_column.table
                        if related_table not in self.tables:
                            continue
                        log.info('    Adding <secondary> foreign key(%s) for:%s'%(key, related_table.name))
                        setattr(Temporal, plural(related_table.name), _deferred_relationship(Temporal,
                                                                                         relation(singular(name2label(related_table.name,
                                                                                                             related_table.schema)),
                                                                                                  secondary=join_table,
                                                                                                  primaryjoin=list(primary_column.foreign_keys)[0].column==primary_column,
                                                                                                  secondaryjoin=column==related_column
                                                                                                  )))
                        break;
        
        return Temporal

    def get_table(self, name):
        """(name) -> sqlalchemy.schema.Table
        get the table definition with the given table name
        """
        if self.schemas:
            for schema in self.schemas:
                if schema and not name.startswith(schema):
                    new_name = '.'.join((schema, name))
                table = self._metadata.tables.get(new_name, None)
                if table is not None:
                    return table
        return self._metadata.tables[name]

    def get_single_foreign_keys_by_column(self, table):
        keys_by_column = {}
        fks = self.get_foreign_keys(table)
        for table, keys in fks.iteritems():
            if len(keys) == 1:
                fk = keys[0]
                keys_by_column[fk.parent] = fk
        return keys_by_column

    def get_composite_foreign_keys(self, table):
        l = []
        fks = self.get_foreign_keys(table)
        for table, keys in fks.iteritems():
            if len(keys)>1:
                l.append(keys)
        return l
        
        
    def get_foreign_keys(self, table):
        if table in self._foreign_keys:
            return self._foreign_keys[table]
        
        fks = table.foreign_keys

        #group fks by table.  I think this is needed because of a problem in the sa reflection alg.
        grouped_fks = {}
        for key in fks:
            grouped_fks.setdefault(key.column.table, []).append(key)
        
        self._foreign_keys[table] = grouped_fks
        return grouped_fks
    
#        fks = {}
#        for column in table.columns:
#            if len(column.foreign_keys)>0:
#                fks.setdefault(column.name, []).extend(column.foreign_keys)
#        return fks

    def is_many_to_many_table(self, table):
        fks = self.get_single_foreign_keys_by_column(table).values()
        return len(fks) >= 2

    def is_only_many_to_many_table(self, table):
        return len(self.get_single_foreign_keys_by_column(table)) == 2 and len(table.c) == 2

    def get_many_to_many_tables(self):
        if not hasattr(self, '_many_to_many_tables'):
            self._many_to_many_tables = [table for table in self._metadata.tables.values() if self.is_many_to_many_table(table)]
        return sorted(self._many_to_many_tables, by_name)

    def get_non_many_to_many_tables(self):
        tables = [table for table in self.tables if not(self.is_only_many_to_many_table(table))]
        return sorted(tables, by_name)

    def get_related_many_to_many_tables(self, table_name):
        tables = []
        src_table = self.get_table(table_name)
        for table in self.get_many_to_many_tables():
            for column in table.columns:
                if column.foreign_keys:
                    key = list(column.foreign_keys)[0]
                    if key.column.table is src_table:
                        tables.append(table)
                        break
        return sorted(tables, by_name)
