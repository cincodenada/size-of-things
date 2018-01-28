# -*- coding: utf-8 -*-
import math
from copy import copy
import sys
import logging
from sortedcontainers import SortedListWithKey
math.tau = math.pi*2
default_precision = 2

logger = logging.getLogger()

def frange(end, jump):
  x = 0
  while x < end:
    yield x
    x += jump

# Adapted from http://www.floating-point-gui.de/errors/comparison/
def nearlyEqual(a, b, epsilon = 0.001):
  absA = abs(a);
  absB = abs(b);
  diff = abs(a - b);

  if (a == b): # shortcut, handles infinities
    return True;
  elif (a == 0 or b == 0 or diff < sys.float_info.min):
    # a or b is zero or both are extremely close to it
    # relative error is less meaningful here
    return diff < (epsilon * sys.float_info.min);
  else: # use relative error
    return diff / min((absA + absB), sys.float_info.max) < epsilon;

def nearlyCmp(a, op, b, epsilon = 0.001):
  if op == '>':
    return ((a > b) or (nearlyEqual(a, b)))
  elif op == '<':
    return ((a < b) or (nearlyEqual(a, b)))
  elif op == '==':
    return nearlyEqual(a, b)

class Rayish:
  def __init__(self, angle_or_end, origin = (0,0), length=1, precision = default_precision):
    self.p = precision
    self.origin = origin
    try:
      self.end = angle_or_end
      self.angle = self.clamp_range(
        math.atan2(
          self.end[1] - self.origin[1],
          self.end[0] - self.origin[0]
        )
      )
    except TypeError:
      self.angle = angle_or_end
      self.end = (
        self.origin[0] + math.cos(self.angle)*length,
        self.origin[1] + math.sin(self.angle)*length
      )

    self._length = None

  @staticmethod
  def as_pi(val):
    try:
      return [Rayish.as_pi(v) for v in val]
    except TypeError:
      return "{}π".format(round(val/math.pi, 3))

  @staticmethod
  def clamp_range(val, range=(0,2*math.pi)):
    if not (range[1] - range[0]) == 2*math.pi:
      raise ValueError("Range must span 2*pi")

    while val < range[0]:
      val += 2*math.pi
    while val > range[1]:
      val -= 2*math.pi

    return val

  def __str__(self):
    return "Rayish length {} from {} to {} (angle {})".format(
      self.length(), self.origin, self.end, self.as_pi(self.angle)
    )

  def draw(self, canvas, tags = None, color="red"):
    if(canvas):
      elms = []
      oval_size = 5
      elms.append(canvas.create_line(
        self.origin[0], self.origin[1],
        self.end[0], self.end[1],
        dash=(1,2),
        tags=tags
      ))
      elms.append(canvas.create_oval(
        self.end[0]-oval_size/2, self.end[1]-oval_size/2,
        self.end[0]+oval_size/2, self.end[1]+oval_size/2,
        fill=color, tags=tags
      ))
      return elms
    return None

  def distance(self, angle):
    phi = math.abs(angle.angle - self.angle) % 360
    distance = 360 - phi if phi > 180 else phi
    return distance

  def length(self):
    if not self._length:
      self._length = math.sqrt(
        math.pow((self.origin[0] - self.end[0]), 2) +
        math.pow((self.origin[1] - self.end[1]), 2)
      )

    return self._length

  def intersects_segment(self, a, b):
    xdiff = (a[0] - b[0], self.origin[0] - self.end[0])
    ydiff = (a[1] - b[1], self.origin[1] - self.end[1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
      return None

    d = (det(a, b), det(self.origin, self.end))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div

    x_range = [
      min(a[0],b[0]),
      max(a[0],b[0])
    ]
    y_range = [
      min(a[1],b[1]),
      max(a[1],b[1])
    ]

    if (nearlyCmp(x, '>', x_range[0]) and
        nearlyCmp(x, '<', x_range[1]) and
        nearlyCmp(y, '>', y_range[0]) and
        nearlyCmp(y, '<', y_range[1])
      ):
      return (x, y)
    else:
      return None

class Rect:
  def __init__(self, size, center = (0,0), precision = default_precision):
    self.p = precision
    self.size = size
    self.move_to(center)

  def __str__(self):
    return "Rectangle: tldr {}/{}/{}/{}".format(
      *[round(v, 3) for v in (self.top, self.left, self.bottom, self.right)]
    )

  def move(self, dist):
    logger.debug("Moving {} from {} ".format(dist, self.center))
    self.move_to((
      self.center[0] + dist[0],
      self.center[1] + dist[1]
    ))

  def move_to(self, center):
    self.center = center
    self.min_radius_ = None
    self.max_radius_ = None
    logger.debug("New center: {}".format(self.center))

    self.left = self.center[0] - self.size[0]/2
    self.right = self.center[0] + self.size[0]/2
    self.bottom = self.center[1] - self.size[1]/2
    self.top = self.center[1] + self.size[1]/2

  def corners(self):
    return [
      (self.right, self.top),
      (self.left, self.top),
      (self.left, self.bottom),
      (self.right, self.bottom)
    ]

  def corner_rays(self, origin = (0,0)):
    return [Rayish(c, origin) for c in self.corners()]

  def corner_angles(self, origin = (0,0)):
    return [cr.angle for cr in self.corner_rays(origin)]

  def min_radius(self):
    if not self.min_radius_:
      self.min_radius_ = self.calc_min_radius()

    return self.min_radius_

  def calc_min_radius(self):
    straddle_v = (self.left < 0 and self.right > 0)
    straddle_h = (self.bottom < 0 and self.top > 0)
    if straddle_h and straddle_v:
      return min(self.top, self.right)
    if straddle_v:
      if self.top > 0:
        return self.bottom
      else:
        return -self.top
    if straddle_h:
      if self.right > 0:
        return self.left
      else:
        return -self.right

    return min([r.length() for r in self.corner_rays()])

  def max_radius(self):
    if not self.max_radius_:
      self.max_radius_ = self.calc_max_radius()

    return self.max_radius_

  def calc_max_radius(self):
    return max([r.length() for r in self.corner_rays()])

  def corner_distances(self, angle, origin=(0,0)):
    corner_angles = self.corner_angles()
    distances = [ca - angle for ca in corner_angles]
    logger.debug(Rayish.as_pi(distances))
    distances = [Rayish.clamp_range(d, [-math.pi, math.pi]) for d in distances]
    return distances

  def intersects_angle(self, angle, origin = (0,0)):
    distances = self.corner_angles(origin)
    return (min(distances) < 0 and max(distances) > 0)

  def outer_radius(self, angle):
    logger.debug(self)

    # We can ignore the closest corner
    # Line will then be between two of the remaining points
    ignore_corner = self.get_ignore(angle)
    middle_corner = (ignore_corner + 2) % 4
    distances = self.corner_distances(angle)
    dist_middle = distances[middle_corner]

    logger.debug("Finding sides for angle {}, ignoring corner {}, middle corner {} ({})".format(
      Rayish.as_pi(angle), ignore_corner, middle_corner, Rayish.as_pi(dist_middle)
    ))

    # Ensure our corner is even in the quadrant
    corner_angles = self.corner_angles()
    if (corner_angles[middle_corner] < middle_corner*math.pi/2 or
        corner_angles[middle_corner] > (middle_corner+1)*math.pi/2):
      return None

    logger.debug(Rayish.as_pi(distances))
    if not min(distances) < 0 and max(distances) > 0:
      return None

    ray = Rayish(angle)

    corners = self.corners()
    if(dist_middle < 0):
      point = ray.intersects_segment(corners[(middle_corner + 1) % 4], corners[middle_corner])
      side = (middle_corner + 1) % 4
    else:
      point = ray.intersects_segment(corners[(middle_corner - 1) % 4], corners[middle_corner])
      side = middle_corner

    if not point:
      return None

    ray = Rayish(point)
    ray.side = side
    logger.debug(ray)
    return ray

  def get_ignore(self, angle):
    quadrant = math.floor(angle/(math.pi/2))
    return int((quadrant + 2) % 4)

  def intersects(self, rect):
    # standard cartesian
    # "below" is <
    # "above" is >
    #logger.debug(rect)
    #logger.debug(self)
    # TODO: Use nearlyCmp here?
    # Margins might make this unnecessary, thank goodness
    v = False
    if rect.top < self.top:
      if rect.top > self.bottom:
        v = True
    else:
      if rect.bottom < self.top:
        v = True

    h = False
    if rect.left > self.left:
      if rect.left < self.right:
        h = True
    else:
      if rect.right > self.left:
        h = True

    intersects = (v and h)
    if(intersects):
      logger.debug("Intersection:\n{}\n{}".format(self, rect))
    return (v and h)

  def draw(self, canvas, tags = None, color = "black"):
    if(canvas):
      elms = []
      elms.append(canvas.create_rectangle(
        self.left, self.top,
        self.right, self.bottom,
        tags = tags,
        outline = color
      ))
      return elms
    return None


class Layout:
  def __init__(self, num_slices, canvas = None, margin = 0.05, precision = default_precision):
    self.rects = SortedListWithKey(key = lambda r: r.max_radius())
    self.outer_rects = {}
    self.angle = 0
    self.num_slices = num_slices
    self.angle_step = math.tau/num_slices
    self.canvas = canvas
    self.margin = margin

  def add_rect(self, size):
    if(len(self.rects) == 0):
      rect = Rect(size, (0,0))
    else:
      rect = self.place_rect(size)

    if rect is None:
      logger.debug("Couldn't add rectangle!")
      return

    rect.draw(self.canvas)

    self.rects.add(rect)
    return rect

  def get_radius(self, angle):
    try:
      outer_rect_idx = self.outer_rects[angle]
    except KeyError:
      outer_rect_idx = 0

    max_radius = None
    for i in reversed(range(len(self.rects))):
      cur_radius = self.rects[i].outer_radius(angle)
      if cur_radius and (max_radius is None or cur_radius.length() > max_radius.length()):
        new_outer = i
        max_radius = copy(cur_radius)

    self.outer_rects[angle] = new_outer

    return max_radius

  def intersects_any(self, rect):
    for r in reversed(self.rects):
      if r.max_radius() < rect.min_radius():
        return False
      elif r.intersects(rect):
        return True

  def place_rect(self, size):
    min_radius = None
    rect = Rect(size)
    if(self.canvas):
      self.canvas.delete("outer_radius")

    radii = []
    for ang in frange(math.tau, self.angle_step):
      logger.debug("---")
      logger.debug("Getting radius for angle {}".format(Rayish.as_pi(ang)))
      base_radius = self.get_radius(ang)
      radii.append(base_radius)

    radii.sort(key = lambda x: x.length())

    hexcolor = lambda tup: '#%02x%02x%02x' % tuple(tup)
    curcolor = [255, 0, 0]
    color_inc = int(192/self.num_slices)

    for r in radii:
      r.draw(self.canvas, tags="outer_radius", color = hexcolor(curcolor))
      curcolor[0] -= color_inc

    # Try just side-scooting
    for r in radii:
      # Move rectangle so edge is on radius end
      axis = r.side % 2
      direction = 1-int(r.side/2)*2
      move_dist = [0,0]
      move_dist[axis] = direction*size[axis]/2*(1+self.margin)

      rect.move_to(r.end)
      rect.move(move_dist)

      # If we're good here, that's as good as we'll get
      if not self.intersects_any(rect):
        return rect

      # Otherwise, scoot around until we find something better
      # Scoot from inside out
      nudge_pos = [0,0]
      nudge_neg = [0,0]
      nudge_pos[1-axis] = size[1-axis]/(self.num_slices/2)
      nudge_neg[1-axis] = -size[1-axis]/(self.num_slices/2)

      rect_pos = copy(rect)
      rect_neg = copy(rect)
      curcolor = [0, 255, 0]
      if(self.canvas):
        self.canvas.delete("shifty")
      for nudge_step in range(1, int(self.num_slices/2)):
        # Shift positive
        rect_pos.move(nudge_pos)
        rect_pos.draw(self.canvas, tags="shifty", color = hexcolor(curcolor))
        if not self.intersects_any(rect_pos):
          return rect_pos

        rect_neg.move(nudge_neg)
        rect_neg.draw(self.canvas, tags="shifty", color = hexcolor(curcolor))
        if not self.intersects_any(rect_neg):
          return rect_neg

        curcolor[1] -= color_inc*2

    return None

      #budge = 1
      #while True:
      #  for r in self.rects:
      #    if rect.intersects(r):
      #      rect.move(move_dist*budge)
      #      continue

      #  # At this point, we didn't intersect
      #  # Let's move closer
      #  budge = -budge/2


