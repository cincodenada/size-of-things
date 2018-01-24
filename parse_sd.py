from __future__ import print_function
from bs4 import BeautifulSoup
import glob
import re
import os
from shutil import copyfile
import yaml
import urllib

size_extracts = [
  r"(?P<name>.*) (?P<dimension>\w+): (?P<size>[\d\.]+)(?P<unit>\w+)",
  r"(?P<name>.*) (?P<size>[\d\.]+)(?P<unit>\w+)(?: (?P<dimension>\w+))?",
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
}

size_types = ['Size','Height','Width','Length','Diameter']

def dewhite(desc):
  desc = re.sub(r"\s+", " ", desc).strip()
  return desc

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
    parts = re.match(r'(?P<dimension>[\d\.]+) ?(?P<unit>\w+)(?: \((?P<note>.*)\))?', ship[cur_dim])
    if(parts):
      info[cur_dim] = float(parts.group('dimension'))
      info['Unit'] = parts.group('unit')
      if parts.group('note'):
        info['Size Notes'] = parts.group('note')
    else:
      info[cur_dim] = ship[cur_dim]
    if 'description' in ship:
      info['Description'] = ship['description']
  elif 'description' in ship:
    info['Description'] = ship['description']
    if ship_info:
      info[str(ship_info.group('dimension'))] = float(ship_info.group('size'))
      info['Units'] = ship_info.group('unit')
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
      print(images)
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
