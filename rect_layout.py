import math
math.tau = math.pi*2

def frange(end, jump):
  x = 0
  while x < end:
    yield x
    x += jump

class Rayish:
  def __init__(self, angle_or_end, origin = (0,0), length=1):
    self.origin = origin
    try:
      self.end = angle_or_end
      self.angle = math.atan2(
        self.end[1] - self.origin[1],
        self.end[0] - self.origin[0]
      )
    except TypeError:
      self.angle = angle_or_end
      self.end = (
        self.origin[0] + math.cos(self.angle)*length,
        self.origin[1] + math.sin(self.angle)*length
      )

    print("Created {}".format(self))
    
    self._length = None

  def __str__(self):
    return "Rayish from {} to {} (angle {})".format(
      self.origin, self.end, self.angle
    )

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
    ydiff = (a[1] - b[1], self.origin[1] - self.end[1]) #Typo was here

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
      return None

    d = (det(a, b), det(self.origin, self.end))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return (x, y)

class Rect:
  def __init__(self, size, center = (0,0)):
    self.size = size
    self.move_to(center)

  def __str__(self):
    return "Rectangle: tldr {}/{}/{}/{}".format(
      self.top, self.left, self.bottom, self.right
    )

  def move(self, dist):
    self.move_to((
      self.center[0] + dist[0],
      self.center[1] + dist[1]
    ))

  def move_to(self, center):
    self.center = center

    self.left = center[0] - self.size[0]/2
    self.right = center[0] + self.size[0]/2
    self.top = center[1] - self.size[1]/2
    self.bottom = center[1] + self.size[1]/2

  def corners(self):
    return [
      (self.right, self.top),
      (self.left, self.top),
      (self.left, self.bottom),
      (self.right, self.bottom)
    ]

  def corner_angles(self, origin = (0,0)):
    return [
      Rayish(c).angle
      for c in self.corners()
    ]

  def intersects_angle(self, angle, origin = (0,0)):
    distances = self.corner_angles(origin)
    return (min(distances) < 0 and max(distances) > 0)

  def outer_radius(self, angle):
    corners = self.corners()
    corner_angles = self.corner_angles()
    distances = [ca - angle for ca in corner_angles]
    if not min(distances) < 0 and max(distances) > 0:
      return False

    ray = Rayish(angle)

    # We can ignore the closest corner
    # Line will then be between two of the remaining points
    ignore_corner = self.get_ignore(angle)
    middle_corner = (ignore_corner + 2) % 4
    dist_middle = distances[middle_corner]
    print("Finding sides for angle {}, ignoring corner {}, middle corner {}".format(
      angle, ignore_corner, middle_corner
    ))
    print(distances)
    if(dist_middle < 0):
      point = ray.intersects_segment(corners[(middle_corner - 1) % 4], corners[middle_corner])
      side = middle_corner
    else:
      point = ray.intersects_segment(corners[(middle_corner + 1) % 4], corners[middle_corner])
      side = (middle_corner + 1) % 4

    ray = Rayish(point)
    ray.side = side
    return ray

  def get_ignore(self, angle):
    quadrant = math.floor(angle/math.pi/2)
    return int((quadrant + 2) % 4)

  def intersects(self, rect):
    # origin top-left
    # "below" is >
    # "above" is <
    print(rect)
    print(self)
    v = False
    if rect.top > self.top:
      if rect.top < self.bottom:
        vert = True
    else:
      if rect.bottom > self.top:
        vert = True

    h = False
    if rect.left > self.left:
      if rect.left < self.right:
        h = True
    else:
      if rect.right > self.left:
        h = True

    return (v and h)

class Layout:
  def __init__(self, num_slices, canvas = None):
    self.rects = []
    self.outer_rects = {}
    self.angle = 0
    self.angle_step = math.tau/num_slices
    self.canvas = canvas

  def add_rect(self, size):
    if(len(self.rects) == 0):
      rect = Rect(size, (0,0))
    else:
      rect = self.place_rect(size)

    if rect is None:
      print("Couldn't add rectangle!")
      return

    self.rects.append(rect)

    if(self.canvas):
      self.canvas.create_rectangle(rect.top+200, rect.left+200, rect.bottom+200, rect.right+200)

  def get_radius(self, angle):
    try:
      outer_rect_idx = self.outer_rects[angle]
    except KeyError:
      outer_rect_idx = 0

    max_radius = None
    for i in reversed(range(len(self.rects))):
      cur_radius = self.rects[i].outer_radius(angle)
      if max_radius is None or cur_radius.length() > max_radius.length():
        new_outer = i
        max_radius = cur_radius

    self.outer_rects[angle] = new_outer

    return max_radius

  def place_rect(self, size):
    min_radius = None
    rect = Rect(size)
    for ang in frange(math.tau, self.angle_step):
      print(ang)
      base_radius = self.get_radius(ang)
      print(base_radius)
      print(base_radius.side)
      if base_radius.side % 2:
        move_dist = (0, size[1])
      else:
        move_dist = (size[0], 0)

      rect_center = (
        base_radius.end[0] + move_dist[0],
        base_radius.end[1] + move_dist[1]
      )
      rect.move_to(rect_center)
      
      for r in self.rects:
        if rect.intersects(r):
          continue 

      if min_radius is None or base_radius.length() < min_radius.length():
        min_radius = base_radius

    if min_radius:
      rect_center = (
        base_radius.end[0] + move_dist[0],
        base_radius.end[1] + move_dist[1]
      )
      rect.move_to(rect_center)
    else:
      rect = None

    return rect


      #budge = 1
      #while True:
      #  for r in self.rects:
      #    if rect.intersects(r):
      #      rect.move(move_dist*budge)
      #      continue

      #  # At this point, we didn't intersect
      #  # Let's move closer
      #  budge = -budge/2

