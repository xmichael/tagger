#!/usr/bin/python
#-*- mode: python; -*-
################# INIT ###################
import os, sys, json,urllib
## Change working directory so relative paths (and template lookup) work
pwd = os.path.dirname(__file__)
#os.chdir(pwd)
## Also add library to the python path
sys.path.append(os.path.join(pwd,'../lib'))

import bottle
from bottle import route, request, static_file, redirect

# gtr imports
import logtool, mediafactory, configuration, db, helper
from ExifException import ExifException

#Dropbox imports
dbpath = configuration.getDropboxSDK()
sys.path.append(os.path.join(pwd,dbpath))
import gtr_dropbox

application = bottle.default_app()
log = logtool.getLogger("gtr")
################ ROUTES ####################

@route('/ws/editfile/:uuid')
def editfile( uuid ):
    """
    Edit the properties of an already-uploaded media file.
    
    This is also usefull for getting rid of extra GET parameters forcibly added by dropbox
    """
    
    # optional drobox arguments ( currently ignored )
    uid = request.GET.get("uid",None)
    oauth_token = request.GET.get("oauth_token",None)    
    log.info("editfile" + " params: uuid:%s uid:%s oauth_token:%s " % (uuid,uid, oauth_token))
    return redirect('/index.html?uuid=%s' % uuid)

#######################################################
###  Rest Callbacks (can be tested with wget/curl)  ###
#######################################################

@route('/ws/getfile/:uuid')
def getfile( uuid ):
    """
    Download already-uploaded media file.
    """
    media = mediafactory.MediaFactory()
    media.loadFromFile(uuid)
    log.debug("getfile: Downloading %s" % os.path.join(media.filedir, media.filename))
    #download=true forces download even if browser can display it inline
    return static_file(media.filename, root=media.filedir, download=True)

@route('/ws/getfile_inline/:uuid')
def getfile_inline( uuid ):
    """
    Download already-uploaded media file (embedded). Only IE needs that.
    """
    media = mediafactory.MediaFactory()
    media.loadFromFile(uuid)
    log.debug("getfile_inline: Downloading %s" % os.path.join(media.filedir, media.filename))
    return static_file(media.filename, root=media.filedir)

## Return geograph image using id
@route('/ws/geograph_image/:id')
def geograph_image( id ):
    """
    Return geograph image by it's id. Used for displaing as background.
    """
    rootdir = db.getGeographDir(id)
    image = str(id).zfill(6) + ".jpg"
    log.debug("geograph_image: Downloading %s" % os.path.join(rootdir, image))
    #download=true forces download even if browser can display it inline. (still works inline with css for everything except IE)
    return static_file(image, root=rootdir, download=False)

@route('/ws/export/:uuid')
def export( uuid ):
    """
    Download XMP for uuid.
    """
    media = mediafactory.MediaFactory()
    media.loadFromFile(uuid)
    xmpfile = media.datasetname + ".xmp"
    media.createXMP()
    log.debug("Exporting %s" % os.path.join(media.filedir, xmpfile))
    #download=true forces download even if browser can display it inline
    return static_file(xmpfile, root=media.filedir, download=True)

@route('/ws/uploadFile', method='POST')
def uploadfile():
    """
    POST a media file. Return is json { uuid:<the uuid>, error:0, msg:<error message>, url: <dropbox_sharing_url> } on success or { uuid:0, error: ERROR_CODE } for failure
    
    error codes are:
        0: success (uuid is valid)
        1: unsupported media file
        2: internal error
    """
    response = { "uuid":0, "error": 2, "msg":"" }
    #client_ip
    ip = request.environ.get('REMOTE_ADDR')
    #data pointer
    data = request.files.get('fileInput')
    license_sel = request.forms.get("license_sel", None)
    license_other = request.forms.get("license_other", None)
    l = license_other if license_other else license_sel
    if not l:
        l = "None"
    log.debug("Selected License: " + l)
    if data != None:
        try:
            media = mediafactory.MediaFactory()
            media.loadFromWeb( ip, data.filename, data.file )
            #log.debug( logtool.pp(media.mediamd) )
            if media.mediamd != []:
                media.saveconf()
                media.setlicense(l)
                response = { "uuid": media.uuid, "error": 0, "msg":"Success!" }
                return response
            else:
                response["error"] = 1 
                response["msg"] = "Could not find any supported format inside %s." %  data.filename
                return response           
        except IOError:
            response["error"] = 1 
            response["msg"] = "File %s is not a valid MEDIA file. Please try again." %  data.filename
            return response
        except ExifException as e:
            response["error"] = 1
            #response["msg"] = "Could not find any usable media file insize the %s." %  data.filename
            response["msg"] = e.shortmsg
            return response
    else:
        response = { "uuid":0, "error": 2, "msg":"Data were never received. File was not uploaded." }
    return response


# Similar to edit_geograph (s. API). but used for wget interface.
@route('/ws/loadURL')
def loadURL():
    response = {}
    url = request.GET.get("url", None)
    l = request.GET.get("license", None)
    #client_ip
    ip = request.environ.get('REMOTE_ADDR')
    if ( url==None or l==None ):
        msg = 'Both URL and license parameters are required'
        log.error("/loadURL: " + msg)
        return { "error": 1, "msg" : msg }
    try:
        log.info("loadURL params: url:%s ip:%s" %  (url,ip) )
        media = mediafactory.MediaFactory()
        media.loadFromURL( ip, url)
    except ExifException:
        response["error"] = 1 
        response["msg"] = "Could not find any usable media file under %s." %  url
        return response
    except Exception as e:
        return {"error":1 , "msg": str(e)}
    log.debug( logtool.pp(media.mediamd) )
    media.saveconf()
    media.setlicense(l)
    response = { "uuid": media.uuid, "error": 0, "msg":"Success!" }
    return response    
    
# Similar to edit_geograph (s. API). but used for wget interface.
@route('/ws/edit/:id')
def edit(id):
    return editGeograph(id)

# shortcut function to anonymise/remove GPS coords
@route('/ws/anonymise/:uuid')
def anonymise(uuid):
    log.debug('Got API ANONYMISE request for: ' + uuid)
    new_md =  {"GPSLatitude": "","GPSLongitude": "","GPSPosition": "","GPSLatitudeRef":"","GPSLongitudeRef":""}
    media = mediafactory.MediaFactory()
    media.loadFromFile(uuid)
    try:
        media.update( new_md )
    except ExifException as e:
        msg = e.shortmsg
        log.debug("ExifException: " + msg )
        return { "uuid":uuid, "error":1, "msg": msg }
    return { "uuid":uuid, "error":0, "msg": "Metadata saved!" }

# shortcut function for geotagging image
@route('/ws/geotag/:uuid')
def geotag(uuid):
    """ Geocode using lat/lon or placename. Either lat/lon or placename must
    be provided"""
    #get placename
    placename = request.GET.get("placename", None)
    #get lat,lon
    lon = float(request.GET.get("lon", -1000))
    lat = float(request.GET.get("lat", -1000))
    if ( placename ):
        if ( len(placename) < 4 ):
            return { "uuid": uuid, "error": 1, "msg" : "Placename has to be at least 3 characters long" }
        try:
            #sets lat/lon using unlock. Overwrites existing lat/lon values.
            ul = 'http://unlock.edina.ac.uk/ws/search?format=json&count=no&maxRows=1&name=' + placename
            (lon,lat) = json.loads(urllib.urlopen(ul).read())["features"][0]["properties"]["centroid"].split(',')
            (lon,lat) = [ float(x) for x in (lon,lat) ]
        except IOError as e:
            msg = 'Cannot connect to the Unlock service'
            return { "uuid": uuid, "error": 1, "msg" : msg }
    if ( lat==-1000 or lon==-1000 ):
        msg = 'Both lat and lon arguments are required'
        log.error("/ws/geotag: " + msg)
        return { "uuid": uuid, "error": 1, "msg" : msg }
    # geocode
    log.debug('/ws/geotag/: ' + uuid + " with lon: %s lat: %s" % (lon , lat))
    try:
        media = mediafactory.MediaFactory()
        media.loadFromFile(uuid)
        media.geotag(lon, lat, placename)
    except ExifException as e:
        msg = e.shortmsg
        log.debug("ExifException: " + msg )
        return { "uuid":uuid, "error":1, "msg": msg }
    except IOError as e:
        msg = 'Cannot connect to the Geonames service'
        return { "uuid": uuid, "error": 1, "msg" : msg }
    return { "uuid":uuid, "error":0, "msg": "Metadata saved!" }

######################
### AJAX Callbacks ###
######################

### Load All Metadata. If a "group=XXX" parameter exists then fetches metadata only for XXX group (e.g. EXIF) ###
@route('/ws/loadMetadata/:uuid', method='GET')
def loadMetadata( uuid ):
    # Get Optional GET parameter "group" otherwise assume ALL
    group = request.GET.get("group","ALL")
    log.debug('Got AJAX LOAD metadata request for: %s for %s tags' % (uuid,group))
    media = mediafactory.MediaFactory()
    media.loadFromFile(uuid, group)
    # build response tree:
    #log.debug("metadata: ")
    #log.debug( logtool.pp(media.mediamd)) #-- noisy!
    if group == "Custom":
        return media.customtags
    return media.mediamd

### Save Metadata ###
@route('/ws/saveMetadata/:uuid', method='POST')
def saveMetadata( uuid ):
    log.debug('saveMetadata request for: ' + uuid)
    media = mediafactory.MediaFactory()
    media.loadFromFile(uuid)
    group = request.forms.get('group')
    new_md_json = request.forms.get('metadata')
    new_md = json.loads(new_md_json)
    try:
        media.update( new_md, group )
    except ExifException as e:
        msg = e.shortmsg
        log.debug("ExifException: " + msg )
        return { "uuid":uuid, "error":1, "msg": msg }
    log.debug("got new " + `group` + " metadata: ")
    log.debug( logtool.pp(new_md))
    return { "uuid":uuid, "error":0, "msg": "Metadata saved!" }

### getUUIDs OBSOLETES searchKeywords ###
@route('/ws/getUUIDs', method='GET')
def getUUIDs():
    """ Get uuids by bbox or keyword """
    key = request.GET.get('key', None)
    bbox = request.GET.get('bbox', None) #xmin,ymin,xmax,ymax
    if (key == None and bbox==None):
        msg = "At least one of `bbox' or `key' parameters must be specified"
        return { "error": 0, "msg" : msg }
    try:
        res = db.getUUIDs(bbox, key)
        res2 = db.getGeographIDs(bbox, key)
        return { "error": 0, "tagger_uuids" : res, "geograph_uuids": res2 }
    except Exception as e:
        return { "error": 2, "msg" : str(e) }        
    
### Add keyword ###
@route('/ws/addKeyword/:uuid', method='GET')
def addKeyword( uuid ):
    key = request.GET.get('key', None)
    if ( key==None ):
        msg = 'addKeyword: "key" argument required but missing'
        log.error("/ws/addKeyword: " + msg)
        return { "uuid": uuid, "error": 1, "msg" : msg }
    key = helper.strfilter(key, "'/\. ")
    log.debug('addKeyword request for: %s with key: %s' % (uuid,`key`) )
    try:
        media = mediafactory.MediaFactory()
        media.loadFromFile(uuid)
        if media.customtags.has_key("keywords"):
            keys = media.customtags["keywords"]
            log.debug("Previous keywords " + `keys`)
            keys = keys + "," + key
            # `set' removes duplicate keywords
            keys = ','.join(set(keys.split(',')))
        else:
            keys = key
        media.update( { 'keywords' : keys }, group="Custom" )
        db.insert_key(key)
        db.connect_key(media.uuid, key)
    except ExifException as e:
        msg = str(e)
        log.debug("Exception: " + msg )
        return { "uuid":uuid, "error":1, "msg": msg }
    except Exception as e:
        return {"error":1 , "msg": str(e)}
    return { "uuid":uuid, "error":0, "msg": "Keyword saved!" }

### Set License ###
@route('/ws/setLicense/:uuid', method='GET')
def setLicense( uuid ):
    """ Set the license of the media data as follows:
        1) If the license is CC then it is added as an XMP-cc tag
        2) Otherwise it is added as a value of custom tag "license"
        
        This is done transparently by the mediafactory object
    """
    l = request.GET.get('license', None)
    if ( l==None ):
        msg = 'setLicense: "license" argument required but missing'
        log.error("/ws/setLicense: " + msg)
        return { "uuid": uuid, "error": 1, "msg" : msg }
    log.debug('setLicense/%s:%s' % (uuid,l) )
    media = mediafactory.MediaFactory()
    try:
        media.loadFromFile(uuid)
        media.setlicense(l)
    except ExifException as e:
        msg = str(e)
        log.debug("Exception: " + msg )
        return { "uuid":uuid, "error":1, "msg": msg }
    return { "uuid":uuid, "error":0, "msg": "License saved!" }

### Set License ###
@route('/ws/getLicense/:uuid', method='GET')
def getLicense( uuid ):
    """ Returns the license of the media data:
        1) If it exists at the XMP-cc tag this takes precedence
        2) Otherwise it returns the value of custom tag "license" or None
        
        This is done transparently by the mediafactory object
    """
    log.debug('getLicense/%s' % uuid)
    media = mediafactory.MediaFactory()
    try:
        media.loadFromFile(uuid)
        lic = media.getlicense()
    except ExifException as e:
        msg = str(e)
        log.debug("Exception: " + msg )
        return { "uuid":uuid, "error":1, "msg": msg }
    return { "uuid":uuid, "license": lic, "error":0, "msg": "Success!" }

### Add keyword ###
@route('/ws/getKeywords/:uuid', method='GET')
def getKeywords( uuid ):
    log.debug('getKeywords request for: %s' % uuid ) 
    media = mediafactory.MediaFactory()
    media.loadFromFile(uuid)
    if media.customtags.has_key("keywords"):
        keys = media.customtags["keywords"]
    else:
        keys = ""
    return { "uuid":uuid, "error":0, "keywords" : keys}

## Return nearest geograph files
@route('/ws/nearest', method='GET')
def getNearest():
    lon = float(request.GET.get("lon"))
    lat = float(request.GET.get("lat"))
    log.debug('Got AJAX NEAREST request for: %f , %f' % (lon,lat))
    res = db.nearest_dist( lon, lat, 2500.0 )
    # build response tree:
    log.debug( logtool.pp(res))
    return json.dumps(res)

## Edit geograph files by converting it to UUID and saving its tags as custom
@route('/ws/edit_geograph/:id')
def editGeograph(id):
    """ imports geograph image as if it were uploaded. Creates a new copy of the image and the original image is left untouched """
    response = {}
    #client_ip
    ip = request.environ.get('REMOTE_ADDR')
    #geograph image
    rootdir = db.getGeographDir(id)
    imagename = str(id).zfill(6)
    imagefile = os.path.join(rootdir, imagename + ".jpg" )
    log.debug("Downloading %s" % imagefile )
    try:
        media = mediafactory.MediaFactory()
        media.loadFromWeb( ip, imagename + ".jpg", open(imagefile) )
        # update coords in exif from geograph database
        (lon,lat,tags) = db.geograph_byid(id)
        log.debug("geograph metadata for " + id )
        log.debug( logtool.pp( (lon,lat,tags) ) )
        #create sessions.js
        media.saveconf()
        updatedata = {
            "GPSLatitude" : `lat`,
            "GPSLongitude" : `lon`,
            "GPSLatitudeRef" : "S" if lat<0 else "N",
            "GPSLongitudeRef" : "W" if lon<0 else "E"
        }
        media.update(updatedata)
        if tags != None:
            media.update( { 'Tags' : tags }, group="Custom" )
    except ExifException as e:
        msg = e.shortmsg
        response["error"] = 1 
        log.debug("ExifException: " + msg )
        response = { "uuid":media.uuid, "error":1, "msg": msg }
        return response
    except IOError:
        response["error"] = 1 
        response["msg"] = "Could not find geograph file %s." %  imagename
        return response    
    log.debug( logtool.pp(media.mediamd))
    if media.mediamd != []:
         media.saveconf()
         response = { "uuid": media.uuid, "error": 0, "msg":"Success!" }
    else:
         response["error"] = 1 
         response["msg"] = "Could not find any supported format inside %s." %  media.filename
    return response    

# Login to Dropbox.
@route('/ws/dropbox_login', method='GET')
def dropbox_login():
    # Get optional req_key and callback URL parameters otherwise assume None
    req_key = request.GET.get("req_key",None)
    callback = request.GET.get("callback", None)
    log.debug("dropbox_login:" + " params callback: " + `callback` + " req_key :" + `req_key`);
    dbox = gtr_dropbox.GTRDropbox()
    response = dbox.login(req_key, callback)
    log.debug("dropbox_login response: ")
    log.debug( logtool.pp(response))
    return response

@route('/ws/dropbox_callback/:req_key')
def dropbox_callback(req_key):
    """ Callback to indicate that verification was done by user. User MUST provide req_key for session tracking.
    
    Returns:
        req_key: verified request token (same as the argument basically). this should be stored by the client for future passwordless logins
    """
    log.debug("Received callback for req_key : " + `req_key`);
    dbox = gtr_dropbox.GTRDropbox()
    try:
        return { "error": 0 , "msg": dbox.callback(req_key)}
    except Exception as e:
        return {"error":1 , "msg": str(e)}

@route('/ws/dropbox_upload/:uuid/:req_key', method='GET')
def dropbox_upload(uuid,req_key):
    media = mediafactory.MediaFactory()
    media.loadFromFile(uuid)
    dbox = gtr_dropbox.GTRDropbox()
    login = dbox.login(req_key)
    try:
        log.debug("Received upload for req_key : " + `req_key` + " uuid: " + `uuid`);
        if ( login["state"] == gtr_dropbox.STATE_CODES["connected"] ):
            uploaded_metadata = dbox.upload("/" + media.filename , open(media.filefullpath,"rb"))
            log.debug(uploaded_metadata) # this is not used
            shared_file = dbox.media("/" + media.filename)
            return { "error": 0 , "msg": "File uploaded", "url": shared_file["url"], "expires": shared_file["expires"] }
        else:
            return { "error": 1 , "msg": "Invalid Session. Relogin"}
    except Exception as e:
        log.exception("dropbox_upload exception: " + str(e))
        return {"error":1 , "msg": str(e)}

### STATIC FILES (html/css/js etc.)###
root = configuration.getStaticHTML()
@route('/<filename:re:(?!ws/).*>')
def serve_static(filename):
    return static_file(filename, root=root, download=False)
@route('/')
def default_static():
    return static_file('index.html', root=root, download=False)
# Do NOT use bottle.run() with APACHE / mod_wsgi   
bottle.run(host=configuration.getGTRHost(), port=configuration.getGTRPort(), debug=True)
