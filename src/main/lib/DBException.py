class DBException(Exception):
    """ This class covers all exceptions thrown during spatialite accessess """
    
    # Everything in stderr after executing spatialite
    msg = None
    # A user friendlier shorter version of msg
    shortmsg = None
    
    def __init__(self, msg):
        self.msg = msg
        self.shortmsg = msg
    def __str__(self):
        return repr(self.msg)
