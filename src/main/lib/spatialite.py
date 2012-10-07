## This is a Singleton class to return a spatialite instance. 
## Note to java coders: Singletons in python are just modules with plain functions.
##
## Usage:
##      import spatialite
##      output = spatialite.execute("select HEX(GeomFromText(?));",('POINT(788703.57 4645636.3)',))
## The output is a a tuple of lists. To get the 2nd field from 3rd row just use output[2][1] (0-based index)

import sys
## Devel's python has "surprisingly" disabled sqlite3 support unlike 99.9% of sane python installations.
import pysqlite2.dbapi2 as db

import configuration

### Constants ###

# full path of sqlite3 database
DB = configuration.getdb()

# full path of libspatialite.so.3
SPATIALPLUGIN = configuration.get_libspatialite()

# creating/connecting the test_db
con = db.connect(DB, check_same_thread=False)
con.enable_load_extension(True)
con.load_extension(SPATIALPLUGIN)
con.enable_load_extension(False)

def execute(sql, args=()):
    """
        Execute sql using args for sql substitution
        
        Args:
            sql:  SQL statement
            args (optional) : list of susbtitution values
    """
    res = con.execute(sql, args)    
    con.commit()
    return res.fetchall()

# Example:
if __name__ == "__main__":
    # Test geometry functions
    print execute("select HEX(GeomFromText(?));",('POINT(788703.57 4645636.3)',))
    # See if a tag exists!
    #(implement custom tags in db) print execute('select exists ( select tag_id from gtr_tag where tag="mytag");')[0][0] # 1 or 0
    # Find neighbours
    print execute(""" SELECT * FROM geot_geograph 
    WHERE GeodesicLength( MakeLine( MAKEPOINT(-3.27253,55.96394, 4326) , geot_geograph.geom)) < 1000.0
        AND geot_geograph.ROWID IN ( 
          SELECT pkid FROM idx_geot_geograph_geom WHERE xmax >= -3.28253 AND ymax >= 55.95394 AND xmin <= -3.26253 AND ymin <= 55.97394
        )
        AND geot_geograph.id IN ( select id from sample_ids )
    ORDER BY 2 LIMIT 10;
   """)[9]
#################
