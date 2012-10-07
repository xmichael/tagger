## Just some static utility functions that didn't justify the creation of a class

import sys
import exiftool
from bottle import template
from ExifException import ExifException

### Constants ###

#################

def strfilter(text , remove):
    """
    remove chars defined in "remove" from "text"
    """
    return ''.join([c for c in text if c not in remove])

def getBaseName(filename):
    """ Converts uploaded filename from something like "C\foo\windows\name.zip to name """
    #remove suffix
    tmp = filename
    tmp = tmp[ :tmp.rfind('.')]
    #remove funny chars
    return strfilter(tmp , "\\/")

def probedata(filepath, group="ALL", uuid=None, showgroups=False):
    """Uses ExifTool to probe metadata of a media file and return a python dict with those metadata.

    Args:
        filepath (str): File object of the main data file (e.g. foo.avi).
        group (str): (optional) fetch ALL,EXIF,XMP... tags.
        uuid (str): (optional) if uuid is defined and the group is ALL or Custom then fetch tags from the sqlite database as well.
        showgroups (optional): will return results as a dictionary of dictionaries for all the groups (useful for separating tag groups).

    Raises: 
        ExifException, DBException
    """
    et = exiftool.ExifTool( filepath )
    res = et.probe(group)
    if res == None:
        raise ExifException( "Could not recognise file format")
    if uuid and (group=="ALL" or group=="Custom" ):
        res.update(db.loadtags(uuid))
    return res

def save_sessions():
    pass
    
def save_tag():
    pass
