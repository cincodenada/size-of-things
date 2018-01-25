# -*- coding: utf-8 -*-
from __future__ import print_function
from bs4 import BeautifulSoup
import glob
import re
import os
from shutil import copyfile
import yaml
import urllib

size_extracts = [
  # Name Length: 123.45m or 123.45 m
  r"(?P<name>.*) (?P<dimension>\w+): (?P<size>[\d\., ]*\d) ?(?P<unit>\w+)",
  # Name 123.45m diameter
  r"(?P<name>.*) (?P<size>[\d\., ]*\d) ?(?P<unit>\w+)(?: (?P<dimension>\w+))?",
]

field_map = {
  '_default_': 'description',
  'Source': 'group',
  'Name': 'name',
  'Dimension': 'Size',
  'SHIP NAME/TYPE': 'name',
  'HEIGHT': 'Height',
  'LENGTH': 'Length',
  'WIDTH': 'Width',
  'DIAMETER': 'Diameter',
  'BUILDER/COMMENTS': 'description',
  'SOURCE': 'group',
  'long': 'Length',
  'height': 'Height',
  'length': 'Length',
  'width': 'Width',
  'diameter': 'Diameter',
}

size_types = ['Size','Height','Width','Length','Diameter','Wingspan']

units = {
  'ly': ['lightyear'],
  'm': ['meter'],
  'km': ['kilometer'],
  'cm': ['centimeter'],
  'mm': ['millimeter'],
  'µm': ['micrometer','um'],
  'nm': ['nanometer'],
  'Å': ['angstrom','A'],
  'mi': ['mile'],
  'ft': ['foot','feet'],
}

unit_map = {}
for (unit, maps) in units.items():
  maps.append(unit)
  for name in maps:
    unit_map[name] = unit
    unit_map[name + 's'] = unit

def dewhite(desc):
  desc = re.sub(r"\s+", " ", desc).strip()
  return desc

def getnum(numstr):
  return float(numstr.replace(',','').replace(' ',''))

def generate_ship(ship):
  info = {}
  
  for regex in size_extracts:
    ship_info = re.match(regex, ship['description'])
    if ship_info:
      break
  
  if 'name' in ship:
    info['Name'] = ship['name']

  has_size = False
  cur_dim = None
  for dim in size_types:
    if dim in ship:
      cur_dim = dim
      has_size = True
      break

  if has_size:
    parts = re.match(r'(?P<size>[\d\., ]*\d) ?(?P<unit>\w+)(?:[,\.]\s+)?(?P<note>[^,\.].*)?', ship[cur_dim])
    if(parts):
      print(ship[cur_dim])
      print(parts.groups())
      info[cur_dim] = getnum(parts.group('size'))
      info['Unit'] = parts.group('unit')
      if parts.group('note'):
        note = parts.group('note').strip()
        if note[0] == '(' and note[-1] == ')':
          note = note[1:-1].strip()
        info['Size Notes'] = note
    else:
      info[cur_dim] = ship[cur_dim]
    if 'description' in ship:
      info['Description'] = ship['description']
  elif 'description' in ship:
    info['Description'] = ship['description']
    if ship_info:
      dim = ship_info.group('dimension')
      if dim and ((dim in field_map) or (dim in size_types)):
        if dim in field_map:
          dim_key = field_map[dim]
        else:
          dim_key = dim
      else:
        dim_key = 'Size'

      unit = ship_info.group('unit')
      if unit and (unit in unit_map):
        info['Unit'] = unit_map[unit]
        info[dim_key] = getnum(ship_info.group('size'))

      if ship_info.group('name') and 'Name' in info and info['Name'] != ship['name']:
        info['AltName'] = ship_info.group('name')

  outship = {}
  outship['filename'] = os.path.basename(ship['src'])
  outship['info'] = info
  outship['source'] = "http://www.merzo.net/indexSD.html"
  outship['credit'] = "Jeff Russell"

  return outship

basedir = 'Starship Dimensions'

ships = []
for page in glob.glob(os.path.join(basedir,'*.htm')):
  soup = BeautifulSoup(open(page, 'r'), "lxml")
  category = None
  incomplete_idx = None
  field_start = None
  for td in soup.body.find_all(['td','p']):
    if td.name == 'p' and not td.find('img'):
      continue

    if td.find('strong'):
      category = dewhite(td.find('strong').text)
    else:
      images = td.select('> img, > font > img')
      lines = td.find_all(['font','img'], recursive=False)

      if len(images) == len(lines):
        # <img><font>Description</font>
        # <font><img> Description</font>
        # <td> <font><img></font> x N </td><td> <font>Description</font> </td>
        for img in images:
          ship = {}
          ship['group'] = category
          ship['src'] = img['src']
          ship['description'] = dewhite(img.parent.text)
          if 'alt' in img:
            ship['name'] = img['alt']

          if not ship['description'] and incomplete_idx is None:
            incomplete_idx = len(ships)
            field_idx = incomplete_idx
            cur_field = '_default_'

          ships.append(ship)

      elif len(lines) == len(images)*2:
        # <font><img></font><font>Description</font>
        for (idx, img) in enumerate(images):
          ship = {}
          ship['group'] = category
          ship['src'] = img['src']
          ship['description'] = dewhite(lines[idx*2+1].text)
          ships.append(ship)
      elif len(lines) == 1 and len(images) == 0:
        line = lines[0]
        if line.find('b'):
          cur_field = line.find('b').text.replace(":","")
          cur_field = re.sub(" \(.*\)$","",cur_field)
          cur_field = re.sub("\s+"," ",cur_field)
          if incomplete_idx is not None:
            field_start = incomplete_idx
            incomplete_idx = None
          field_idx = field_start
        else:
          ships[field_idx][field_map[cur_field]] = dewhite(line.text)
          field_idx += 1
      elif len(images)*2 < len(lines):
        # <font>Description</font>
        dangling_ship = False
        for l in lines:
          if l.find('img'):
            ship = {}
            ship['group'] = category
            ship['src'] = l.find('img')['src']
            if 'alt' in img:
              ship['name'] = img['alt']
            dangling_ship = True
          else:
            description = dewhite(l.text)
            if dangling_ship:
              ship['description'] = description
              ships.append(ship)
            elif incomplete_idx is not None:
              ships[incomplete_idx]['description'] = dewhite(lines[0].text)
              incomplete_idx += 1
              if incomplete_idx == len(ships):
                incomplete_idx = None

# Deduplicate
max_res = {}
filtered = {}
for (idx, s) in enumerate(ships):
  imgname = os.path.basename(s['src']).lower()
  bits = re.match(
    '(\d+)([kc]?)([mp])([mp])([mp])(.*).gif',
    imgname 
  )
  if(bits):
    (num, prefix, numer, _, denom, ship) = bits.groups()
    num = float(num)
    if(prefix == 'k'):
      num *= 1000
    elif(prefix == 'c'):
      num /= 100

    if(numer == 'p'):
      ppm = num
    else:
      ppm = 1/num

    if ship not in max_res or max_res[ship] < ppm:
      max_res[ship] = ppm
      filtered[ship] = s
  else:
    print(imgname)
    filtered[imgname] = s

ships = filtered.values()
print(len(ships))
for ship in ships:
  try:
    groupname = ship['group'].replace(' Starships','')
  except AttributeError:
    groupname = 'Other'
  if len(groupname) > 50:
    groupname = ' '.join(groupname.split(' ')[0:2])

  groupdir = os.path.join('images',groupname.replace("/","_"))
  try:
    os.mkdir(groupdir)
  except OSError:
    # Assume path exists
    pass

  filesrc = urllib.unquote(ship['src'])

  copyfile(
    os.path.join(basedir, filesrc),
    os.path.join(groupdir,os.path.basename(filesrc))
  )
  outfile = open(os.path.join(groupdir,'info.yaml'), 'a')
  outfile.write('---' + os.linesep)
  outfile.write(yaml.safe_dump(generate_ship(ship), default_flow_style=False))
