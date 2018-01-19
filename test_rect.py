import rect_layout
import random
import tkinter as tk

def addrect():
  global layout
  width = random.randrange(10) + 20
  height = random.randrange(10) + 20
  layout.add_rect((width, height))

win = tk.Tk()
can = tk.Canvas(win)
can.pack()

btn = tk.Button(win, text="Add Rectangle", command=addrect)
btn.pack()

layout = rect_layout.Layout(400, can)

win.mainloop()

