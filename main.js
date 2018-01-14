$(function() {
  container = $('.stuff')
  jQuery.getJSON("ships.json").done(function(data) {
    $.each(data, function(idx, ship) {
      elm = $('<img class="thing"></img>')
      elm.attr('src', ship.path + '/' + ship.filename)
      container.append(elm)
    })
  })
})
