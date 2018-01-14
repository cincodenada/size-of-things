var container;
var ships;
var min_size_px = 5
var m_per_px = 10
var zoomSlowFactor = 100
var screen_px_per_mm = 96/2.54
var loaded = false

var FancyNumber = (function(number, sigfigs) {
  var number_names = [
    'million', 'billion', 'trillion', 'quadrillion','quintillion',
    'sextillion','septillion','octillion','nonillion','decillion'
  ]
  var si_units = ['nm','µm','mm','m','km']
  var si_offset = 3

  function FancyNumber(number, sigfigs) {
    if(!sigfigs) { sigfigs = 1 }
    this.zeroes = Math.floor(Math.log10(number))
    this.groups = Math.floor(this.zeroes/3)
    this.number = number
    this.sigfigs = sigfigs
  }

  FancyNumber.prototype.setSigFigs = function(digits) {
    this.sigfigs = digits
  }

  FancyNumber.prototype.roundSigFig = function() {
    if(!sigfigs) { sigfigs = 1; }
    var num_clear = this.zeroes - (sigfigs-1)
    var out_num = Math.round(this.number/Math.pow(10, num_clear)) * Math.pow(10, num_clear)
    if(num_clear < 0) { out_num = out_num.toFixed(-num_clear) }
    return out_num
  }

  FancyNumber.prototype.getHuman = function() {
    var out_num = this.roundSigFig()
    if(this.groups >= 2) {
      out_num /= Math.pow(10, this.groups*3)
      out_num = out_num + " " + number_names[this.groups-2]
    } else if(this.groups == 1) {
      out_num = out_num.toString().substring(0,this.zeroes-2) + ',' + out_num.toString().substring(this.zeroes-2)
    }
    return out_num
  }

  FancyNumber.prototype.getUnits = function() {
    var si_idx = this.groups + si_offset;
    if(si_idx < 0) { si_idx = 0 }
    if(si_idx >= si_units.length) { si_idx = si_units.length - 1 }
    power_adj = si_idx - si_offset
    var out_num = this.roundSigFig()/Math.pow(10, power_adj*3)
    if(power_adj < 0) {
      var decimals = (power_adj+1)*3-(this.zeroes+1)
      out_num = out_num.toFixed(decimals)
    }
    return out_num + " " + si_units[si_idx]
  }

  return new FancyNumber(number, sigfigs)
})

$(function() {
  container = $('.stuff')
  $.getJSON("ships.json").done(function(data) {
    ships = data;
    initialize_ships();
  })

  // Figure out px/mm

  $(window).on('mousewheel', function(evt) {
    evt.preventDefault();
    m_per_px *= Math.pow(10, evt.deltaY/zoomSlowFactor);
    resize();
  })
})

function initialize_ships() {
  resize();
}

function set_size(px_width, elm) {
  if(!elm) {
    // We're an event handler, first arg is evt data
    elm = this
    px_width = px_width.px_width
  }
  var ratio = px_width/elm.naturalWidth
  elm.width = px_width
  elm.height = elm.naturalHeight*ratio
  console.log("Set size")
  console.log(px_width)
  console.log(elm)
}

function resize() {
  for(var i = ships.length-1; i >= 0; i--) {
    var ship = ships[i];
    var info = ship.info
    if(!info.Length) {
      console.log("Error: No length for " + info.Name)
      continue
    }
    var px_width = info.Length/m_per_px
    if(px_width > min_size_px) {
      var reinsert = false
      if(!ship.elm) {
        ship.elm = $('<img class="thing"></img>')
        ship.elm.prop('src', ship.path + '/' + ship.filename)
        reinsert = true;
      }
      if(ship.elm.prop('complete')) {
        set_size(px_width, ship.elm.get(0))
      } else {
        console.log("Deferring size for " + ship['info']['Name'])
        ship.elm.on('load', {px_width: px_width}, set_size)
      }
      if(reinsert) { container.prepend(ship.elm) }
    } else {
      if(ship.elm) {
        container.get(0).removeChild(ship.elm);
        ship.elm = false;
      }
    }
  }
  var text_elm = $('.status')
  text_elm.find('.m_per_px').text((new FancyNumber(m_per_px, 3)).getUnits());
  real_to_screen = m_per_px*1000*screen_px_per_mm
  if(real_to_screen < 1) {
    text_elm.find('.ratio').text('1:' + new FancyNumber(1/real_to_screen).getHuman())
  } else {
    text_elm.find('.ratio').text(new FancyNumber(real_to_screen).getHuman() + ':1')
  }
  if(!loaded) {
    text_elm.find('.loading').hide()
    text_elm.find('.loaded').show()
    loaded = true
  }
}
