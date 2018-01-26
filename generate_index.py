# -*- coding: utf-8 -*-
import json
import yaml
import os
import math
import rect_layout
from PIL import Image
from progress.bar import Bar

dimension_axes = {
  'Size': 0,
  'Length': 0,
  'Width': 0,
  'Diameter': 0,
  'Wingspan': 1,
  'Height': 1,
}

unit_conversions = {
  'ly': 946073e10,
  'm': 1,
  'km': 1000,
  'mi': 1609.344,
  'ft': 0.3048,
  'cm': 0.01,
  'mm': 0.001,
  'um': 1e-6,
  'µm': 1e-6,
  'nm': 1e-9,
  'Å': 1e-10,
  'A': 1e-10,
}

def get_parts(path):
  part_values = {}
  keys = ['Universe','Faction']
  keys.reverse()

  remainder = path
  parts = []
  while remainder:
    (remainder, part) = os.path.split(remainder)
    parts.append(part)

  parts.pop() # Strip off "images"
  while len(parts) and len(keys):
    part_values[keys.pop()] = parts.pop()

  return part_values

def set_default(d, k, defaults):
  combined = {}
  combined.update(defaults)
  combined.update(d[k])
  d[k] = combined

def gather_yaml(path):
  ships = []
  extra_info = get_parts(path)
  for e in os.listdir(path):
    fullpath = os.path.join(path, e)
    if os.path.isfile(fullpath):
      if e.endswith('.yaml'):
        for ship in yaml.load_all(open(fullpath, 'r')):
          try:
            set_default(ship, 'info', extra_info)
            ship['path'] = path

            # Get image width/height
            im = Image.open(os.path.join(path, ship['filename']))
            ship['image_size'] = im.size

            # Initialize scale information
            m = px = unit = m_per_px = None

            # First, check for explicit x_per_px
            loaded_explicit = False
            for pre in unit_conversions.keys():
              key = pre + '_per_px'
              if key in ship:
                m_per_px = ship[key]
                unit = pre
                if isinstance(m_per_px, str):
                  (m, px) = m_per_px.split('/')
                break

            # Otherwise, load from info
            if not m_per_px:
              # Look for size keys
              for (dim, axis) in dimension_axes.items():
                if dim in ship['info']:
                  m = ship['info'][dim]
                  ship['info']['Size'] = m
                  ship['info']['Dimension'] = dim
                  # Load px from correct image axis
                  px = im.size[axis]
                  break

              # Look for a unit as well
              if ('Unit' in ship['info']) and ship['info']['Unit']:
                unit = ship['info']['Unit']

            # At this point we should have something
            if m and px:
              m_per_px = float(m)/float(px)
              if unit and unit != 'm':
                print("Converting {} to m".format(unit))
                m_per_px = m_per_px*unit_conversions[unit]

            # Assign to ship
            if m_per_px:
              ship['m_per_px'] = m_per_px
              ship['real_size'] = [
                d*ship['m_per_px']
                for d in ship['image_size']
              ]
            else:
              # If we don't have things by now throw a fit
              raise ArithmeticError("Couldn't determine m/px!")

            ships.append(ship)
          except ValueError as e:
            print("Failed to load ship from {}:\n{}\n{}".format(fullpath, str(e), str(ship)))
          except IOError as e:
            print("Failed to load image from {}:\n{}\n{}".format(fullpath, str(e), str(ship)))
          except ArithmeticError as e:
            print("Failed to load ship from {}:\n{}\n{}".format(fullpath, str(e), str(ship)))

    elif os.path.isdir(fullpath):
      ships += gather_yaml(fullpath)

  return ships

def sort_ship(ship):
  size_order = None
  if 'real_size' in ship:
    size_order = ship['real_size'][0]*ship['real_size'][1]
  else:
    size_order = 0

  return (size_order, ship['info'].get('Universe'), ship['info'].get('Faction'))

ships = gather_yaml('images')
ships.sort(key = sort_ship)

layout = rect_layout.Layout(24)
bar = Bar('Placing ships', max=len(ships))
for s in ships:
  if 'm_per_px' not in s:
    print("Skipping {}, no size info!".format(s['info']['Name']))
  if 'image_size' not in s:
    print("Skipping {}, no image info!".format(s['info']['Name']))

  rect = layout.add_rect([
    px * s['m_per_px']
    for px in s['image_size']
  ])

  s['position'] = rect.center
  bar.next()

json.dump(ships, open('ships.json', 'w'))
