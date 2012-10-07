## This is a Singleton class to return values stored under resources/config.ini. 
## Read that file for documentation of values.
## note to java coders: Singletons in python are just modules with plain functions.

"""
For an explanation of each config. item see comments in resource/config.ini
"""

import ConfigParser

config = ConfigParser.SafeConfigParser()

config.read(['../resources/config.ini'])

def getSampleUUID():
    return config.get('TEST','sampleuuid')    

def getStaticHTML():
    return config.get('DEFAULT','static_html')

def getGTRHost():
    return config.get('DEFAULT','gtrhost')

def getGTRPort():
    return config.get('DEFAULT','gtrport')

def getDropboxSDK():
    return config.get('DEFAULT','dropbox_path')

def getCCMap():
    ccmap = { 
             "Default" : "",
             "Zero":"http://creativecommons.org/publicdomain/zero/1.0/",
             "CC-BY":"http://creativecommons.org/licenses/by/3.0",
             "CC-SA":"http://creativecommons.org/licenses/by-sa/3.0",
             "BY-NC-CA":"http://creativecommons.org/licenses/by-nc/3.0",
             "BY-NC-DC":"http://creativecommons.org/licenses/by-nc-nd/3.0"
    }
    return ccmap

def getExifDir():
    return config.get('DEFAULT','exif_dir')

def getDataDir():
    return config.get('DEFAULT','data_dir')

def getSessionsDB():
    return config.get('DEFAULT','sessionsdb')

def getTest1():
    return config.get('TEST','testfile1') 

def getTest2():
    return config.get('TEST','testfile2') 

def getMapserverURL():
    return config.get('DEFAULT','wms_url')

def getdb():
    return config.get('DEFAULT','sessionsdb')
    
def get_libspatialite():
    return config.get('DEFAULT','libspatialite')    

def get_geograph_base_dir():
    return config.get('DEFAULT','geograph_dir')    

def get_app_key():
    return config.get('DEFAULT','app_key')    
    
def get_app_secret():
    return config.get('DEFAULT','app_secret')    

def get_log_file():
    return config.get('DEFAULT','log_file')    
    
if __name__ == "__main__":
    print "Data Dir: " + getDataDir()
    print "Test file 1: " + getTest1()
    print "Test file 2: " + getTest2()

