import os
import configuration, logtool

from dropbox import client, rest, session

### Static Variables ###
# XXX Fill in your consumer key and secret below
# You can find these at http://www.dropbox.com/developers/apps
APP_KEY = configuration.get_app_key()
APP_SECRET = configuration.get_app_secret()
ACCESS_TYPE = 'app_folder'  # should be 'dropbox' or 'app_folder' as configured for your app

# COOKIES are an immutable hash table with request tokens as keys and request secret, access key, secret tuples as values. They are kept in memory till
# we decide to store credentials on a database (do we want this?).
# This is a static value and exists for the lifetime of the python interpreter.
COOKIES = {}

STATE_CODES = {
        "verify_token": 0,
        "connected" : 1
    }

log = logtool.getLogger("GTRDropbox", "gtr")
#########################

class GTRDropbox:
    """ Create and control Dropbox sessions using oAuth protocol. Sessions are cached internally memory in the static variable COOKIES.
    
    Use one of the login or load methods to initialise the class as python does not have multiple constructors
    
    Example usage from a site gtr.ac.uk
    
        newurl = self.test_new_dropbox_session()
        print "URL: " + 
        self.wait()
        self.cookie = self.gtrdb.callback()
        print "Cookie: " + self.cookie
    """
    
    def __init__(self):
        # This is send to clients to let them know which state this object is in.
        self.state = {
                "url": "",
                "req_key": "",
                "state" : STATE_CODES["verify_token"]
            }
    
    def login(self, cookie = None, callback = None):
        """ Create a URL which the browser can use to verify a token and redirect to webapp.
        
        Args:
            cookie : request key (not secret!), cached by session cookie (optional)
            callback : where to return
        
        Returns:
            None: if connection is already established (from cookie) or
            URL: a URL to authorize the token
        
        Raises:
            rest.ErrorResponse
        """
        self.sess = session.DropboxSession(APP_KEY, APP_SECRET, access_type=ACCESS_TYPE)
        self.api_client = client.DropboxClient(self.sess)

        #check if user has cookie
        if (cookie):
            accesspair = self.get_access_pair(cookie)
            # check if cookie has credentials associate with it
            if accesspair : self.sess.set_token(*accesspair)

        #if we don't have a sessions get a URL for authn
        if (not self.sess.is_linked()):
            self.request_token = self.sess.obtain_request_token()
            url = self.sess.build_authorize_url(self.request_token, callback)
            self.state = { "url" : url , "req_key" : self.request_token.key , "state" : STATE_CODES["verify_token"] }
            self.save_all_pairs( self.request_token.key, self.request_token.secret )
        else:
            self.state = { "state" : STATE_CODES["connected"] }
        return self.state
        
    def upload(self,name, fp):
        """ Upload the media file `uuid'
        Args:
            name (str): destination path of file in sandbox with directories created on-the-fly e.g. "/foo.jpg" for apps/geotagger/foo.jpg
            fp (File): the file object to upload.
        
        Returns: Dictionary of Metadata of uploaded file.
                 see also https://www.dropbox.com/developers/reference/api#metadata-details
        
        Raises:
            rest.ErrorResponse
        """
        log.debug("uploading file: " + name)
        log.debug("delete me! with cookies: " + `COOKIES` )
        metadata = self.api_client.put_file(name, fp )
        fp.close()
        return metadata
    
    def media(self,name):
        """ Upload the media file `uuid'
        Args:
            name (str): destination path of file in sandbox with directories created on-the-fly e.g. "/foo.jpg" for apps/geotagger/foo.jpg
        
        Returns: Dictionary with url and expiration data e.g. {'url': 'http://www.dropbox.com/s/m/a2mbDa2', 'expires': 'Thu, 16 Sep 2011 01:01:25 +0000'}
        
        Raises:
            rest.ErrorResponse
        """
        log.debug("Creating share for " + name)
        res = self.api_client.media(name)
        return res
    
    def callback(self, req_key):
        """ Call this when authentication has been established with browser. This will save the credentials for future use.        
        Supply request_token to lookup object credentials from previeous authentications the object from scratch
        
        Returns:
            the request key (aka cookie to set to browser)
        
        Raises:
            rest.ErrorResponse: e,g, 'Token is disabled or invalid'
        """
        req_tuple = self.get_request_pair(req_key)
        self.sess = session.DropboxSession(APP_KEY, APP_SECRET, access_type=ACCESS_TYPE)
        self.api_client = client.DropboxClient(self.sess)
        self.sess.set_request_token(req_tuple[0], req_tuple[1])
        acc_pair = self.sess.obtain_access_token() #only works if request token is verified
        self.save_all_pairs(req_tuple[0], req_tuple[1], acc_pair.key, acc_pair.secret )
        log.debug( "delete me! saving: " + `(req_tuple[0], req_tuple[1], acc_pair.key, acc_pair.secret )`)
        return req_key
    
    def get_access_pair(self, req_key):
        """ Get credentials of user using a session cookie.
        
        Args:
            req_key: the request key used for looking up other keys
            
        Returns:
            credential tuple or None if it doesn't exist.
        """
        if ( COOKIES.has_key(req_key) and COOKIES[req_key][1] ):
            return  ( COOKIES[req_key][1] , COOKIES[req_key][2] )
        else:
            return None     
    
    def get_request_pair(self, req_key):
        if ( COOKIES.has_key(req_key) and COOKIES[req_key][0] ):
            return ( req_key , COOKIES[req_key][0] )
        else:
            return None             
    
    def save_all_pairs(self, req_key, req_secret, acc_key=None, acc_secret=None ):
        """ Save a all pairs for cookie. acc_key/acc_secret can be none """
        COOKIES[req_key] =  ( req_secret, acc_key, acc_secret )

