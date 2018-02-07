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
var origin = [0,0]
var center_offset = [0,0]
var screen_origin
var text_index = {}
var idx_pos = text_index
var jump_idx = 0

// TODO: Vary on window size?
var scalebar_target_width = 150

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

var TrieIndex = (function(pool, text_keys, min_chars) {
  function TrieIndex(pool, text_props, min_chars) {
    this.min_chars = min_chars
    this.last_query = ""
    this.matches = []
    this.new_matches = false
    this.trie = {}
    this.cur_node = this.trie
    this.cur_idx = 0

    // Build a friggin' trie, man
    for(var i = pool.length-1; i >= 0; i--) {
      words = []
      for(var k = 0; k < text_keys.length; k++) {
        if(pool[i].info[text_keys[k]]) {
          curtext = pool[i].info[text_keys[k]]
          curtext = curtext.toLowerCase().replace(/[^ a-z0-9]/g,"")
          words = words.concat(curtext.split(' '))
        }
      }
      for(var w = 0; w < words.length; w++) {
        var curword = words[w]
        var node = this.trie
        if(curword) {
          for(var l = 0; l < curword.length; l++) {
            if(!node[curword[l]]) {
              node[curword[l]] = {}
            }
            node = node[curword[l]]
          }
          if(!node['_idx']) {
            node['_idx'] = []
          }
          node['_idx'].push(i)
        }
      }
    }
  }

  TrieIndex.prototype.step = function(l) {
    // We're at a failed end
    if(this.cur_node === false) { return 0 }

    if(l == " ") {
      // New word, start back at the top
      // but keep our matches around
      this.cur_node = this.trie
    } else if(this.cur_node[l]) {
      this.cur_node = this.cur_node[l]
      if(this.matches.length == 0) {
        // If we don't have any matches,
        // add everything
        this.matches = this.get_vals(this.cur_node)
        this.dropped = []
        this.new_matches = !!this.matches.length
      } else {
        // Otherwise, only add things we've already seen
        // this is necessary for multi-word searches
        var new_matches = this.get_vals(this.cur_node)
        var prev_matches = this.matches
        this.matches = []
        this.dropped = []
        for(var i=0; i < prev_matches.length; i++) {
          var match_idx = prev_matches[i]
          if(new_matches.indexOf(match_idx) > -1) {
            this.matches.push(match_idx)
          } else {
            this.dropped.push(match_idx)
          }
        }
        // Disable further searches if we are at a dead end
        if(prev_matches.length && !this.matches.length) { this.cur_node = false }
      }
    } else {
      this.cur_node = false
      this.dropped = this.matches
      this.matches = []
    }
    return this.matches.length
  }

  TrieIndex.prototype.search = function(query) {
    this.new_matches = false

    if(query.length < this.min_chars) {
      this.dropped = this.matches
      this.matches = []
      return 0
    }

    if(query.slice(0,-1) == this.last_query) {
      // Keep going down the tree
      this.step(query.slice(-1))
    } else {
      // New query, reset and re-search
      var prev_matches = this.matches

      this.cur_node = this.trie
      this.matches = []
      for(var i=0; i < query.length; i++) {
        this.step(query[i])
      }
      this.dropped = prev_matches.filter(idx => this.matches.indexOf(idx) == -1)
    }

    this.last_query = query
    return this.matches.length
  }

  TrieIndex.prototype.get_vals = function(node) {
    results = {}
    for(l in node) {
      var new_results
      if(l == '_idx') {
        new_results = node[l]
      } else {
        new_results = this.get_vals(node[l])
      }

      // Add them to our object
      for(var i=0; i<new_results.length; i++) {
        results[new_results[i]] = 1
      }
    }
    return Object.keys(results)
  }

  TrieIndex.prototype.next_match = function() {
    if(this.matches.length) {
      this.cur_idx = (this.cur_idx + 1) % this.matches.length
      return this.matches[this.cur_idx]
    } else {
      return false
    }
  }

  return new TrieIndex(pool, text_keys, min_chars)
})

$(function() {
  container = $('.stuff')
  $.getJSON("ships.json?v=2").done(function(data) {
    ships = data;
    initialize_ships();
  })

  $('.px_mm').text(screen_px_per_mm.toFixed(2))

  $(window).on('resize', update_windowsize)
  update_windowsize()

  $(window).on('mousewheel', function(evt) {
    evt.preventDefault()
    m_per_px *= Math.pow(10, -evt.deltaY/zoomSlowFactor)
    clear_info()
    resize()
  })

  $(window).on('mousedown', function(evt) {
    if(evt.target.name == 'input') { return; }
    var last_loc = [evt.screenX, evt.screenY]
    $(window).on('mousemove', function(evt) {
      origin[0] += (evt.screenX - last_loc[0])*m_per_px
      origin[1] += (evt.screenY - last_loc[1])*m_per_px
      last_loc = [evt.screenX, evt.screenY]
      resize()
    })
  })
  $(window).on('mouseup', function(evt) {
    $(window).off('mousemove')
  })

  $('.stuff').on('mouseover', 'img', function() {
    clear_info()
    infodiv = $('.info')
    infodiv.find('.universe').text(this.data.info.Universe)
    infodiv.find('.faction').text(this.data.info.Faction)
    infodiv.find('.name').text(this.data.info.Name)
    infodiv.find('.size').text(this.data.info.Size)
    infodiv.find('.unit').text(this.data.info.Unit || 'm')
    infodiv.find('.credit').text(this.data.credit)
    infodiv.find('.credit').attr('href',this.data.source)
    ship_rect = this.getBoundingClientRect()
    infodiv.css('top', ship_rect.bottom)
    infodiv.css('left', ship_rect.left)
    infodiv.show()
  })

  var last_len = 0
  var last_sel = []
  $('.search input').on('keyup', function(evt) {
    if(evt.key=="Enter") {
      if((idx = text_index.next_match()) !== false) {
        found_ship = ships[idx]
        // Not sure why I have to negate these but whatevs
        origin[0] = -found_ship.position[0]
        origin[1] = -found_ship.position[1]
        // Use screen_origin for half screen size
        // Calculate m_per_px to fit on screen
        vert_zoom = found_ship.real_size[0]/screen_origin[0]
        horiz_zoom = found_ship.real_size[1]/screen_origin[1]
        m_per_px = Math.max(vert_zoom, horiz_zoom)
        resize()
      }
    }
    query = evt.target.value.toLowerCase()
    var num_results = text_index.search(query)
    $('.search .count').text(num_results)

    // Deselect dropped ships
    $.each(text_index.dropped, function(x, idx) {
      if(ships[idx].elm) {
        $(ships[idx].elm).removeClass('highlight')
      }
    })

    // Add new ones if applicable
    if(text_index.new_matches) {
      $.each(text_index.matches, function(x, idx) {
        if(ships[idx].elm) {
          $(ships[idx].elm).addClass('highlight')
        }
      })
    }
  })
})

function clear_info() {
    infodiv = $('.info')
    infodiv.find('.universe').text("")
    infodiv.find('.faction').text("")
    infodiv.find('.name').text("")
    infodiv.find('.size').text("")
    infodiv.find('.unit').text("")
    infodiv.find('.length').text("")
    infodiv.find('.credit').text("")
    infodiv.find('.credit').attr('href',"#")
    infodiv.hide()
}

function update_windowsize() {
  screen_origin = [
    $(window).width()/2,
    $(window).height()/2
  ]
}

function initialize_ships() {
  text_index = TrieIndex(ships, ['Name','Faction','Universe'], 4)
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
  center_offset[0] = screen_origin[0] + origin[0]/m_per_px
  center_offset[1] = screen_origin[1] + origin[1]/m_per_px
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

  update_status()
  update_scalebar()
}

function update_status() {
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

function update_scalebar() {
  var scalebar = $('.scalebar')
  var basewidth = scalebar_target_width*m_per_px
  var divfact = Math.pow(10, Math.floor(Math.log10(basewidth)))
  var scalewidth = Math.round(basewidth/divfact)*divfact
  scalebar.find('.bar').css('width', scalewidth/m_per_px)
  scalebar.find('.label').text(FancyNumber(scalewidth).getUnits())
}
