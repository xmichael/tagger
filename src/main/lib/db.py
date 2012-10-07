import spatialite, configuration, logtool
from DBException import DBException

""" High Level GTR Wrapper arround Spatialite
Supports:
1) Reading tags from uuid
2) Editing + Writing new tags
3) *temporary* Geograph specific functions (might eventually get merged with exiftool ones)
   
#NOTE: Currently implemented as a module (i.e. Singleton in python)
"""

log = logtool.getLogger("db", "gtr")

# UUID of media file
uuid = None
# Lon/Lat Coordinates of media file
coords = None
# Dictionary of tags of media file
tags = None
# stdout Output of last execution
stdout = None

def __init__():
    pass
        
def get_tags():
    """ 
    """
    stdout = spatialite.execute("""
        BEGIN;
        select group_concat(tag) as tags from sessions LEFT OUTER JOIN gtr_tags 
        USING uuid LEFT OUTER JOIN gtr_tag USING tag_id where uuid=?
        COMMIT;""", (uuid,))
    if stdout == None:
        raise DBException("No tags found!")
    return stdout.split(',')

def insert_key(key):
   """ register a new keyword. Noop if keyword exists. """
   res = spatialite.execute("""
       INSERT OR IGNORE INTO gtr_tag(tag) VALUES (?);
       """ , (key,))
   return res

def insert_uuid(uuid, lon=None, lat=None):
    """ register uuid. No-op if uuid already exists. 
    Optional argument lon/lat allow for geocoded uuids.
    """
    if ( not (lon and lat)):
        res = spatialite.execute("""
            INSERT OR IGNORE INTO sessions(uuid) VALUES (?);
        """, (uuid,))
    else:
        res = spatialite.execute("""
            INSERT OR IGNORE INTO sessions(uuid, geom) 
            VALUES (?,PointFromText('POINT('|| ? || ' '|| ? || ')', 4326))
        """, (uuid, lon, lat) )
    return res

def geotag_uuid(uuid, lon, lat):
    """ geocode existing uuid 
    args: 
        lon/lat WGS84 coords.
    """
    log.debug("lon is %s" % lon)
    log.debug("UPDATE sessions SET geom = PointFromText('POINT('|| %s || ' '|| %s || ')', 4326) WHERE uuid='%s'" % (lon,lat,uuid))
    res = spatialite.execute("""
        UPDATE sessions SET geom = PointFromText('POINT('|| ? || ' '|| ? || ')', 4326) WHERE uuid=?
    """, (lon, lat, uuid) )
    return res

def getUUIDs(bbox,key):
    """
    Return all UUIDs in database for mediafile within a BBOX and/or with keyword `key'    
    
    Args:
        bbox (optional): string of comma separated xmin,ymin,xmax,ymax
        key (optional): keyword string to filter by 
    """
    if bbox and not key:
        res = spatialite.execute("""
            SELECT group_concat(uuid) from sessions WHERE sessions.ROWID IN 
            (SELECT pkid FROM idx_sessions_geom WHERE xmin >= ? AND ymin >= ? AND xmax <= ? AND ymax <= ?)
        """, bbox.split(',') )
    if not bbox and key:
        res = spatialite.execute("""
            SELECT group_concat(uuid) from sessions s, gtr_tags tags, gtr_tag tag 
            WHERE s.id = tags.sessions_id and tag.id = tags.tag_id and tag=?
        """, (key,) )
    if bbox and key:
        res = spatialite.execute("""
            SELECT group_concat(uuid) from sessions s, gtr_tags tags, gtr_tag tag 
            WHERE s.id = tags.sessions_id and tag.id = tags.tag_id and tag=?
            AND s.ROWID IN (SELECT pkid FROM idx_sessions_geom 
                WHERE xmin >= ? AND ymin >= ? AND xmax <= ? AND ymax <= ?)
        """, (key,) + tuple(bbox.split(',')) )
    res = ','.join(res[0]) if res[0]!=(None,) else ""
    return res

def getGeographIDs(bbox,key):
    """
    Same as getUUIDs but for geograph files
    """
    if bbox and not key:
        res = spatialite.execute("""
            SELECT group_concat(id) as geograph_ids from geot_geograph g
            WHERE g.ROWID IN (SELECT pkid FROM idx_geot_geograph_geom 
                WHERE xmin >= ? AND ymin >= ? AND xmax <= ? AND ymax <= ?)
            AND id IN ( select id from sample_ids )
        """, bbox.split(',') )
    if not bbox and key:
        #filter out small keywords for keyword-only queries
        if ( len(key) < 3):
            res = [(None,)]
        else:
            res = spatialite.execute("""
                SELECT group_concat(b.gridimage_id) FROM gridimage_base b, gridimage_tag gt,tag  
                WHERE gt.gridimage_id=b.gridimage_id AND tag.tag_id=gt.tag_id 
                AND b.gridimage_id IN ( select id from sample_ids )
                AND tag like ?
                """, ( key + '%' ,))
    if bbox and key:
        # TODO too slow unless one uses a sorted text index and substitutes LIKE with a 
        # x< foobas AND x >= foobar kind of optimization 
        res = spatialite.execute("""
                    SELECT group_concat(id) as geograph_ids from geot_geograph g
                    WHERE g.ROWID IN (SELECT pkid FROM idx_geot_geograph_geom 
                        WHERE xmin >= ? AND ymin >= ? AND xmax <= ? AND ymax <= ?)
                    AND id IN ( select id from sample_ids )
                    -- AND tags like ?
            """, tuple(bbox.split(',')) ) # + (key,)
    res = ','.join(res[0]) if res[0]!=(None,) else ""
    return res    
           
def connect_key(uuid,key):
   """ Associate a uuid with a keyword. Both MUST already exist 
   (so run insert_key&insert_uuid before just in case.) """
   res = spatialite.execute("""
       INSERT OR IGNORE INTO gtr_tags(sessions_id,tag_id) 
           SELECT s.id, t.id from sessions s, gtr_tag t 
           WHERE s.uuid=? and t.tag=?
       """ , (uuid,key))
   return res

def gnearest_dist( lon, lat, dist ):
    """ Find nearest neighbours of lon,lat within dist
        Args:
            lon: Longitude
            lat: Latitude
            dist: distance in metres (assuming data in wgs84)
        Returns:
            nearest sorted by distance
    """
    pass
    

def nearest_dist( lon, lat, dist ):
    """ Find nearest neighbours of lon,lat within dist
        Args:
            lon: Longitude
            lat: Latitude
            dist: distance in metres (assuming data in wgs84)
        Returns:
            nearest sorted by distance
    """
    rad = 0.01 # rough approximation for filter
    #FYI sample_ids are the ones that geograph actually delivers for download as a torrent (about 10% of the whole).
    res = spatialite.execute("""
            SELECT id, realname,title,tags,comment, long,lat, GeodesicLength( MakeLine( MAKEPOINT(?, ?, 4326) , geot_geograph.geom)) AS "Distance (m)"
            FROM geot_geograph 
            WHERE GeodesicLength( MakeLine( MAKEPOINT(?, ?, 4326) , geot_geograph.geom)) < ?
                AND geot_geograph.ROWID IN ( 
                    SELECT pkid FROM idx_geot_geograph_geom WHERE xmin >= ? AND ymin >= ? AND xmax <= ? AND ymax <= ?)
                AND geot_geograph.id IN ( select id from sample_ids )
            ORDER BY 8 
            LIMIT 10;
            """, ( lon, lat, lon, lat ,dist, lon - rad, lat - rad , lon + rad, lat + rad )
        )
    return res

def geograph_byid( id ):
    """ Return lon,lat,tags for geogrph image of given id. Tags are None if they are empty"""
    res = spatialite.execute("""
            select long, lat, tags from geot_geograph where id = ?;
            """, (id,))
    return res[0]
    
def getGeographDir(id):
    """ Guess geograph dir where file <id>.jpg resides
    e.g. an id 1042506 is in <geograph_dir>/10/42/104206.jpg 
    This function only returns the directory name. Just append "/" + str(id)+".jpg" to get the full file path.
    """
    s = str(id).zfill(6)
    return configuration.get_geograph_base_dir() + "/%s/%s" % (s[0:2], s[2:4])

def create_instance(tag):
    """ 
    Return list of all instances with tag
    """
    pass

################### MAIN #######################
if __name__ == "__main__" :
    # IGNORE THESE...
    db = sys.argv[1] #uuid
    try:
        res = db.get_tags()
        print "Stdout is: " + db.stdout
        print "Tags are: " + res
        newtag = { "Software" : 'Some Value' }
        #db.save(newtag)
        print "tags after saving: " + db.get_tags()
    except DBException as e:
        print e
    