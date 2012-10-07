/** create a new object that does *not* include the fields in an array 
 * src: source object
 * exclude: array of fields to exclude
 */
function subObject ( src, exclude ){
    dst = {};
    for ( k in src ){
        if ( $.inArray(k,exclude) == -1 ){ 
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

//like getJSON but SYNCHRONOUS. data is optional
function getSyncJSON(url, data){
    var out = null;
    $.ajax({
        url: url,
        dataType: 'json',
        async: false,
        success: function(data) {
            out = data;
        },
        data: data
    });
    return out;
}

