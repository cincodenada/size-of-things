import rect_layout
import random
import tkinter as tk

scale = 1
growth_rate = 1.05

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

def addrect():
  global layout
  global scale
  scale *= growth_rate
  height = (random.randrange(10) + 20)*scale
  width = height + (random.randrange(10) + 10)*scale
  layout.add_rect((width, height))

win = tk.Tk()
can = CartesianCanvas(win, width=600, height=400)
can.pack()

btn = tk.Button(win, text="Add Rectangle", command=addrect)
btn.pack()

layout = rect_layout.Layout(24, can)

for i in range(15):
  #addrect()
  pass

win.mainloop()
