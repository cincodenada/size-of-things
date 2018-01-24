from __future__ import print_function
from bs4 import BeautifulSoup
import glob
import re
import os
from shutil import copyfile
import yaml
import urllib

def dewhite(desc):
  desc = re.sub(r"\s+", " ", desc).strip()
  return desc

def generate_ship(ship):
  info = {}
  size_extract = re.match("(.*) (\w+): ([\d\.]+)(\w+)", ship['description'])
  if size_extract:
    info[size_extract.groups(2)] = size_extract.groups(3)
    info['Units'] = size_extract.groups(4)
    info['Name'] = size_extract.groups(1)

  if 'Name' in info and 'name' in ship and info['Name'] != ship['name']:
    info['AltName'] = ship['name']

  outship = {}
  outship['filename'] = os.path.basename(ship['src'])
  outship['info'] = info
  outship['source'] = "http://www.merzo.net/indexSD.html"
  outship['credit'] = "Jeff Russell"

  return outship

basedir = 'Starship Dimensions'

for page in glob.glob(os.path.join(basedir,'1 Pixel*.htm')):
  soup = BeautifulSoup(open(page, 'r'), "lxml")
  category = None
  ships = []
  incomplete_idx = None
  for td in soup.body.find_all('td'):
    if td.find('strong'):
      category = dewhite(td.find('strong').text)
    else:
      images = td.find_all('img')
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

          ships.append(ship)

      elif len(lines) == len(images)*2:
        # <font><img></font><font>Description</font>
        for (idx, img) in enumerate(images):
          ship = {}
          ship['group'] = category
          ship['src'] = img['src']
          ship['description'] = dewhite(lines[idx*2+1].text)
          ships.append(ship)
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

for ship in ships:
  groupname = ship['group'].replace(' Starships','')
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
  outfile.write(yaml.dump(generate_ship(ship)))
