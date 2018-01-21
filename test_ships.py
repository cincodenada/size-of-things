import rect_layout
import json
import tkinter as tk

class CartesianCanvas(tk.Canvas):
  def __init__(self, master=None, cnf={}, **kw):
    cnf['scrollregion'] = (
      -kw['width']/2,
      -kw['height']/2,
      kw['width']/2,
      kw['height']/2
    )
    super(CartesianCanvas, self).__init__(master, cnf, **kw)
  def _create(self, itemType, args, kw): # Args: (val, val, ..., cnf={})
    # transform x1 y1 x2 y2
    args = list(args)
    args[1] = -args[1]
    args[3] = -args[3]
    super(CartesianCanvas, self)._create(itemType, args, kw)

ships = json.load(open('ships.json', 'r'))
cur_ship = 0
scale = 50

win = tk.Tk()
can = CartesianCanvas(win, width=1200, height=800)
can.pack()

layout = rect_layout.Layout(24, can)

def addrect():
  global layout
  global ships
  global cur_ship
  global scale
  print(ships[cur_ship])
  layout.add_rect([
    p*ships[cur_ship]['m_per_px']/scale
    for p in ships[cur_ship]['image_size']
  ])
  cur_ship+=1


btn = tk.Button(win, text="Add Rectangle", command=addrect)
btn.pack()

win.mainloop()
