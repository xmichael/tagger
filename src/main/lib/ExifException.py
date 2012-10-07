import logtool
log = logtool.getLogger("Exiftool", "gtr")

class ExifException(Exception):
    """ This class covers all exceptions thrown during execution of the external perl program exiftool. Should be Thrown *only* by the exiftool class """
    
    # Everything in stderr after executing exiftool
    msg = None
    # A user friendlier shorter version of msg
    shortmsg = None
    
    def __init__(self, msg):
        self.msg = msg
        # take first line as a short message, which should be just enough.
        line = msg.split('\n')[0]
        # extra bodge since exiftool like to put home directories in message
        idx = line.find( " - /home")
        if (idx != -1):
            self.shortmsg = line[:idx]
        else:
            self.shortmsg = line
        log.error("Exiftool exception shown to user: " + self.shortmsg)
    def __str__(self):
        return repr(self.msg)
