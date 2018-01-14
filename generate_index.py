import json
import yaml
import os

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
  defaults.update(d[k])
  d[k] = defaults

def gather_yaml(path):
  ships = []
  extra_info = get_parts(path)
  for e in os.listdir(path):
    fullpath = os.path.join(path, e)
    if os.path.isfile(fullpath):
      if e.endswith('.yaml'):
        for ship in yaml.load_all(open(fullpath, 'r')):
          set_default(ship, 'info', extra_info)
          ship['path'] = path
          ships.append(ship)
    elif os.path.isdir(fullpath):
      ships += gather_yaml(fullpath)

  return ships

json.dump(gather_yaml('images'), open('ships.json', 'w'))
