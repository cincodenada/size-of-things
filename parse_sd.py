# -*- coding: utf-8 -*-
from __future__ import print_function
from bs4 import BeautifulSoup
import glob
import re
import os
from shutil import copyfile
import yaml
try:
  from urllib import unquote
except ImportError:
  from urllib.parse import unquote

mpp_map = {
  "1 cm per pixel.htm": 1.0/100,
  "10 Pixels per meter.htm": 1.0/10,
  "1 Pixel per meter.htm": 1,
  "2 meters per pixel.htm": 2,
  "10 meters per pixel.htm": 10,
  "100 Pixels per meter.htm": 100,
  "2000 Meters per Pixel.htm": 2000,
  "FIVE HUNDRED THOUSAND KILOMETERS per Pixel!!.htm": 500000
}

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
  'high': 'Height',
  'length': 'Length',
  'width': 'Width',
  'diameter': 'Diameter',
  'wingspan': 'Wingspan',
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

unit_match = "|".join([re.escape(k) for k in units.keys()])
field_match = "|".join([re.escape(k) for k in field_map.keys()])
size_extracts = [
  # Name Length: 123.45m or 123.45 m
  r"(?P<name>.*?)[,]? (?P<dimension>" + field_match + "): (?P<size>[\d\., ]*\d) ?(?P<unit>" + unit_match + ")(?:,? ?\(?(?P<note>[^\(\)]*)\)?)?",
  # Name Length note: 123.45m or 123.45 m
  r"(?P<name>.*?)[,]? (?P<dimension>" + field_match + ")(?:,? ?\(?(?P<note>[^\(\)]*)\)?)?: (?P<size>[\d\., ]*\d) ?(?P<unit>" + unit_match + ")",
  # Name 123.45m diameter
  r"(?P<name>.*?)[,]? (?:\(?(?P<note>approximately)\)? )?(?P<size>[\d\., ]*\d) ?(?P<unit>" + unit_match + ")(?: (?P<dimension>" + field_match + "))?",
]
print(size_extracts)



unit_map = {}
for (unit, maps) in units.items():
  maps.append(unit)
  for name in maps:
    unit_map[name] = unit
    unit_map[name + 's'] = unit

def dewhite(desc):
  desc = re.sub(r"\s+", " ", desc, flags=re.UNICODE).strip()
  return desc

def getnum(numstr):
  return float(numstr.replace(',','').replace(' ',''))

def generate_ship(ship):
  info = {}
  
  for regex in size_extracts:
    ship_info = re.match(regex, ship['description'], flags=re.IGNORECASE)
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
      dim = getnum(parts.group('size'))
      if dim:
        info[cur_dim] = dim
      info['Unit'] = parts.group('unit')
      if parts.group('note'):
        note = parts.group('note').strip()
        if note[0] == '(' and note[-1] == ')':
          note = note[1:-1].strip()
        info['Size Notes'] = note
    else:
      if ship[cur_dim]:
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
        dim = getnum(ship_info.group('size'))
        if dim:
          info[dim_key] = dim

      if ship_info.group('note'):
        info['Size Note'] = ship_info.group('note')

      if ship_info.group('name'):
        if 'Name' in info and info['Name'] != ship['name']:
          info['AltName'] = ship_info.group('name')
        else:
          info['Name'] = ship_info.group('name')

  outship = {}
  outship['filename'] = os.path.basename(ship['src'])
  outship['info'] = info
  outship['source'] = "http://www.merzo.net/indexSD.html"
  outship['credit'] = "Jeff Russell"

  if 'Unit' not in info:
    outship['m_per_px'] = ship['default_mpp']

  return outship

basedir = 'Starship Dimensions'

def fill_pending():
  global ships
  global pending_ships
  global pending_idx

  global pending_text
  global pending_field
  print("Filling pending ships...")
  if pending_ships and pending_idx < len(pending_ships):
    print(pending_ships)
    print("Starting at {}, filling {} with {}".format(pending_idx, pending_field, pending_text))
    for idx in range(pending_idx, len(pending_ships)):
      pending_ships[idx][field_map[pending_field]] = pending_text
    pending_field = "_default_"
    pending_text = ""
  else:
    print("No orphans, yay!")

def finish_pending():
  global ships
  global pending_ships
  global pending_idx

  if pending_ships:
    fill_pending()
    print("Merging pending ships...")
    ships += pending_ships
    pending_ships = []
    pending_idx = 0

ships = []
pending_ships = []
pending_idx = 0

pending_text = ""
pending_field = ""

last_found = ""

for page in glob.glob(os.path.join(basedir,'*.htm')):
  default_mpp = mpp_map[os.path.basename(page)]
  soup = BeautifulSoup(open(page, 'r'), "lxml")
  category = None
  for td in soup.body.find_all(['td','p']):
    print("===\nLoaded {} ships, {} pending...\n===".format(len(ships), len(pending_ships)))
    if td.name == 'p' and ((not td.find('img')) or td.parent.name == 'td'):
      continue

    if td.find('strong'):
      category = dewhite(td.find('strong').text)
    else:
      images = td.select('> img, > font > img, > p > font > img, > p > img')
      lines = td.find_all(['font','img', 'a'], recursive=False)
      for p in td.find_all('p', recursive = False):
        if p.find('img') and not p.find('font'):
          print("Converting <p>...")
          print(p)
          p.name = 'font'
          lines.append(p)
        else:
          children = p.find_all(['font','img', 'a'], recursive=False)
          if children:
            print("Unwrapping <p>...")
            print(p)
            lines += children


      if len(lines) == 0:
        continue

      print("{} im, {} ln".format(len(images), len(lines)))
      if len(images) == len(lines):
        # <img><font>Description</font>
        # <font><img> Description</font>
        # <td> <font><img></font> x N </td><td> <font>Description</font> </td>
        if last_found != 'image':
          print("images == lines")
          print(lines)
          finish_pending()

        for img in images:
          ship = {'default_mpp': default_mpp}
          ship['group'] = category
          ship['src'] = img['src']
          if img.find_next_sibling('table'):
            # Don't pull in table descriptions, we'll get those later
            ship['description'] = ""
          else:
            ship['description'] = dewhite(img.parent.text)
          if 'alt' in img:
            ship['name'] = img['alt']

          if not ship['description']:
            print(img)
            print("Adding ship to pending...")
            pending_ships.append(ship)
            pending_idx = len(pending_ships)
            pending_field = "_default_"
            pending_text = ""
          else:
            ships.append(ship)

        last_found = 'image'
      elif len(lines) == len(images)*2:
        # <font><img></font><font>Description</font>
        if last_found != 'image':
          print("lines == images*2")
          print(lines)
          finish_pending()

        for (idx, img) in enumerate(images):
          ship = {'default_mpp': default_mpp}
          ship['group'] = category
          ship['src'] = img['src']
          ship['description'] = dewhite(lines[idx*2+1].text)
          ships.append(ship)

        last_found = 'image'
      elif len(lines) >= 1 and len(images) == 0:
        line = lines[0]
        if line.find('b'):
          fill_pending()

          pending_field = line.find('b').text.replace(":","")
          pending_field = re.sub(" \(.*\)$","",pending_field)
          pending_field = re.sub("\s+"," ",pending_field)
          print("New heading: " + pending_field)

          pending_idx = 0
        else:
          if last_found == 'image':
            print("lines >=1 images = 0")
            print(lines)
            fill_pending()
            pending_idx = 0
          print(lines)
          print("Adding {} to {}...".format(pending_field, pending_idx))
          pending_text = dewhite(' '.join([l.text for l in lines]))
          pending_ships[pending_idx][field_map[pending_field]] = pending_text
          pending_idx+=1

        last_found = 'text'
      elif len(images)*2 < len(lines):
        # <font>Description</font>
        # But we might have extra images
        dangling_ship = False
        cur_text = ""
        for l in lines:
          if l.find('img'):
            # Finish up any previous bits
            if cur_text:
              if dangling_ship:
                ship['description'] = dewhite(cur_text)
                ships.append(ship)
              elif pending_ships:
                pending_ships[pending_idx]['description'] = dewhite(cur_text)
                pending_idx += 1
              cur_text = ""

            ship = {'default_mpp': default_mpp}
            ship['group'] = category
            ship['src'] = l.find('img')['src']
            if 'alt' in img:
              ship['name'] = img['alt']
            dangling_ship = True
          else:
            cur_text += l.text

        if cur_text:
          if dangling_ship:
            ship['description'] = dewhite(cur_text)
            ships.append(ship)
          elif pending_ships:
            pending_ships[pending_idx]['description'] = dewhite(cur_text)
            pending_idx += 1
          cur_text = ""

        last_found = 'text'

      elif len(images) > len(lines):
        # <font><img><img>Description</font>
        for img in images:
          ship = {'default_mpp': default_mpp}
          ship['group'] = category
          ship['src'] = img['src']
          if 'alt' in img:
            ship['name'] = img['alt']
          pending_ships.append(ship)

        pending_text = dewhite(lines[0].text)
        pending_field = "_default_"
        finish_pending()

  finish_pending()

config = yaml.load(open('sdparse_config.yaml', 'r'))

# Deduplicate/filter
max_res = {}
filtered = {}
for (idx, s) in enumerate(ships):
  imgname = os.path.basename(s['src'])
  if os.path.basename(s['src']) in config['ignore_images']:
    continue

  mpp = s['default_mpp']
  bits = re.match(
    '(\d+)([kc]?)([mp])([mp])([mp])(.*).gif',
    imgname.lower()
  )
  if bits:
    (num, prefix, numer, _, denom, ship) = bits.groups()

    if ship in config['ignore_images']:
      print("Skipping " + ship)
      continue

    if ship not in max_res or max_res[ship] > mpp:
      max_res[ship] = mpp
      filtered[ship] = s
  else:
    print(imgname)
    filtered[imgname] = s

ships = list(filtered.values())
# Sort by filename to guarantee consistent order
ships.sort(key=lambda x: x['src'])
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

  filesrc = unquote(ship['src'])

  copyfile(
    os.path.join(basedir, filesrc),
    os.path.join(groupdir,os.path.basename(filesrc))
  )
  outfile = open(os.path.join(groupdir,'sd_gen.yaml'), 'a')
  outfile.write('---' + os.linesep)
  outfile.write(yaml.safe_dump(generate_ship(ship), default_flow_style=False, allow_unicode=True))
