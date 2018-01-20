import rect_layout
import random
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

def addrect():
  global layout
  height = random.randrange(10) + 20
  width = height + random.randrange(10) + 10
  layout.add_rect((width, height))

win = tk.Tk()
can = CartesianCanvas(win, width=500, height=500)
can.pack()

btn = tk.Button(win, text="Add Rectangle", command=addrect)
btn.pack()

layout = rect_layout.Layout(24, can)

win.mainloop()
