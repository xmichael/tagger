import sys, os, subprocess, json
import configuration, logtool
from ExifException import ExifException


log = logtool.getLogger("exiftool")

class ExifTool:
    """ Wrapper arround Exiftool. Processes an *existing* media file and print information as json
    Supports:
    1) Reading tags from file
    2) Editing + Writing new tags
    3) Show supported filetypes/groups/tags
    
    Generally methods that return json, do so directly. Text information is not returned but remains in self.stdout
    
    NOTE: Each instance of the class has 1-1 relationship with a media file
    """
    
    # Full path of media file
    filename = None
    # exiftool location (for execution)
    exiftoolpath = None
    # stdout Output of last execution
    stdout = None
    # stderr Output of last execution
    stderr = None
    
    def __init__(self, fname):
        self.filename = fname
        self.exiftoolpath = os.path.join(configuration.getExifDir(),"exiftool")
        print self.exiftoolpath
    
    def exiftool(self, args):
        """ Execute exiftool with args 
        args: list of arguments as pass in command line
        """
        log.debug("Executing exiftool " + `args`)
        process = subprocess.Popen( [ self.exiftoolpath ] + args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        ( self.stdout , self.stderr ) = process.communicate()
        if process.returncode != 0:
            raise ExifException(self.stderr )       
    
    def probe(self, group="ALL", showgroups=False):
        """ return properties as a python object. Numeric Values only! 
        Args:
            group (optional): The tag group to fetch. Probes for everything by default
            showgroups (optional): will return results as a dictionary of dictionaries for all the groups. (useful for separating tag groups)
        """
        options = ["-n", "-j"]
        if group == "XMP" or group == "EXIF" or group == "IPTC":
            options.append("-%s:All" % group)
        if group == "EXIF":
            options.append("-Composite:All") #exiftool "hides" Exif tags under composite!
        if showgroups:
            options.append("-g")
        options.append( self.filename )
        self.exiftool(options)
        return json.loads(self.stdout)[0]
    
    def probegroups(self):
        """ return all the metadata groups defined in the file as a list"""
        md =  probe()
        return [ k for k in md ]
    
    def listw(self, group=None):
        """ List all writable TAGS. Optionally specify "group" e.g. "EXIF:ALL" """
        if group == None:
            self.exiftool(["-listw"])
        else:
            self.exiftool(["-listw",group])
    
    def save(self, data):
        """ data: dictionary of values to save """
        args = []
        for k in data:
            args.append("-%s=%s" % ( k, str(data[k]) ))
        args.append(self.filename)
        self.exiftool(args)

    def createXMP(self, outfile):
        """ export metadata as an XMP sidecar file """
        args = [ "-tagsfromfile", self.filename , outfile ] # using -o out.xmp complains if already exists
        self.exiftool(args)

    def add(self, data):
        """ data: dictionary of values to save that didn't exist in original.
        
        NOTE: The reason for having both save() and add() methods is that exiftool uses a different syntax
        for adding new tags and changing existing tags
        """
        args = []
        for k in data:
            args.append("-%s+=%s" % ( k, data[k]) )
        args.append(self.filename)
        self.exiftool(args)

################### MAIN #######################
if __name__ == "__main__" :
    exif = ExifTool(sys.argv[1])
    try:
        exif.listw("-EXIF:ALL")
        print "Stdout is: \n\n" + exif.stdout
        #instance method
        print exif.probe()
        newdata = { "Software" : 'Bas fotware' }
        exif.save(newdata)
        print exif.probe()
        exif.createXMP("out.xmp" );
    except ExifException as e:
        print e
    