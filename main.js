var container;
var ships;
var min_size_px = 50;
$(function() {
  container = $('.stuff')
  $.getJSON("ships.json").done(function(data) {
    ships = data;
    initialize_ships();
  })
})

function initialize_ships() {
  resize(2);
}

function resize(m_per_px) {
  $.each(ships, function(idx, ship) {
    var info = ship.info
    var px_width = info.Length/m_per_px
    if(px_width > min_size_px) {
      if(!ship.elm) {
        ship.elm = $('<img class="thing"></img>').get(0)
        ship.elm.src = ship.path + '/' + ship.filename
        container.append(ship.elm)
      }
      var ratio = px_width/ship.elm.naturalWidth
      ship.elm.width = px_width
      ship.elm.height = ship.elm.naturalHeight*ratio
    } else {
      if(ship.elm) { container.remove(elm); }
    }
  })
}
