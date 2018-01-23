from bs4 import BeautifulSoup
import glob

for page in glob.glob("Starship Dimensions/1 Pixel*.htm"):
  soup = BeautifulSoup(open(page, 'r'), "lxml")
  category = None
  for td in soup.body.table.find_all('td'):
    if td.find('strong'):
      category = td.find('strong').text
    else:
      lines = td.find_all(['font','img'], recursive=False)
      if len(lines) == 2:
        img = lines[0]
        if img.img:
          img = img.img

        src = img['src']
        description = lines[1].text
      elif len(lines) == 1:
        src = lines[0].find('img')
        description = lines[0].text 

      print category
      print src
      print description
