import os
from sqlalchemy import *


metadata = MetaData()

environment =  Table('environment', metadata,
    Column(u'environment_id', Numeric(precision=10, scale=0, asdecimal=True), primary_key=True, nullable=False),
            Column(u'environment_name', String(length=100, convert_unicode=False, assert_unicode=None), primary_key=False, nullable=False),
            Column(u'database_host', String(length=100, convert_unicode=False, assert_unicode=None), primary_key=False, nullable=False),
            Column(u'database_port', String(length=5, convert_unicode=False, assert_unicode=None), primary_key=False, nullable=False),
            Column(u'database_sid', String(length=32, convert_unicode=False, assert_unicode=None), primary_key=False, nullable=False),
            Column(u'database_user', String(length=100, convert_unicode=False, assert_unicode=None), primary_key=False, nullable=False),
            Column(u'database_pass', String(length=100, convert_unicode=False, assert_unicode=None), primary_key=False, nullable=False),
    
    
    )


report =  Table('report', metadata,
    Column(u'report_id', Numeric(precision=10, scale=0, asdecimal=True), primary_key=True, nullable=False),
            Column(u'environment_id', Numeric(precision=10, scale=0, asdecimal=True), primary_key=False, nullable=False),
            Column(u'report_name', String(length=50, convert_unicode=False, assert_unicode=None), primary_key=False, nullable=False),
            Column(u'report_description', String(length=4000, convert_unicode=False, assert_unicode=None), primary_key=False),
            Column(u'deleted', Numeric(precision=1, scale=0, asdecimal=True), primary_key=False, nullable=False),
            Column(u'created_date', DateTime(timezone=False), primary_key=False, nullable=False),
            Column(u'created_by', Numeric(precision=10, scale=0, asdecimal=True), primary_key=False, nullable=False),
            Column(u'updated_date', DateTime(timezone=False), primary_key=False, nullable=False),
            Column(u'updated_by', Numeric(precision=10, scale=0, asdecimal=True), primary_key=False, nullable=False),
            Column(u'deleted_date', DateTime(timezone=False), primary_key=False),
            Column(u'deleted_by', Numeric(precision=10, scale=0, asdecimal=True), primary_key=False),
            ForeignKeyConstraint([u'environment_id'], [u'environment.environment_id'], name='REPORT_FK_ENV_ID'),
    
    )


ui_report =  Table('ui_report', metadata,
    Column(u'ui_report_id', Numeric(precision=10, scale=0, asdecimal=True), primary_key=True, nullable=False),
            Column(u'report_id', Numeric(precision=10, scale=0, asdecimal=True), primary_key=False, nullable=False),
            Column(u'environment_id', Numeric(precision=10, scale=0, asdecimal=True), primary_key=False, nullable=False),
            Column(u'ui_report_name', String(length=100, convert_unicode=False, assert_unicode=None), primary_key=False, nullable=False),
            Column(u'ui_report_description', String(length=4000, convert_unicode=False, assert_unicode=None), primary_key=False),
            Column(u'enabled', Numeric(precision=1, scale=0, asdecimal=True), primary_key=False, nullable=False),
            Column(u'deleted', Numeric(precision=1, scale=0, asdecimal=True), primary_key=False, nullable=False),
            Column(u'created_date', DateTime(timezone=False), primary_key=False, nullable=False),
            Column(u'created_by', Numeric(precision=10, scale=0, asdecimal=True), primary_key=False, nullable=False),
            Column(u'updated_date', DateTime(timezone=False), primary_key=False, nullable=False),
            Column(u'updated_by', Numeric(precision=10, scale=0, asdecimal=True), primary_key=False, nullable=False),
            Column(u'deleted_date', DateTime(timezone=False), primary_key=False),
            Column(u'deleted_by', Numeric(precision=10, scale=0, asdecimal=True), primary_key=False),
            ForeignKeyConstraint([u'report_id'], [u'report.report_id'], name='UI_REPORT_FK_REPORT_ID'),
            ForeignKeyConstraint([u'environment_id'], [u'environment.environment_id'], name='UI_REPORT_FK_ENV_ID'),
    
    )

bound = False
def make_test_db():
    global bound, metadata
    if not bound:
        testdb_filename = os.path.abspath(os.path.dirname(__file__))+'/data/testdb.db'
        #try:
        #    os.remove(testdb_filename)
        #except OSError:
        #    pass
        
        db = 'sqlite:///'+testdb_filename
        
        test_engine = create_engine(db)
        metadata.bind =test_engine
        #metadata.create_all()
        bound = True
    return metadata

bound_multi = False
metadata_multi = MetaData()
def make_test_db_multi():
    global bound_multi, metadata_multi
    if not bound_multi:
        testdb_filename = os.path.abspath(os.path.dirname(__file__))+'/data/multi.db'
        #testdb_filename = os.path.abspath(os.path.dirname(__file__))+'/data/devdata.db'
        
        db = 'sqlite:///'+testdb_filename
        
        test_engine = create_engine(db)
        metadata_multi.bind =test_engine
        metadata_multi.reflect()
        bound_multi = True
    return metadata_multi


    