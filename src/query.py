# -*- coding: utf-8 -*-

"""
Copyright (C) 2008-2012 Wolfgang Rohdewald <wolfgang@rohdewald.de>

partially based on C++ code from:
    Copyright (C) 2006 Mauricio Piacentini <mauricio@tabuleiro.com>

kajongg is free software you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


"""

import os, sys, time, datetime, traceback, random
from collections import defaultdict
from PyQt4.QtCore import QVariant, QString
from util import logInfo, logWarning, logError, logDebug, appdataDir, m18ncE, xToUtf8
from common import InternalParameters, Debug, IntDict
from PyQt4.QtSql import QSqlQuery, QSqlDatabase, QSql

class Transaction(object):
    """a helper class for SQL transactions"""
    def __init__(self, name=None, dbhandle=None):
        """start a transaction"""
        self.dbhandle = dbhandle or Query.dbhandle
        if name is None:
            dummy, dummy, name, dummy = traceback.extract_stack()[-2]
        self.name = '%s on %s' % (name or '', self.dbhandle.databaseName())
        if not self.dbhandle.transaction():
            logWarning('%s cannot start: %s' % (
                    self.name, self.dbhandle.lastError().text()))
        self.active = True
        self.startTime = datetime.datetime.now()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, trback):
        """end the transaction"""
        diff = datetime.datetime.now() - self.startTime
        if diff > datetime.timedelta(seconds=1.0):
            logWarning('%s took %d.%06d seconds' % (
                    self.name, diff.seconds, diff.microseconds))
        if self.active and trback is None:
            if not self.dbhandle.commit():
                logWarning('%s: cannot commit: %s' % (
                        self.name, self.dbhandle.lastError().text()))
        else:
            if not self.dbhandle.rollback():
                logWarning('%s: cannot rollback: %s' % (
                        self.name, self.dbhandle.databaseName()))
            if exc_type:
                exc_type(exc_value)

    def rollback(self):
        """explicit rollback by the caller"""
        self.dbhandle.rollback()
        self.active = False

class Query(object):
    """a more pythonic interface to QSqlQuery. We could instead use
    the python sqlite3 module but then we would either have to do
    more programming for the model/view tables, or we would have
    two connections to the same database.
    For selecting queries we fill a list with ALL records.
    Every record is a list of all fields. q.records[0][1] is record 0, field 1.
    For select, we also convert to python data
    types - as far as we need them"""
    dbhandle = None

    localServerName = m18ncE('kajongg name for local game server', 'Local Game')

    def __init__(self, cmdList, args=None, dbHandle=None, silent=False, mayFail=False):
        """we take a list of sql statements. Only the last one is allowed to be
        a select statement.
        Do prepared queries by passing a single query statement in cmdList
        and the parameters in args. If args is a list of lists, execute the
        prepared query for every sublist.
        If dbHandle is passed, use that for db access.
        Else if the default dbHandle (Query.dbhandle) is defined, use it."""
        # pylint: disable=R0912
        # pylint says too many branches
        silent |= not Debug.sql
        self.dbHandle = dbHandle or Query.dbhandle
        assert self.dbHandle
        preparedQuery = not isinstance(cmdList, list) and bool(args)
        self.query = QSqlQuery(self.dbHandle)
        self.msg = None
        self.records = []
        if not isinstance(cmdList, list):
            cmdList = list([cmdList])
        self.cmdList = cmdList
        for cmd in cmdList:
            retryCount = 0
            while retryCount < 100:
                self.lastError = None
                if preparedQuery:
                    self.query.prepare(cmd)
                    if not isinstance(args[0], list):
                        args = list([args])
                    for dataSet in args:
                        if not silent:
                            _, utf8Args = xToUtf8(u'', dataSet)
                            logDebug("{cmd} [{args}]".format(cmd=cmd, args=", ".join(utf8Args)))
                        for value in dataSet:
                            self.query.addBindValue(QVariant(value))
                        self.success = self.query.exec_()
                        if not self.success:
                            break
                else:
                    if not silent:
                        logDebug(cmd)
                    self.success = self.query.exec_(cmd)
                if self.success or self.query.lastError().number() not in (5, 6):
                    # 5: database locked, 6: table locked. Where can we get symbols for this?
                    break
                time.sleep(0.1)
                retryCount += 1
            if not self.success:
                self.lastError = unicode(self.query.lastError().text())
                self.msg = 'ERROR in %s: %s' % (self.dbHandle.databaseName(), self.lastError)
                if mayFail:
                    if not silent:
                        logDebug(self.msg)
                else:
                    logError(self.msg)
                return
        self.records = None
        self.fields = None
        if self.query.isSelect():
            self.retrieveRecords()

    def rowcount(self):
        """how many rows were affected?"""
        return self.query.numRowsAffected()

    def retrieveRecords(self):
        """get all records from SQL into a python list"""
        record = self.query.record()
        self.fields = [record.field(x) for x in range(record.count())]
        self.records = []
        while self.query.next():
            self.records.append([self.__convertField(x) for x in range(record.count())])

    def __convertField(self, idx):
        """convert a QSqlQuery field into a python value"""
        result = self.query.value(idx).toPyObject()
        if isinstance(result, QString):
            result = unicode(result)
        if isinstance(result, long) and -sys.maxint -1 <= result <= sys.maxint:
            result = int(result)
        return result

    @staticmethod
    def hasTable(table):
        """does the table contain table?"""
        query = Query('select name from sqlite_master WHERE type = "table" and name=?',
                list([table]), silent=True)
        tables = (x[0] for x in query.records)
        return table in tables

    @staticmethod
    def tableHasField(table, field):
        """does the table contain a column named field?"""
        query = QSqlQuery(Query.dbhandle)
        query.exec_('select * from %s' % table)
        record = query.record()
        for idx in range(record.count()):
            if record.fieldName(idx) == field:
                return True

    schema = {}
    schema['player'] = """
        id INTEGER PRIMARY KEY,
        name TEXT unique"""
    schema['game'] = """
            id integer primary key,
            seed text,
            autoplay integer default 0,
            starttime text default current_timestamp,
            endtime text,
            ruleset integer references ruleset(id),
            p0 integer constraint fk_p0 references player(id),
            p1 integer constraint fk_p1 references player(id),
            p2 integer constraint fk_p2 references player(id),
            p3 integer constraint fk_p3 references player(id)"""
    schema['score'] = """
            game integer constraint fk_game references game(id),
            hand integer,
            data text,
            manualrules text,
            rotated integer,
            notrotated integer,
            player integer constraint fk_player references player(id),
            scoretime text,
            won integer,
            penalty integer default 0,
            prevailing text,
            wind text,
            points integer,
            payments integer,
            balance integer"""
    schema['ruleset'] = """
            id integer primary key,
            name text,
            hash text,
            description text"""
    schema['rule'] = """
            ruleset integer,
            list integer,
            position integer,
            name text,
            definition text,
            points text,
            doubles text,
            limits text,
            parameter text,
            primary key(ruleset,list,position),
            unique (ruleset,name)"""
    schema['server'] = """
                url text,
                lastname text,
                lasttime text,
                lastruleset integer,
                primary key(url)"""
    schema['passwords'] = """
                url text,
                player integer,
                password text"""
    schema['general'] = """
                ident text"""

    @staticmethod
    def sqlForCreateTable(table):
        """the SQL command for creating 'table'"""
        return "create table %s(%s)" % (table, Query.schema[table])

    @staticmethod
    def createTable(table):
        """create a single table using the predefined schema"""
        if table not in Query.dbhandle.driver().tables(QSql.Tables):
            Query(Query.sqlForCreateTable(table))

    @staticmethod
    def createTables():
        """creates empty tables"""
        for table in ['player', 'game', 'score', 'ruleset', 'rule']:
            Query.createTable(table)
        Query.createIndex('idxgame', 'score(game)')

        if InternalParameters.isServer:
            Query('ALTER TABLE player add password text')
        else:
            Query.createTable('passwords')
            Query.createTable('server')

    @staticmethod
    def createIndex(name, cmd):
        """only try to create it if it does not yet exist. Do not use create if not exists because
        we want debug output only if we really create the index"""
        if not Query("select 1 from sqlite_master where type='index' and name='%s'" % name,
                silent=True).records:
            Query("create index %s on %s" % (name, cmd))

    @staticmethod
    def cleanPlayerTable():
        """remove now unneeded columns host, password and make names unique"""
        playerCounts = IntDict()
        names = {}
        keep = {}
        for nameId, name in Query('select id,name from player').records:
            playerCounts[name] += 1
            names[int(nameId)] = name
        for name, counter in defaultdict.items(playerCounts):
            nameIds = [x[0] for x in names.items() if x[1] == name]
            keepId = nameIds[0]
            keep[keepId] = name
            if counter > 1:
                for nameId in nameIds[1:]:
                    Query('update score set player=%d where player=%d' % (keepId, nameId))
                    Query('update game set p0=%d where p0=%d' % (keepId, nameId))
                    Query('update game set p1=%d where p1=%d' % (keepId, nameId))
                    Query('update game set p2=%d where p2=%d' % (keepId, nameId))
                    Query('update game set p3=%d where p3=%d' % (keepId, nameId))
                    Query('delete from player where id=%d' % nameId)
        Query('drop table player')
        Query.createTable('player')
        for nameId, name in keep.items():
            Query('insert into player(id,name) values(?,?)', list([nameId, name]))

    @staticmethod
    def removeGameServer():
        """drops column server from table game. Sqlite3 cannot drop columns"""
        Query('create table gameback(%s)' % Query.schema['game'])
        Query('insert into gameback '
            'select id,seed,autoplay,starttime,endtime,ruleset,p0,p1,p2,p3 from game')
        Query('drop table game')
        Query('create table game(%s)' % Query.schema['game'])
        Query('insert into game '
            'select id,seed,autoplay,starttime,endtime,ruleset,p0,p1,p2,p3 from gameback')
        Query('drop table gameback')

    @staticmethod
    def haveGamesWithRegex():
        """we do not support Regex rules anymore.
        Mark all games using them as finished - until somebody
        complains. So for now always return False"""
        if not Query.hasTable('usedrule'):
            return
        usedRegexRulesets = Query("select distinct ruleset from usedrule "
            "where definition not like 'F%' "
            "and definition not like 'O%' "
            "and definition not like 'int%' "
            "and definition not like 'bool%' "
            "and definition<>'' "
            "and definition not like 'XEAST9X%'").records
        usedRegexRulesets = list(unicode(x[0]) for x in usedRegexRulesets)
        if not usedRegexRulesets:
            return
        openRegexGames = Query("select id from game "
            "where endtime is null "
            "and ruleset in (%s)" % ','.join(usedRegexRulesets)).records
        openRegexGames = list(x[0] for x in openRegexGames)
        if not openRegexGames:
            return
        logInfo('Marking games using rules with regular expressions as finished: %s' % openRegexGames)
        for openGame in openRegexGames:
            endtime = datetime.datetime.now().replace(microsecond=0).isoformat()
            Query('update game set endtime=? where id=?',
                list([endtime, openGame]))

    @staticmethod
    def removeUsedRuleset():
        """eliminate usedruleset and usedrule"""
        if Query.hasTable('usedruleset'):
            if Query.hasTable('ruleset'):
                Query('UPDATE ruleset set id=-id where id>0')
                Query('INSERT OR IGNORE INTO usedruleset SELECT * FROM ruleset')
                Query('DROP TABLE ruleset')
            Query('ALTER TABLE usedruleset RENAME TO ruleset')
        if Query.hasTable('usedrule'):
            if Query.hasTable('rule'):
                Query('UPDATE rule set ruleset=-ruleset where ruleset>0')
                Query('INSERT OR IGNORE INTO usedrule SELECT * FROM rule')
                Query('DROP TABLE rule')
            Query('ALTER TABLE usedrule RENAME TO rule')
        query = Query("select count(1) from sqlite_master "
            "where type='table' and tbl_name='ruleset' and sql like '%name text unique,%'", silent=True)
        if int(query.records[0][0]):
            # make name non-unique. Needed for used rulesets: Content may change with identical name
            # and we now have both ruleset templates and copies of used rulesets in the same table
            Query([
                    'create table temp(%s)' % Query.schema['ruleset'],
                    'insert into temp select id,name,hash,description from ruleset',
                    'drop table ruleset',
                    Query.sqlForCreateTable('ruleset'),
                    'insert into ruleset select * from temp',
                    'drop table temp'])

    @staticmethod
    def upgradeDb():
        """upgrade any version to current schema"""
        Query.createIndex('idxgame', 'score(game)')
        if not Query.tableHasField('game', 'autoplay'):
            Query('ALTER TABLE game add autoplay integer default 0')
        if not Query.tableHasField('score', 'penalty'):
            Query('ALTER TABLE score add penalty integer default 0')
            Query("UPDATE score SET penalty=1 WHERE manualrules LIKE "
                    "'False Naming%' OR manualrules LIKE 'False Decl%'")
        if Query.tableHasField('player', 'host'):
            Query.cleanPlayerTable()
        if InternalParameters.isServer:
            if not Query.tableHasField('player', 'password'):
                Query('ALTER TABLE player add password text')
        else:
            Query.createTable('passwords')
            if not Query.tableHasField('server', 'lastruleset'):
                Query('alter table server add lastruleset integer')
        if Query.tableHasField('game', 'server'):
            Query.removeGameServer()
        if not Query.tableHasField('score', 'notrotated'):
            Query('ALTER TABLE score add notrotated integer default 0')
        Query.removeUsedRuleset()

    @staticmethod
    def generateDbIdent():
        """make sure the database has a unique ident and get it"""
        Query.createTable('general')
        records = Query('select ident from general').records
        assert len(records) < 2
        if records:
            action = 'found'
            InternalParameters.dbIdent = records[0][0]
        else:
            action = 'generated'
            InternalParameters.dbIdent = str(random.randrange(100000000000))
            Query("INSERT INTO general(ident) values('%s')" % InternalParameters.dbIdent)
        if Debug.sql:
            logDebug('%s dbIdent for %s: %s' % (action, Query.dbhandle.databaseName(), InternalParameters.dbIdent))

    @staticmethod
    def initDb():
        """open the db, create or update it if needed.
        sets Query.dbhandle."""
        dbhandle = QSqlDatabase("QSQLITE")
        if InternalParameters.isServer:
            name = 'kajonggserver.db'
        else:
            name = 'kajongg.db'

        dbpath = InternalParameters.dbPath.decode('utf-8') if InternalParameters.dbPath else appdataDir() + name
        dbhandle.setDatabaseName(dbpath)
        dbExisted = os.path.exists(dbpath)
        if Debug.sql:
            logDebug('%s database %s' % \
                ('using' if dbExisted else 'creating', dbpath))
        # timeout in msec:
        dbhandle.setConnectOptions("QSQLITE_BUSY_TIMEOUT=2000")
        if not dbhandle.open():
            logError('%s %s' % (str(dbhandle.lastError().text()), dbpath))
            return
        Query.dbhandle = dbhandle
        try:
            if not dbExisted:
                with Transaction():
                    Query.createTables()
            else:
                if Query.haveGamesWithRegex():
                    raise Exception('you have old games with regular expressions')
                with Transaction():
                    Query.upgradeDb()
            Query.generateDbIdent()
        except BaseException, exc:
            print(exc)
            dbhandle.close()
            Query.dbhandle = None
            return False
        return True
