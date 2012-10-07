// UUID of media object. Set when uploading a file or by setting uuid=XXX parameter in the URL
var uuid=null;

// Error messages queue (buffers messages for asynchronous display to user)
var msgfifo = [];

//unlock API base url:
var unlock = "http://unlock.edina.ac.uk/ws/"

/** save global metadata */
function download(uuid) {
    window.location = 'http://' + window.location.host + '/ws/getfile/' + uuid;
}

/** save exported metadata */
function exportXMP(uuid) {
    window.location = 'http://' + window.location.host + '/ws/export/' + uuid;
}

/**************** OL Declarations *******************/
    var wgs84 = new OpenLayers.Projection("EPSG:4326"); // WGS 1984 Projection
    var osm = new OpenLayers.Projection("EPSG:900913"); // Spherical Mercator Projection
    var map=undefined; // without "undefined" chrome breaks as it searches for a DIV named map (well done google!)
    var lon = -1.40000; 
    var lat = 54.00000;
    var zoom = 7;
    var extent = new OpenLayers.Bounds(-7.49714,50,3.86,60.13).transform(wgs84,osm);
    var base;

    var map_options = {
          controls: [ 
                        new OpenLayers.Control.PanZoomBar(),
                        new OpenLayers.Control.Navigation(),
                        new OpenLayers.Control.MousePosition(),
                        new OpenLayers.Control.Attribution()
                    ],
          projection: new OpenLayers.Projection("EPSG:900913"),
          displayProjection: new OpenLayers.Projection("EPSG:4326"), //for MousePosition only          
          format: "image/png",
          maxResolution: "auto",
          maxExtent: extent,
          numZoomLevels: 7
    };

   /************************* BASE LAYERS **********************************/

    /** OS Free:  OSOpenData {Streetview,VMD_Raster,Raster_250k,Miniscale_100,GB}  THROUGH GWC WMS emulation */
    var osattr = "Contains Ordnance Survey data. (c) Crown copyright and database right 20XX. Data provided by Digimap OpenStream, an EDINA, University of Edinburgh Service."
    var base = new OpenLayers.Layer.OSM()
    
    /** extra layers **/
    var markers = new OpenLayers.Layer.Markers("Markers");
    var geograph = new Geograph(map);
/**************** OL Declarations END *******************/

/** Geo specific functions */
function popupMap(){
    if (map==undefined){
        $("#mapPane").show();
        //*** OL setup ***/
        map = new OpenLayers.Map( 'map', map_options ); //implied "EPSG:4326"
        map.addLayers([base, markers]);
        map.setCenter(new OpenLayers.LonLat(-2.55,54.67).transform(wgs84,osm), 6);
        
        /** Add jquery search bar */
        $("#unlockAutoComplete").autocomplete({
                source: function(request, response){
                    $.ajax({
                        url: unlock + "search",
                        dataType: "jsonp",
                        data: {
                            format: 'json', // Retrieve the results in JSON format
                            maxRows: 10, // Limit the number of results to 10
                            count: 'no', // Prevent Unlock from counting the total possible results (faster)
                            name: request.term + '*' // Search for partial names
                        },
                        success: function(data){
                            response( $.map( data.features, function( item ) {
                                return {
                                    label: item.properties.name + ", " + item.properties.countrycode,
                                    value: item.properties.name + ", " + item.properties.countrycode,
                                    centroid: item.properties.centroid
                                }
                            }));
                        }
                    });
                },
                minLength: 3, // User must type 3 characters before a search is performed
                select: function( event, ui){
                    //ui.item
                    var centroid = $.map ( ui.item.centroid.split(',') , parseFloat )
                    map.setCenter(new OpenLayers.LonLat(centroid[0], centroid[1]).transform(wgs84,osm), 10);                    
                }
        });
    }
}

/** Add right-click event to map */
function addRightClickEvent(){
       $("#map").contextMenu({
                                menu: "mapMenu"
                             }, function(action, el, pos) {
                                    var coords = map.getLonLatFromViewPortPx(new OpenLayers.Pixel(pos.x, pos.y)).transform(osm,wgs84);
                                    if (action == "updatemarker"){
                                        dtExif.geotag( coords.lon , coords.lat );
                                        displayCoordinates(dtExif.metadata_edit);
                                    }
                                    if (action == "geograph"){
                                        var md = dtAll.metadata_edit
                                        if (exists(md.GPSLatitude) && exists(md.GPSLongitude)){
                                            geograph.load(md.GPSLongitude , md.GPSLatitude);
                                            map.setCenter(new OpenLayers.LonLat(md.GPSLongitude , md.GPSLatitude).transform(wgs84,osm), 13);
                                        }
                                    }
                            });
}

/** 
 * Add marker if metadata contain GPSLongitude and GPSLatitude 
 * 
 * Args:
 *    md: metadata
 */
function displayCoordinates(md){
    if (exists(md.GPSLatitude) && exists(md.GPSLongitude)){

        //remove old marker if they exist
        markers.clearMarkers();
        
        //create new marker
        var y = md.GPSLatitude;
        var x = md.GPSLongitude;
        var size = new OpenLayers.Size(21,25);
        var offset = new OpenLayers.Pixel(-(size.w/2), -size.h);
        var icon = new OpenLayers.Icon('/js/OpenLayers-2.11/img/marker.png', size, offset);
        markers.addMarker(new OpenLayers.Marker(new OpenLayers.LonLat(x,y).transform(wgs84,osm),icon));
        if (map.getLayersByName("Markers").length == 0) {
            map.addLayer(markers);
        }
    }
    else { perror("No coordinates found!");}
}

/**
 * Display notification messages to user in a non-obtrusive way
 * 
 * This is multi threaded with no locking semantic (js sucks) so we just display the first message in the queue
 */

function perror(msg){
        msgfifo.push(msg);
        if (msgfifo.length > 1) return; //another thread is on.
        $('#perror').text(msg)
                    .show()
                    .css({ opacity: 1.0 }).animate( { opacity: 0.0 }, 5000, 
                                                                    function(){
                                                                        msgfifo.shift() //remove my message
                                                                        if (msgfifo.length>0){
                                                                            console.log ("Got message waiting: " + msgfifo[0]);
                                                                            perror( msgfifo.shift());
                                                                        }
                                                                    } );
}

/* Initialize page elements AFTER we have a uuid of a mediafile */
function init(uuid){
        dtAll.loadData(uuid,"ALL");
        dtExif.loadData(uuid,"EXIF"); 
        dtXMP.loadData(uuid,"XMP");
        dtIPTC.loadData(uuid,"IPTC");
        dtCustom.loadData(uuid,"Custom");
        dtAll.dt.dblclick( function() { perror('"All" Grid is not editable.')} );
        $('#thumbnail').css("background-image", "url(/ws/getfile_inline/" + uuid +")").css("background-size", "100%");
        $('#permalink').attr("href",'http://' + window.location.host + '/index.html?uuid=' + uuid);
        popupMap();
        addRightClickEvent();
        
        dbox = new GTRDropbox({callback_url:'/ws/editfile/'+ uuid, 
                               uuid: uuid, 
                               herald: function(msg){ 
                                                    display(msg);
                                                },
                               onsuccess: function(data){
                                                    messageWindow(data.msg, 'Direct link: <a href="' + data.url + '">' + data.url + '</a>', data.url.length * 9);
                                                }
        });
        
        /* set callbacks */
        $('#save').on("click", function(){ 
                $.each([dtExif,dtXMP,dtIPTC,dtCustom], function (x){
                    this.save();
                });         
        });
        $('#export').on("click", function (){ exportXMP(uuid) });
        $('#download').on("click", function (){ download(uuid); });
        $('#anonymise').on("click", function (){ 
                anonymise_dialog.dialog("open").show();
            });
        /* Dropbox support */
        $('#dropbox').on("click", function (){
            perror("Initiating Dropbox connection...");
            dbox.upload(uuid);
        });
}

/*************** MAIN ***************/
$(document).ready(function(){
    /* remove loading indicator */
    setTimeout(function(){
            $('#loading').remove();
            $('#loading-mask').fadeOut(300, function() {$(this).remove()});
        }, 250);

    /* Get uuid */
    if ( re = window.location.search.match(/uuid=([0-9a-f]+)/) ){
        uuid = re[1];
    }
    
    /* Initialize tables */
    
    dtAll = new GTRData({
                    selector: '#mediaProps',
                    readonly: true, 
                    onload: function(){ 
                            displayCoordinates (dtAll.metadata_edit) 
                        },
                    header_html: '<div class="rednote dataTables_filter_left">Note view only; click other tabs to edit content</div>'
            });    
    dtExif = new GTRData({selector: '#mediaPropsEXIF', couples:[dtAll]});
    dtXMP = new GTRData({selector:'#mediaPropsXMP', couples:[dtAll]});
    dtIPTC = new GTRData({ selector:'#mediaPropsIPTC', couples:[dtAll] });
    dtCustom = new GTRData({ 
                           selector:'#mediaPropsCustom',
                           table_options: {  "oLanguage": { sEmptyTable: 'Right click inside the table to add new tags!'  } },
                           edit_all: true,
                           couples:[dtAll],
                           header_html: '<div class="rednote dataTables_filter_left">Right click to add values!</div>',
                           onload: function(){
                                         // Covers the whole table canvas area
                                         $('#mediaPropsCustom_wrapper .dataTables_scrollBody').contextMenu({
                                                menu: "customMenu",
                                                mycontext: this
                                            }, function(action, el, pos, context) {
                                                console.log("canvas");                                                
                                                if ( action == "new" ){
                                                    create_dialog.dialog("open").show();
                                                    //context.sync( { "Click to edit Name":"Click to edit Value"});
                                                }
                                            });
                                         // Covers Area with Cells
                                          $('table#mediaPropsCustom td').contextMenu({
                                                    menu: "customMenu",
                                                    mycontext: this
                                             }, function(action, el, pos, context) {
                                                if ( action == "new" ){
                                                    //create_dialog.dialog("open").show();
                                                    context.sync( { "Click to edit Name":"Click to edit Value"}) 
                                                    }
                                                if ( action == "delete" ){
                                                // check if there is a previous child to selected cell (i.e the key "name") and switch to it.
                                                    cell = $(el);
                                                    if( cell.prev().length == 1 ){
                                                        cell = cell.prev();
                                                    }
                                                    console.log("deleting :" + cell.text());                                                    
                                                    context.delete([ cell.text() ]);
                                                }
                                         }); 
                           }
    });
            
    /* Create file upload control */
    $('#uploadForm').ajaxForm({
         context: this,
         beforeSubmit: function(arr, $form, options) {
             if ( ! $('#agreep').attr("checked") ){
                perror("Please accept the terms. Upload canceled.");
                return false;
             }
             $('#thumbnail').css("background-image", "url(../images/busy/busy.gif)").css("background-size", "10%");  
             return true;
         },
         success: function (res, status, xhr, form)  {
             /* res has {msg, uuid, error} according to GTR API spec. */
             //show upload response message
             perror($.trim(res.msg))
             if (res.error == 0){
                //update global uuid
                uuid = res.uuid;
                init(uuid);
             }
        } 
    
    });

    /* Select coord system */
    $("#srsvalue").change( function(){
            console.log("changed: ", $(this).val());
            perror("Only Lat/Lon is currently supported");
        });
    
    /* Create tabs -- resize datatable on show */
    $("#tabs").tabs({
            "show": function (event, ui) { 
                var oTable = $('div.dataTables_scrollBody>table', ui.panel).dataTable();
                if ( oTable.length > 0 ) {
                        oTable.fnAdjustColumnSizing();
                }
                switch (ui.index){
                    case 4: if (uuid) $('#create').show();
                            break;
                    default: $('#create').hide();
                }
            }
    });
    
                    
   /* resize datatable columns when user resizes window */
   $(window).resize(function () {
        var oTable = $('div.dataTables_scrollBody>table').dataTable();
                if ( oTable.length > 0 ) {
                        oTable.fnAdjustColumnSizing();
                }
    });

   
    var create_dialog = $('#create-custom-dialog')
         .dialog({
                 autoOpen: false,
                 title: 'Create Metadata',
                 modal: true,
                 height: 300,
                 width: 350,
                 buttons: {
                         "Create a new tag": function() {
                                 diffobj = {}
                                 diffobj[ $('#name').val() ] = $('#value').val();
                                 dtCustom.sync(diffobj);
                                 $( this ).dialog( "close" );
                             },
                         Cancel: function() {
                                 $( this ).dialog( "close" );
                             }
                         },
                 open: function() {
                    // make Create button focus so that the user can click it with "enter" key
                    $(this).parents('.ui-dialog-buttonpane button:eq(0)').focus();
                 },
                 close: function() {
                     //allFields.val( "" ).removeClass( "ui-state-error" );
                 }               
         });

     anonymise_dialog = $('#anonymise-dialog')
         .dialog({
                 autoOpen: false,
                 title: 'Anonymise Media',
                 modal: true,
                 height: 300,
                 width: 350,
                 buttons: {
                         "OK": function() {
                                 method =  $('select[name="anomethod"]').val();
                                 console.log ("method is "+ method);
                                 tolerance = $('input[name="tolerance"]').val();
                                 dtExif.anonymise(method,tolerance);
                                 displayCoordinates(dtExif.metadata_edit);
                                 $( this ).dialog( "close" );
                             },
                         Cancel: function() {
                                 $( this ).dialog( "close" );
                             }
                         },
                 close: function() {
                     //allFields.text("");
                 }               
         });
     /* anon dialog */
        $('select[name="anomethod"]').change( function(){
            if ( $(this).val() == "expunge" ){
//                 $("#tolerance").attr('disabled', 'disabled');
                $('#fuzzifyform').css( { 'opacity': 0.0 } ); 
            }
            else {
                $('#fuzzifyform').css( { 'opacity': 1.0 } ); 
//                 $("#tolerance").val('').removeAttr("disabled");
            }
            
        });
        
        $("select[name=license_sel]").combobox();
        
        $("#upload").cluetip({ cluezIndex:"20000", rel:"/docs/supported_files.html", positionBy:"right", width: 400, sticky: false });
        
	$(".logo").mouseover(function() {
            makeWindow("/docs/about.html","About Tagger", 580, 200, "aboutdlg");
        });
        
        //help popup
        $("#help1").on("click", function() {
            makeWindow("/docs/help1.html","Tagger Help", 1200, 1024, "helpdlg");
        });
        $("#help2").on("click", function() {
            makeWindow("/docs/help2.html","Tagger Help", 1300, 1024, "helpdlg");
        });
       
        /* Load data if we have a uuid */
        if (uuid){
            init(uuid);
        }
        else{ //someone is just using index.html
            $('#permalink').attr("href",window.location.href);
        }
    
        $('#container').css({opacity: 0.0, visibility: "visible"}).animate({opacity: 1.0});
});
