$(function(){ // on dom ready

$('#cy').cytoscape({
  layout: {
    name: 'preset',
    padding: 10
  },
  
  style: cytoscape.stylesheet()
    .selector('node')
      .css({
        //'width': 'mapData(weight, 40, 80, 20, 60)',
        'content': 'data(name)',
        'text-valign': 'center',
        'text-outline-width': 1,
        //'text-outline-color': 'data(faveColor)',
        //'background-color': 'data(faveColor)',
        'color': '#ffffff'
      })
    .selector('node.province')
      .css({
          'shape': 'ellipse',
          'width': 40,
          'height': 40,
      })
    .selector('node.satellite')
      .css({
          'shape': 'rectangle',
          'width': 20,
          'height': 20,
      })
    .selector('node.fareast')
      .css({
          'shape': 'rectangle',
          'width': 30,
          'height': 70,
      })
    .selector('node.newworld')
      .css({
          'shape': 'rectangle',
          'width': 30,
          'height': 70,
      })
    .selector(':selected')
      .css({
        'border-width': 3,
        'border-color': '#333'
      })
    .selector('edge')
      .css({
        'width': 5,
        //'width': 'mapData(strength, 70, 100, 2, 6)',
        //'target-arrow-shape': 'triangle',
        //'source-arrow-shape': 'circle',
        //'line-color': 'data(faveColor)',
        //'source-arrow-color': 'data(faveColor)',
        //'target-arrow-color': 'data(faveColor)'
      })
    .selector('edge.inland')
      .css({
        'line-color': '#cc9900',
        'width': 5,
      })
    .selector('edge.sea')
      .css({
        'line-style': 'dotted',
        'line-color': '#0099ff',
        'width': 30,
      })
    .selector('edge.support')
      .css({
        'line-color': '#000000',
        'target-arrow-shape': 'triangle'
      }),
  ready: function(){
    window.cy = this;
/*
    var cy = $('#cy').cytoscape('get');
    cy.add([
         { group: "nodes", data: { id: 'a', name: 'a' } },
         { group: "nodes", data: { id: 'b', name: 'b'} },
    ]);
*/
    // giddy up
  }
});

$(document).ready(function(){
    var skin_data, map_data;

    $.when(
        $.getJSON($('#skin_url').val(), function(data) {
            skin_data = data;
        }).fail( function(data, textStatus, error) {
            console.error("getJSON(#skin_url) failed, status: " + textStatus + ", error: "+error)
        }),  
        $.getJSON($('#map_url').val(), function(data) {
            map_data = data;
        }).fail( function(data, textStatus, error) {
            console.error("getJSON(#map_url) failed, status: " + textStatus + ", error: "+error)
        })
    ).then( function() {
        var cy = $('#cy').cytoscape('get');
        var province_map = [];
        var x_max = skin_data.map_area.x_max;
        var y_max = skin_data.map_area.y_max;
        // add all provinces to nodes 
        var provinces = []
        for (var i in map_data.provinces) {
            var p = map_data.provinces[i].fields;
            var p_pk = map_data.provinces[i].pk;

            province_map[p_pk] = p.short_name;
            provinces.push({
                data: { id: p.short_name, name: p.full_name },
                position: { x: p.x / x_max * cy.width(), y: p.y / y_max * cy.height() },
                locked: true,
                classes: ( p.market_size == 1 ? 'satellite' : ( p.area == 'F' ? 'fareast' : ( p.area == 'N' ? 'newworld' : 'province' ) ) ),
            });
        }
        cy.add( {nodes:provinces} );

        // add inland edge
        var inland_edge = []
        for (var i in map_data.provinces) {
            var p = map_data.provinces[i].fields;
            var p_pk = map_data.provinces[i].pk;

            //for (var j=0; p.connected != undefined && j < p.connected.length; ++j ) {
            for (var j in p.connected ) {
                if ( p.connected[j] > p_pk && p.connected[j] in province_map ) {
                    inland_edge.push({
                        data: { 
                            id: p.short_name + '_' + province_map[p.connected[j]], 
                            source: p.short_name, 
                            target: province_map[p.connected[j]] 
                        },
                        classes: 'inland',
                    });
                }
            }
        }
        cy.add( {edges:inland_edge} );
        //$('#json').text( cy.json() );
        //console.log( JSON.stringify({nodes:provinces, edges:inland_edge} ));
    });
    /*
    var cy = $('#cy').cytoscape('get');
    cy.add({ nodes: [
         { data: { id: 'h', name: 'iizs' }, position: {x:100, y:0}, locked: true },
         { data: { id: 'k', name: 'inome'} },
         { data: { id: 'a', name: 'inome2'} }
    ]});
    //cy.getElementById('h').position( {x:0, y:0} );
    cy.getElementById('k').position( {x:100, y:100} );
    cy.getElementById('a').position( {x:0, y:100} );
    */
})

}); // on dom ready
