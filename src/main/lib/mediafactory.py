import os, time, uuid, json, urllib, shutil
import configuration, helper, logtool, exiftool, db
import xml.etree.ElementTree as ETree
#from ipdb import set_trace

log = logtool.getLogger("MediaFactory", "gtr")

class MediaFactory:
    """
        Uses a Media interface (e.g. ExifTool/Sqlite (abstracted from helper.py)) to associate Media with users and sessions
    """
    
    def __init__(self):
        """ Use one of the loadXXX methods to initialise the class as python does not have multiple constructors """
        
        
        #########################
        ### WEB related stuff ###
        #########################
        # IP
        self.ip = None
        # File Object containing uploaded data
        self.filedata = None 
        # uuid corresponding to request (for sharing). This is permanent and unique
        self.uuid = None
        # filename (main file e.g. foo.shp in the filepath to open)
        self.filename = None
        # Full path pointing to the saved data directory
        self.filedir = None
        # filedir/filename
        self.filefullpath = None
        # modification time
        self.mtime = None
        # custom tags set by user  (not necessarily supported by exiftool)
        self.customtags = None
        # creation time
        self.atime = None
        #calculated dataset name without funny chars:
        self.datasetname = None

        ################
        ### sessions ###
        ################
        # General attirbutes for Mediafile
        self.mediamd = {}

    
    def loadFromWeb(self, ip, uploadFilename, uploadData):
        """
        Create a media object sessions and also loads the metadata from the file based on a uploaded file.
        
        ip: remote address
        uploadFilename: upload user name of file (string)
        uploadFile: uploaded user file (file pointer made available by WSGI server)
        """
        log.debug("Filename was: " + uploadFilename )
        self.ip = ip
        self.uuid =  uuid.uuid4().hex
        self.filename = uploadFilename
        self.filedata = uploadData
        self.filedir = os.path.join (configuration.getDataDir(), self.uuid)
        self.filefullpath = os.path.join (self.filedir, self.filename)
        self.ctime = time.strftime('%d%m%y-%H:%M:%S')
        self.customtags = {}
        self.mtime = self.ctime
        self._savefile()
        self.mediamd = helper.probedata(self.filefullpath)
        self.datasetname = helper.getBaseName(self.filename)
        db.insert_uuid(self.uuid)
        log.debug("filename: " + `self.filename`)
        log.debug("DatasetName (filename w/o extention): " + `self.datasetname`)

    def loadFromURL(self, ip, url):
        """
        Create a media object sessions and also loads the metadata from the file based on a uploaded file.
        
        ip: remote address
        url: url of the file (string)
        """
        self.ip = ip
        self.uuid =  uuid.uuid4().hex
        # assuming filename is eveything after the rightmost `/'        
        self.filename = helper.strfilter( url[url.rfind('/'):] ,"\\/" )
        self.filedata = urllib.urlopen(url)
        self.filedir = os.path.join (configuration.getDataDir(), self.uuid)
        self.filefullpath = os.path.join (self.filedir, self.filename)
        self.ctime = time.strftime('%d%m%y-%H:%M:%S')
        self.customtags = {}
        self.mtime = self.ctime
        self._savefile()
        self.mediamd = helper.probedata(self.filefullpath)
        self.datasetname = helper.getBaseName(self.filename)
        db.insert_uuid(self.uuid)
        log.debug("filename: " + `self.filename`)
        log.debug("DatasetName (filename w/o extention): " + `self.datasetname`)
    
    
    def loadFromFile(self, uuid, group="ALL"):
        """
        Create a media object based on a saved session.
        
        uuid: the uuid corresponding to the saved media object instance
        @exceptions: file does not exist, parse error
        """
        self.uuid = uuid
        self.filedir = os.path.join (configuration.getDataDir(), self.uuid)
        
        log.debug("loading saved uuid: " + self.uuid)
        sessions_file = open(os.path.join ( self.filedir, 'sessions.json' ), 'r')
        sessions = json.load( sessions_file )
        sessions_file.close()
        if sessions == None:
            raise ValueError("Cannot parse sessions.json for uuid: " + uuid)
        self.ip = sessions["ip"]
        self.datasetname = sessions["datasetname"]
        self.filename = sessions["filename"]
        self.filefullpath = os.path.join (self.filedir, self.filename)
        self.mtime = sessions["mtime"]
        self.ctime = sessions["ctime"]
        self.customtags = sessions["customtags"]
        self.mediamd = helper.probedata(self.filefullpath, group)
    
    def saveconf( self ):
        """ permanently store media data. """
        # TODO: changing this to use the `db' module is *enough* for database access
        if ( self.mediamd == None ):
            raise IOError("Trying to save null data!")
        sessions_file = open(os.path.join ( self.filedir, 'sessions.json' ), 'w')
        sessions={}
        sessions["ip"] = self.ip
        sessions["datasetname"] = self.datasetname
        sessions["filename"] = self.filename
        sessions["mtime"] = self.mtime
        sessions["ctime"] = self.ctime
        sessions["customtags"] = self.customtags
        json.dump(sessions, sessions_file)
        sessions_file.close()            
    
    def is_writable( self ):
        """ Check if the file is writable by comparing its file type against a
        list of supported file (generated with "exiftool -listwf") 
        
        Returns:
            True if the file can be written by exiftool, otherwise False.
        """
        listwf = ["AI", "AIT", "ARW", "CIFF", "CR2", "CRW", "CS1", "DCP", \
                  "DNG", "EPS", "EPS2", "EPS3", "EPSF", "ERF", "EXIF", "GIF", \
                  "HDP", "ICC", "ICM", "IIQ", "IND", "INDD", "INDT", "JNG", \
                  "JP2", "JPEG", "JPG", "JPM", "JPX", "MEF", "MIE", "MNG", \
                  "MOS","MPO", "MRW", "NEF", "NRW", "ORF", "PBM", "PDF", "PEF",\
                  "PGM", "PNG", "PPM", "PS", "PS2", "PS3", "PSB", "PSD", "RAF",\
                  "RAW", "RW2", "RWL", "SR2", "SRW,THM", "TIF", "TIFF", "VRD",\
                  "WDP", "X3F", "XMP" ]
        
        if (self.mediamd.has_key("FileType")):
            if (self.mediamd["FileType"] in listwf ):
                return True
            else:
                return False
        else:
            log.error('Mediafile does NOT have "FileType" attribute!')
            return False
    
    def update( self, new_md, group="ALL" ):
        """
          Updated an existing media object + media metadata on the file 
          using externally provided json metadata,
          
          Before updating you must load the old media file to update e.g.:
          
          old = mediafactory.loadFromFile( '4214131214f2' )
          old.update( newmetadata )
          
          Before updating a check is beformed for writability of media file. If 
          file is not writable then only custom tags are used (i.e. tags stored
          in a separate file and exported as a sidecar XMP)
        """
        self.mtime = time.strftime('%d%m%y-%H:%M:%S')
        
        if ( not self.is_writable()):
            log.debug('WARNING: Requested write to group ' + group + \
            ' but filetype is not writable. Switching to group "Custom"')
            group = "Custom"
        
        if group=="Custom":
            #custom tags are saved separately in sessions.js
            self.customtags.update(new_md)
            #delete empty tags from the whole after applying the diff (this is also done by exiftool backend)
            for k in self.customtags.keys():
                if self.customtags[k] == "":
                    del (self.customtags[k])
                    log.debug("deleted: " + k)
            # save keywords in database
            if self.customtags.has_key("keywords"):
                log.debug("saving keywords: " + self.customtags["keywords"] )
                for key in self.customtags["keywords"].split(','):
                    db.insert_key(key)
                    db.connect_key(self.uuid, key)
            self.saveconf() #update mtime and customtags
        else:
            #save mediamd
            self._savedata(new_md)
            #if customtags has coordinates then update db
            if ( new_md.has_key("GPSLatitude") and new_md.has_key('GPSLongitude')  ):
                # anonymise function sets these to '' so ignore!
                if (new_md['GPSLongitude']==""  or new_md["GPSLatitude"]==""):
                    return
                # invariant: uuid MUST EXIST in sessions table
                log.debug("geocoding in DB! Newmd is: " + logtool.pp(new_md))
                res = db.geotag_uuid(self.uuid, new_md['GPSLongitude'],new_md["GPSLatitude"])
                log.debug(`res`)
            self.saveconf() #update mtime only
    
    def _savefile( self ):
        """
        First time setup of new media - save the user supplied file under a uuid-based data directory
        """
        # create uuid-based directory
        log.debug("Creating dir: " + self.filedir)
        os.mkdir(self.filedir, 0770)
        # save media file under that dir
        f = open ( self.filefullpath, "w" )
        f.write(self.filedata.read())
        f.close()
    
    def _savedata(self, data):
        """
        Uses ExifTool to update metadata of a media file given a dictionary with the new values.
        
        Args:
            data: values to update as a dictionary e.g. { "newtag" : "newvalue" , ... }
        Throws: 
            ExifException
        """
        et = exiftool.ExifTool( self.filefullpath )
        res = et.save( data )
        return True
    
    def geotag(self, lon, lat, placename=None):
        """
        Uses ExifTool to geotag media file. Solely for API use as it does not 
        do extra reverse-geocoding which depends on geonames -- use the web interface for that
        
        Args:
            lon: Longitude
            lat: latitude
        Throws: 
            ExifException: when saving metadata
            IOError: on reverse geocoding
        """ 
        updatedata = {
            "GPSLatitude" : lat,
            "GPSLongitude" : lon,
            "GPSPosition" : `lat` + " " + `lon`,
            "GPSLatitudeRef" : "S" if lat<0 else "N",
            "GPSLongitudeRef" : "W" if lon<0 else "E"
        }

        # reverse geocoding using geonames (throws IOError when http error)
        if (not placename):
            url = 'http://api.geonames.org/findNearbyJSON?lat='+ `lat` + '&lng=' + `lon` + '&username=gtrtagger'
            try:
                gn = json.loads(urllib.urlopen(url).read())["geonames"][0]
                updatedata["GPSAreaInformation"] = gn["name"] + ', ' + gn["adminName1"] + ', ' + gn["countryCode"]
            except KeyError:
                log.error("geonames returned no results. URL was: " + url)
        else:
            updatedata["GPSAreaInformation"] = placename
        return self.update(updatedata)

    def setlicense(self, lic):
        """ Set the license of the media data as follows:
        1) If the license is CC then it is added as an XMP-cc tag
        2) Otherwise it is added as a value of custom tag "license"
        
        Args:
            lic: License string
        Throws:
            ExifException
        """
        ccmap = configuration.getCCMap()
        if ( ccmap.has_key(lic) ):
            # we have a CC license
            if (lic == "Default"):
            # if license is default then check if another exists or use CC-Zero
                if ( self.mediamd.has_key("License")):
                    log.info("mediafactory.setlicense: leaving existing license: " + 
                    self.mediamd["License"])
                    return True
                lic = "Zero"
                log.info("mediafactory.setlicense: defaulting to CC-Zero")
            # Applies to all CC licenses
            self.update({"License":ccmap[lic]}, group="XMP-cc")
            log.debug("setLicense: Saved CC licence " + lic)
        else:
            # Applies to all arbitrary licenses
            self.update({"License":lic}, group="Custom")
            log.debug("setLicense: Saved arbitrary licence " + lic)
        return True

    def getlicense(self):
        """ Returns the license of the media data:
        1) If it exists at the XMP-cc tag this takes precedence
        2) Otherwise it returns the value of custom tag "license" or None
        
        """
        if ( self.mediamd.has_key("License")):
            return self.mediamd["License"]
        if ( self.customtags.has_key("License") ):
            return self.customtags["License"]
        return "No license found!"

    def createXMP(self):
        """
        Create an XMP file at the directory where the media is.
        
        This will also export custom tags as   
        """
        xmpfile = os.path.join( self.filedir, self.datasetname + ".xmp" )
        tmpfile = os.path.join( self.filedir, self.datasetname + ".ori.xmp" )
        et = exiftool.ExifTool( self.filefullpath )
        res = et.createXMP(tmpfile)
        
        #FYI Seq for a single value or serial values or Bag for tags. 
        # inistially use Seq with all tags as CSVs
        if(self.customtags != {} ):
            xml = '<rdf:Description xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:gtr="http://edina.ac.uk/gtr/1.1/" rdf:about="GeoTagger Project custom properties">'
            for k in self.customtags:
                xml = xml + \
                """
                    <dc:%s>
                        <rdf:Seq>
                            <rdf:li>%s</rdf:li>
                        </rdf:Seq>
                    </dc:%s>
                """ % (k, self.customtags[k],k)
            xml = xml + "</rdf:Description>"
            etr = ETree.parse(tmpfile)
            inject = ETree.fromstring(xml)
            #root = tr.getroot()
            el = etr.find('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF')
            el.append (inject)
            #log.debug("DUMP")
            #log.debug(ETree.tostring(el))
            etr.write(xmpfile,encoding="utf-8")
        else:
            shutil.copy(tmpfile, xmpfile)
        return True    

if __name__ == "__main__":
    ip = '127.0.0.1'
    uploadData = open ( configuration.getTest1() )
    mf = MediaFactory()
    mf.loadFromWeb(ip, "MyMedia.jpg" , uploadData)
    mf.saveconf()
    print "First Media Instance session:\n"
    log.debug( logtool.pp(mf.datasetname) )
    #### now close and reopen ##
    uuid = mf.uuid
    del(mf)
    mf2 = MediaFactory()
    mf2.loadFromFile(uuid)
    print "================================"
    print "Second Media Instance session:"
    print mf2.datasetname
    print "================================"
    print "Second Media Metadata:"
    log.debug( logtool.pp(mf2.mediamd))
    print "old BaseISO value: " + `mf2.mediamd["BaseISO"]`
    updatedict = { 'BaseISO' : 666 }
    log.debug( logtool.pp('using update vector: ' + `updatedict`))
    #save inside media file
    mf2.update(updatedict)
    # save in sessions.js
    mf2.update(updatedict, group="Custom")
    
