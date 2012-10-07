# sessions Singleton to provide connection to sqlite  (singletons are plain modules aka static classes in python).
# No cleanup/closing is required. All commit are atomic.

import sqlite3
import configuration,helper

# global sqlite connection.
_conn = None

def getConnection():
    global _conn
    if _conn == None:
        _conn = sqlite3.connect( configuration.getSessionsDB() )
    return _conn

def execute(sql, subst):
    """ execute SQL transaction.
    
    Args
        sql: SQL statement with `?' for substitution values
        subst: list of substitutions
    
    Returns
        SQL response as a list
    """
    c = _conn.cursor()
    c.execute(sql, subst)
    _conn.commit()
    response = c.fetchall()
    c.close()
    return response

# Shortcut functions for session management #
#######################################################

def getSession(uuid):
    """ Return non-media metadata based on uuid. Use exiftool to get the actualmetadata of file """
    res = execute('SELECT * from sessions where uuid=?', (uuid,) )
    return res
        
def insertSession( ip, uuid, filename ):
    """ Insert a new session. Automatically adds mtime/ctime """
    res = execute('''INSERT INTO sessions (ip, uuid, filename, mtime, ctime) VALUES (?,?,?, strftime('%s','now'), strftime('%s','now') )''' , ( ip, uuid, filename ) )

def updateSession( uuid, filename, ip ):
    """ Update an exisiting session. Automatically updates mtime. """
    res = execute('''UPDATE sessions (ip, uuid, filename, mtime, ctime) VALUES (?,?,?, strftime('%s','now'), strftime('%s','now') )''' , ( ip, uuid, filename ) )

# Functions for sanity checking #
#################################

def checkUUIDs():
    """ print duplicate uuids in database """
    pass

def selectDaysOld(days):
    """ return session with mtime older than X days """
    pass

if __name__ == "__main__":
    uuid = 'eea8afd36f63491db3bedc5f43851d71'
    getConnection()
    print insertSession( '127.0.0.1', uuid, "MyMedia.jpg")
    print `getSession(uuid)`
    