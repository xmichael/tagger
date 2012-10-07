/** Global metadata hash/object to enable fast in-memory processing instead of relying on stupid Ext CRUD Object model  */
// original metadata
var metadata_ori = {};
// metadata edited by mediaGrid
var metadata_edit = {};

// UUID of media object
var uuid;

/** hidden properties for metadata.layers */
var exclude = [ "Directory", "SourceFile" ];

/** Datatable of media data */
var dt;

/** create a new object that does *not* include the fields in an array 
 * src: source object
 * exclude: array of fields to exclude
 */
function subObject ( src, exclude ){
    dst = {};
    for ( k in src ){
        if ( exclude.indexOf(k) == -1 ){ 
              dst[k] = src[k]; 
        }
    }
    return dst;
}


/** Check if an symbol name exists */
function exists ( symbol ) {
    if (symbol==undefined)
        return false;
    return true;
}

/** update object by copying only overlapping fields in records leaving the other ones untouched */
function updateObject(src, dst){
    for ( k in src ){
        if ( k in dst){dst[k] = src[k]};
    }
}

/** Object diff. Return a new object with different values between two objects */
function diffObject(src, dst){
    ret = {};
    for (k in dst){
        // copy keys that exist only in dst or have different values
        if ( k in src  && src[k]==dst[k]){
                continue;
        }
        ret[k] = dst[k];
    }
    return ret;
}


/** save global metadata */
function download(uuid) {
    window.location = 'http://' + window.location.host + '/ws/getfile/' + uuid;
}

/**
 * Create a new key in metadata if it doesn't already exist. If it does then it is just updated. 
 * Note: Exiftool require *new* metadata to be appended with the `+'  sign
 * 
 * Args:
 * 
 *      md: Metadata to write
 *      key: Key name
 *      value: Key value
 */

function createOrUpdate ( md, key, value ){
    if ( exists( md.key ) ){
        md.key = value;
    }
    else {
        md[key] = value;
    }
}

/** CreateOrUpdate geotag coordinates to metadata */
function geotag(lon, lat){
    createOrUpdate( metadata_edit, "GPSLatitude", lat );
    createOrUpdate( metadata_edit, "GPSLongitude", lon );
    createOrUpdate( metadata_edit, "GPSPosition", lat + " " + lon );
    createOrUpdate( metadata_edit, "GPSLatitudeRef", lat<0 ? "S" : "N" );
    createOrUpdate( metadata_edit, "GPSLongitudeRef", lon<0 ? "W" : "E" );
    updateMediaData(dt, metadata_edit);
    displayCoordinates(metadata_edit);
    save_md(uuid);
}

/********************************/
/* Update media data and refresh (default)
 Args:
    Datatable dt :  datatable to update
    Object obj : json object of data
 */
function updateMediaData( dt, obj ){
    var data = []
    for ( i in obj ){
        data.push( [ i , obj[i] ] );
    }        
    dt.fnClearTable();
    dt.fnAddData( data );
    // Not sure if this is a no-op when updating data 
    dt.makeEditable( {
        aoColumns:[
                        null, //read-only
                        {
                                tooltip: 'Click to edit metadata',
                                submit: 'Save changes'
                        }
                    ],
        sUpdateURL: function(value, settings)
                                {
                                        var name = $(this).prev().text(); //jesus what a bodge!
                                        metadata_edit[name] = value;
                                        return(value);
                                }
    });
}

// enable on geocode click
function popupMap(){
    //add new row
    createOrUpdate( metadata_edit, "ADDED ", "ADDED" );
    updateMediaData(dt, metadata_edit);
}

/*************** MAIN ***************/
$(document).ready(function(){
    /* remove loading indicator */
    setTimeout(function(){
            $('#loading').remove();
            $('#loading-mask').fadeOut(300, function() {$(this).remove()});
        }, 250);

    uuid = $('#uuid').text();
        
    dt = $('#mediaProps').dataTable( {
        "bJQueryUI": true,
        "sPaginationType": "full_numbers",
        "iDisplayLength": 25,
        "aoColumns": [
                        { "sTitle": "Name" },
                        { "sTitle": "Value"}
                    ]

        });    
    /////////////////////////////////////////////////////////////////
  
    /** Load global var metadata */
    $.getJSON("/ws/loadMetadata/" + uuid, function (data) {
        metadata_ori = data;
        metadata_edit = subObject( metadata_ori, exclude );
        updateMediaData( dt , metadata_edit );
    });

    $("#logo").show();
    $("#save").show();
    $("#geocode").show();
    $("#download").show();
    
    
});
