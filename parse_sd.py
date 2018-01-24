from __future__ import print_function
from bs4 import BeautifulSoup
import glob
import re

def dewhite(desc):
  desc = re.sub(r"\s+", " ", desc).strip()
  return desc

for page in glob.glob("Starship Dimensions/1 Pixel*.htm"):
  soup = BeautifulSoup(open(page, 'r'), "lxml")
  category = None
  ships = []
  for td in soup.body.find_all('td'):
    if td.find('strong'):
      category = dewhite(td.find('strong').text)
      print(category)
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
          ships.append(ship)
      elif len(lines) == 1:
        # <font>Description</font>
        pass
      elif len(lines) == len(images)*2:
        # <font><img></font><font>Description</font>
        for (idx, img) in enumerate(images):
          ship = {}
          ship['group'] = category
          ship['src'] = img['src']
          ship['description'] = dewhite(lines[idx*2+1].text)
          ships.append(ship)

  print("\n".join([str(s) for s in ships]))
