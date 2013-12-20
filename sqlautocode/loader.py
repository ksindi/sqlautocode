import sqlalchemy
from sqlalchemy.databases import postgres


class AutoLoader(object):
    pass

class PGIndexLoader(AutoLoader):
    """ SA does not load indexes for us """

    sql4indexes = "SELECT indexname, tablename, indexdef FROM pg_indexes"

    def __init__(self, db):
        ix = {}
        for name, tbl_name, sqltext in db.execute(self.sql4indexes):
            ix.setdefault(tbl_name, []).append( (name, sqltext) )
        self._indexes = ix

    def indexes(self, table):
        return [self._index_from_def(name, sqltext, table)
                for name, sqltext in self._indexes.get(table.name, ())]

    def _index_from_def(self, name, sqltext, table):
        # CREATE UNIQUE INDEX name ON "tablename" USING btree (columnslist)
        unique = ' UNIQUE ' in sqltext
        cols = sqltext.split(' (')[1].split(')')[0].split(',')
        cols = [table.columns[cname.strip().replace('"', '')]
                for cname in cols]
        name = name.encode('utf-8')
        return sqlalchemy.Index(name, unique=unique, *cols)

postgres.PGDialect.indexloader = PGIndexLoader
