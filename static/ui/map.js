$(function(){ // on dom ready

$('#cy').cytoscape({
  layout: {
    name: 'preset',
    padding: 10
  },
  
  style: cytoscape.stylesheet()
    .selector('node')
      .css({
        //'shape': 'data(faveShape)',
        'width': 'mapData(weight, 40, 80, 20, 60)',
        'content': 'data(name)',
        'text-valign': 'center',
        'text-outline-width': 2,
        //'text-outline-color': 'data(faveColor)',
        //'background-color': 'data(faveColor)',
        'color': '#fff'
      })
    .selector(':selected')
      .css({
        'border-width': 3,
        'border-color': '#333'
      })
    .selector('edge')
      .css({
        'width': 'mapData(strength, 70, 100, 2, 6)',
        'target-arrow-shape': 'triangle',
        'source-arrow-shape': 'circle',
        'line-color': 'data(faveColor)',
        'source-arrow-color': 'data(faveColor)',
        'target-arrow-color': 'data(faveColor)'
      })
    .selector('edge.questionable')
      .css({
        'line-style': 'dotted',
        'target-arrow-shape': 'diamond'
      })
    .selector('.faded')
      .css({
        'opacity': 0.25,
        'text-opacity': 0
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
    var cy = $('#cy').cytoscape('get');
    cy.add([
         { group: "nodes", data: { id: 'h', name: 'iizs' }, position: {x:100, y:0}, locked: true },
         { group: "nodes", data: { id: 'k', name: 'inome'} },
         { group: "nodes", data: { id: 'a', name: 'inome2'} },
    ]);
    //cy.getElementById('h').position( {x:0, y:0} );
    cy.getElementById('k').position( {x:100, y:100} );
    cy.getElementById('a').position( {x:0, y:100} );
})

}); // on dom ready
