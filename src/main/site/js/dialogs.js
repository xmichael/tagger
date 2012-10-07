/** Some JUI extention functions, if your webapp is heavily template based. */

function makeWindow(url, title, wdth, hght, element){
    $('<div id="'+element+'" title="'+title+'" class="ui-dialog-title"></div>').appendTo($('body'));

    var htmlData = getAjaxHtml(url); // syncronous/blocking
    var div = "#"+element;
    $(div).html(htmlData);

    return openWindow(element, title, wdth, hght); 
}

function getAjaxHtml(url){
    var htmlData = null;
    $.ajax({
        url: url,
        dataType: 'html',
        async: false,
        success: function(data) {
            htmlData = data;
        }
    });
    return htmlData;
}

function openWindow(element, title, wdth, hght){
    var div = "#"+element;
    $(div).dialog({
        position: [100,10],
        autoOpen: false,
        height: hght,
        width: wdth,
        zIndex: 9999, 
        modal: false,
        "title": title
    });
    return $( div ).dialog( "open" ); 
}


//*** GTR Specific */
function showGeograph( id, author, title, desc)
{   
    /* Create Geograph preview image */
    var url = "/ws/geograph_image/" + id;
    var orig_url = 'http://www.geograph.org.uk/photo/' + id;
    var attribution = '© Copyright ' + author + ' and licensed for reuse under ' + 
        '<a href="http://creativecommons.org/licenses/by-sa/2.0/">this</a> Creative Commons Licence';
        
    $('#gm-title').html('<b>' + title + '</b> <a id="onedit_anchor" href="#">Open in Editor<a/>');

    $('#gm-link').attr("href", orig_url);
    $('#gm-thumbnail').css("background-image", "url(/ws/geograph_image/" + id +")")
                      .css("background-size", "100%")
                      .css("margin-top", "1em");
    $('#gm-desc').text(desc);
    $('#gm-attribution').html(attribution)
                        .css("font-size","xx-small");
    d = $('#gm-dialog').dialog({
        autoOpen: false,
        height: 300,
        width: 500,
        zIndex: 20000, 
        modal: false,
        title: 'Geograph Image',
        open: function(event, ui) {  $('#gm-thumbnail').show(); },
        beforeClose: function(event, ui) { $('#gm-thumbnail').hide(); }
    });
    
    /** Add edit_geograph functionality */
    $('#onedit_anchor').click( function(){
            var geograph_uuid;
            // start busy
            $('#gm-thumbnail').css("background-image", "url(../images/busy/busy.gif)").css("background-size", "10%");

            // asynchronous ajax to get new copy of file
            $.ajax({
                        url: '/ws/edit_geograph/' + id,
                        dataType: 'json',
                        async: false,
                        success: function(data) {
                            geograph_uuid = data.uuid;
                        }
                    });
            // start over with new uuid
            console.log("Got geograph_uuid: " + geograph_uuid ); window.location = '/index.html?uuid=' + geograph_uuid;
            if ( geograph_uuid == undefined ){
                return false;
            }
            return true; //needed to activate href
    } );
    
    d.dialog("open");
}

// display operation as modal window:
function messageWindow( title, message, length){
                var length = length || message.length * 14
                $("#operation-dialog").dialog({
                    title: title,
                    width: length,
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
                $("#od-contents").html(message);
                $("#operation-dialog").dialog('open');
}

/** Display background banner message to user */

display.prototype = { fifo : [] };

function display(text){
        display.prototype.fifo.push(text);
        if (display.prototype.fifo.length > 1) return; //another thread is on
        
        $("<div id='message'>" + text + "</div>").css({
        position:"fixed",
        top:"0px",
        left:"0px",
        "z-index": "9999",
        height:"20px",
        width:"100%",
        backgroundColor:"#cccccc",
        color:"blue",
        padding:"5px",
        fontWeight:"bold",
        textAlign:"center",
        display:"none",
        opacity:"0.5"
    })
    .appendTo("body");
    $("#message").slideDown(2500, function () { 
                                            $(this).slideUp(2500, function (){ 
                                                                $(this).remove() 
                                                                display.prototype.fifo.shift() //remove my message
                                                                if (display.prototype.fifo.length>0){
                                                                    //console.log ("Got dialog text waiting: " + display.prototype.fifo[0]);
                                                                    display( display.prototype.fifo.shift())
                                                                }
                                                            });
                                        }
                                );    
}
