//Datatable decorator for something saner.



/** patch datables to exclude values in exclude array */
/*
$.fn.dataTableExt.afnFiltering.push( 
    function( oSettings, aData, iDataIndex ) {
        if (exclude.indexOf(aData[0]) != -1) {
            return false;
        }
        return true;
});*/


/** define datable Wrapper 
 * 
 *  Args as OBJECT:
 *      selector: jquery selector for datatable initialization 
 *      couples (optional): couples table should be a SUPERSET of all values that should be kept in sync.
 *      onload (option): funtion to execute after loading data (async)
 *      table_options (optional): list of table properties
 *      edit_all (optional): edit all properties (name + value) insted of just the value
 *      header_html (optional): html to use for header. This is non-std html manipulation so see examples in gtr.js. 
 */

GTRData = function (args){
        this.couples = args.couples || null;
        this.readonly = args.readonly || false;
        this.onload = args.onload || null;
        this.table_options = {
                    "bJQueryUI": true,
                    "sPaginationType": "full_numbers",
                    // "iDisplayLength": 18, //Paging -- use bLengthChange=25 to avoid displ probs
                    "bPaginate": false,
                    "sScrollY": "267px", //enable vertical scrolling using default height.
                    "aoColumns": [
                                    { "sTitle": "Name" },
                                    { "sTitle": "Value"}
                                ]
                };
        this.editor_options = [
                                args.edit_all ? { context: this, tooltip: 'Click to edit', onblur: 'submit' } : null, //null means read-only
                                {
                                        context: this, //I made up "context" param cause jeditable source uses $.extend to pass everything to sUpdateURL (talking about RTFM from source) 
                                        tooltip: 'Click to edit', 
                                        onblur: 'submit'
                                }
                            ];
        // overrride default table options if table_options argument is given 
        $.extend( this.table_options, args.table_options || {} );
        $.extend( this.editor_options, args.editor_options || {} );
        this.createTable(args.selector, args.header_html || null);
}

GTRData.prototype = {
    /** hidden properties for metadata */
    exclude: [ "Directory", "SourceFile" ],
    metadata_ori: [],
    metadata_edit: [],
    dt: null,
    uuid: null,
    parent: null,
    group: null,
    table_options: null,
    createTable: function ( selector, header_html ){
        //console.log("options are: "); console.log(this.table_options);
        this.dt = $(selector).dataTable(this.table_options);
        $(selector + "_filter").addClass("dataTables_filter_right")
        if (header_html != null){
            $(selector + "_filter").before($(header_html))
            console.log(selector + "_filter"); 
 
        }
    },
    /**
    * Load remote data on the metadata table
    * 
    * Args:
    *      table: metadata table object
    *      uuid: unique identifier of media file
    *      group (optional): Fetch specific tag group (e.g. EXIF). Default: eveything 
    */
    loadData: function (uuid, group){
        if (!group) {  group="ALL" }
        this.uuid = uuid;
        this.group = group;
        $.ajax({
            url: "/ws/loadMetadata/" + uuid,
            dataType: 'json',
            async: 'false',
            data: {group: group},
            context: this, //set the "symbol table" for the success callback
            success: function (data) {
                    this.metadata_ori = data;
                    this.metadata_edit = subObject( this.metadata_ori, this.exclude );
                    //this is a function with lexical scoping (its symbol table values is of the caller). 
                    this.updateMediaData(this.metadata_edit);
                }
        });
    },
    /********************************
    * Update media data and refresh (default)
    * Args:
    *   Datatable dt :  datatable to update
    *   Object obj : json object of data
    */
    'updateMediaData': function(obj ){
        var data = []
        for ( i in obj ){
            if ( obj[i] == "" ){ // empty keys are set for deletion
                continue;
            }
            data.push( [ i , obj[i] ] );
        }
        this.dt.fnClearTable();
        this.dt.fnAddData( data );
        if (!this.readonly){
            this.dt.makeEditable( {
                aoColumns: this.editor_options,
                sUpdateURL: function(value, settings){
                                // check if there is a previous child to selected cell (i.e the key "name") and switch to it.
                                cell = $(this);
                                parent = settings.context; // ditto -- could break with an newer version
                                if( cell.prev().length == 1 ){
                                    // We are changing a value (not key)
                                    key = cell.prev().text();
                                    key_value = value;
                                    parent.metadata_edit[key] = key_value;
                                }
                                else{
                                    // We are change the key name -- need to delete the old key and create a new one
                                    old_key = this.revert;
                                    new_key = value;
                                    console.log(old_key);
                                    console.log(cell);                                    
                                    key_value = cell.next().text();
                                    parent.metadata_edit[new_key] = key_value;
                                    parent.delete([old_key]);
                                }
                                return(value);
                            }
            });
        };
        if(this.onload){ 
            this.onload();
        }
    },
    /** Sets metadata_edit to DELETE a tag on the next save. Also refreshes screen */
    'delete': function(tagarray){
        diff = {}
        for (k in tagarray) {
            diff[ tagarray[k] ] = "";
        }
        console.log("delete::sync ");console.log(diff);
        this.sync(diff);
        this.syncCouples(diff);
    },
    /** CreateOrUpdate geotag coordinates to metadata */
    'geotag': function(lon, lat){
        /* Sync this tables and siblings WITHOUT saving */
        var gpsdata = { 
                GPSLatitude: lat,
                GPSLongitude: lon,
                GPSPosition: lat + " " + lon,
                GPSLatitudeRef: lat<0 ? "S" : "N",
                GPSLongitudeRef: lon<0 ? "W" : "E"
        };
        revgeo = getSyncJSON('http://api.geonames.org/findNearbyJSON?lat='+ lat + '&lng=' + lon + '&username=gtrtagger').geonames[0];
        gpsdata.GPSAreaInformation = revgeo.name + ', ' + revgeo.adminName1 + ', ' + revgeo.countryCode;
        this.sync(gpsdata);
        this.syncCouples(gpsdata); //slow
    },
    /** Anonimise coordinates by fuzzing or expunging */
    anonymise: function(method, tolerance){
        tolerance = tolerance || 1;
        if (method == "expunge"){
            this["delete"]( [ "GPSLatitude", "GPSLongitude", "GPSPosition", "GPSLatitudeRef", "GPSLongitudeRef" ] );
        }
        else if (method == "fuzzify"){ //fuzzify 1 decimal
            // TODO: refactor this after the re-design to use static metadata_edit for all groups
            
            // convert km to degrees (only work for < 5km or so roughly)
            tolerance = tolerance / 200;
            if ( exists(dtAll.metadata_edit.GPSLatitude) && exists(dtAll.metadata_edit.GPSLongitude) ) {
                diff = { 
                            "GPSLatitude" : dtAll.metadata_edit.GPSLatitude + Math.random()*tolerance - tolerance/2, 
                            "GPSLongitude" : dtAll.metadata_edit.GPSLongitude + Math.random()*tolerance - tolerance/2
                        };
                console.log("fuzzified  lat/long");
                console.log(diff);
                this.sync(diff)
                this.syncCouples(diff);
            }
        }
        else {
            console.log("this shouldn't happen");
        }
    },
    /** If there is a coupled datatable it will be synchronized with this one 
     * 
     * Args: 
     *          the Updated Metadata ONLY i.e. the diff. The target will only include them if it already has them
     **/
    syncCouples: function(updated_data) {
        if (this.couples == null){
            console.log(this.group + " has no couples. Skipping sync");
            return;
        }
        $.each(this.couples, function(){
            this.sync(updated_data);
        });
    },
    /** update existing data with data and refresh display (w/o saving) */
    sync: function( data ){
        this.updateMediaData( $.extend(this.metadata_edit,data) );
    },
    /** save global metadata to Server. Syncs automatically with "couples" */
    save: function() {
        // FYI: without "var" the variables below will not remain in the "this" context
        var updated_metadata = diffObject( this.metadata_ori, this.metadata_edit );
        if ( $.isEmptyObject(updated_metadata)){
            console.log(this.group + " has no data to upgrade. Skipping..." );
            return;
        }
        var metadata_js = $.toJSON(updated_metadata);
        $.ajax({
            type: "POST",
            dataType: "json",
            url: "/ws/saveMetadata/" + this.uuid,
            context: this,
            success: function(resp) {
                message = resp.msg;
                if (resp.error == 1){
                    //reset edited metadata
                    this.metadata_edit = subObject( this.metadata_ori, this.exclude );
                    this.updateMediaData(this.metadata_edit);
                }
                
                // Now sync parent
                this.syncCouples(updated_metadata)
                
                $("#operation-dialog").dialog({
                    title:'Save request',
                    width: message.length * 14,
                    autoHeight: true,
                    buttons:  [{
                        text: 'Ok',
                        click: function(){
                            $(this).dialog("close");
                    }}],
                    autoOpen: false,
                    hide:     'slide',
                    show:     'slide',
                    resizable: false
                });
                $("#operation-dialog").dialog('open');
                $("#od-contents").text(message);
            },
            failure: function(msg) {
                $("#operation-dialog").dialog({
                    title:'Failure',
                    width: message.length * 14,
                    autoHeight: true,
                    buttons:  [{
                        text: 'Ok',
                        click: function(){
                            $(this).dialog("close");
                    }}],
                    autoOpen: false,
                    hide:     'slide',
                    show:     'slide',
                    resizable: false
                });
                $("#operation-dialog").dialog('open');
                $("#od-contents").text("<pre>Unable to update the metadata on the server!</pre>");
            },
            data: { 
                metadata : metadata_js,
                group: this.group
            }
        });
    }
}


