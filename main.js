var container;
var ships;
var min_size_px = 5
var m_per_px = 10
var zoomSlowFactor = 100
var screen_px_per_mm = 96/2.54
var loaded = false
var remaining_to_load
var current_load
var load_timeout = 500
var center_offset;

var FancyNumber = (function(number, sigfigs) {
  var number_names = [
    'million', 'billion', 'trillion', 'quadrillion','quintillion',
    'sextillion','septillion','octillion','nonillion','decillion'
  ]
  var si_units = ['nm','µm','mm','m','km']
  var si_offset = 3

  function FancyNumber(number, sigfigs) {
    this.zeroes = Math.floor(Math.log10(number))
    this.groups = Math.floor(this.zeroes/3)
    this.number = number
    this.sigfigs = sigfigs
  }

  FancyNumber.prototype.setSigFigs = function(digits) {
    this.sigfigs = digits
  }

  FancyNumber.prototype.roundSigFig = function() {
    if(this.sigfigs) {
      var num_clear = this.zeroes - (this.sigfigs-1)
      var out_num = Math.round(this.number/Math.pow(10, num_clear)) * Math.pow(10, num_clear)
      if(num_clear < 0) { out_num = out_num.toFixed(-num_clear) }
      return out_num
    } else {
      return this.number
    }
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

  $('.px_mm').text(screen_px_per_mm.toFixed(2))

  $(window).on('mousewheel', function(evt) {
    evt.preventDefault();
    m_per_px *= Math.pow(10, -evt.deltaY/zoomSlowFactor);
    resize();
  })

  $(window).on('resize', update_windowsize)
  update_windowsize()

  $('.stuff').on('mouseover', 'img', function() {
    infodiv = $('.info')
    infodiv.find('.universe').text(this.data.info.Universe)
    infodiv.find('.faction').text(this.data.info.Faction)
    infodiv.find('.name').text(this.data.info.Name)
    infodiv.find('.length').text(this.data.info.Length)
    ship_rect = this.getBoundingClientRect()
    infodiv.css('top', ship_rect.bottom)
    infodiv.css('left', ship_rect.left)
    infodiv.show()
  })
  $('.stuff').on('mouseout', 'img', function() {
    infodiv.find('.universe').text("")
    infodiv.find('.faction').text("")
    infodiv.find('.name').text("")
    infodiv.find('.length').text("")
    infodiv.hide()
  })
})

function update_windowsize() {
  center_offset = [
    $(window).width()/2,
    $(window).height()/2
  ]
}

function initialize_ships() {
  resize();
}

function set_size(elm) {
  if(elm.target) { elm = elm.target }
  elm.width = elm.data.real_size[0]/m_per_px
  elm.height = elm.data.real_size[1]/m_per_px
  elm.style.left = ((elm.data.position[0] - elm.data.real_size[0]/2)/m_per_px + center_offset[0]) + "px"
  elm.style.top = ((elm.data.position[1] - elm.data.real_size[1]/2)/m_per_px + center_offset[1]) + "px"
  elm.style.display = ""

  clear_load(elm)
  if(!remaining_to_load) { $('.stuff').show() }
}

function clear_load(elm) {
  if(elm.target) { elm = elm.target }
  which_load = elm.loads.pop()
  if(which_load == current_load) {
    remaining_to_load--
  }
}

function resize() {
  var min_length = min_size_px*m_per_px
  $('.stuff').hide()
  remaining_to_load = 0
  var load_time = +new Date()
  current_load = load_time
  for(var i = ships.length-1; i >= 0; i--) {
    var ship = ships[i];
    var info = ship.info
    if(ship.real_size[0] > min_length) {
      var reinsert = false
      if(!ship.elm) {
        ship.elm = document.createElement('img')
        ship.elm.className = "thing"
        ship.elm.src = ship.path + '/' + ship.filename
        ship.elm.data = ship;
        if(!ship.elm.loads) { ship.elm.loads = [] }

        reinsert = true;
      }
      if(ship.elm.complete) {
        set_size(ship.elm)
      } else {
        remaining_to_load++
        ship.elm.loads.push(load_time)
        ship.elm.style.display="none"
        ship.elm.addEventListener('load', set_size)
        ship.elm.addEventListener('error', clear_load)
      }
      if(reinsert) { container.prepend(ship.elm) }
    } else {
      if(ship.elm) {
        container.get(0).removeChild(ship.elm);
        ship.elm = false;
      }
    }
  }
  if(remaining_to_load) {
    // Always load within a reasonable time
    setTimeout(function() { $('.stuff').show() }, load_timeout)
  } else {
    $('.stuff').show()
  }
  var text_elm = $('.status')
  text_elm.find('.m_per_px').text((new FancyNumber(m_per_px, 3)).getUnits());
  real_to_screen = m_per_px*1000*screen_px_per_mm
  if(real_to_screen < 1) {
    text_elm.find('.ratio').text('1:' + new FancyNumber(1/real_to_screen, 1).getHuman())
  } else {
    text_elm.find('.ratio').text(new FancyNumber(real_to_screen, 1).getHuman() + ':1')
  }
  if(!loaded) {
    text_elm.find('.loading').hide()
    text_elm.find('.loaded').show()
    loaded = true
  }
}
