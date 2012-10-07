//Geograph support

Geograph = function (map)
{
    /* static */
    this.map = map;
    this.gmarkers = new OpenLayers.Layer.Markers("Geograph")
}

Geograph.prototype = {

    // map
    map: null,
    // geograph markers
    gmarkers: null,
    /* load with new coordinates */
    load: function (x,y) {
        $.ajax({
            url: "/ws/nearest",
            dataType: 'json',
            data: {
                lon: x,
                lat: y
            },
            context: this, //set the "symbol table" for the success callback
            success: function (data) {
                    this.updateMap(data)
                }
        });
    },
    updateMap: function (data){
        gmarkers = this.gmarkers;
        gmarkers.clearMarkers();
        $.each( data, function() {
            var x = this[5];
            var y = this[6];
            var size = new OpenLayers.Size(21,25);
            var offset = new OpenLayers.Pixel(-(size.w/2), -size.h);
            console.log ( "lon/lat " + x + " " + y ); 
            var icon = new OpenLayers.Icon('/js/OpenLayers-2.11/img/marker-blue.png', size, offset);
            var m = new OpenLayers.Marker(new OpenLayers.LonLat(x,y).transform(wgs84,osm),icon);
            m.events.register('mousedown', this, function(ev) {  
                // context here is "this marker"
                    var id = this[0]; //id
                    var author = this[1]; //author
                    var title = this[2]; //aka short desc.
                    var desc = this[4]; // long desc
                    showGeograph( id, author, title, desc);
            });
            gmarkers.addMarker(m);            
        });
        if (map.getLayersByName("Geograph").length == 0) {
            map.addLayer(gmarkers);
        }
    }
}
