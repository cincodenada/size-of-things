import rect_layout
import random
import tkinter as tk

win = tk.Tk()
can = tk.Canvas(win)
can.pack()

btn = tk.Button(win, text="Add Rectangle", command=addrect)
btn.pack()

layout = Layout(400, can)

win.mainloop()

def addrect():
  width = random.randrange(100)
  height = random.randrange(100)
  layout.add_rect((width, height))
