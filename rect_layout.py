import math

class Ray:
  def __init__(self, origin, end):
    self.origin = origin
    self.end = end
    self.angle = atan2(
      end[0] - origin[0],
      end[1] - origin[1]
    )

  def distance(self, angle):
    phi = math.abs(angle.angle - self.angle) % 360
    distance = phi > 180 ? 360 - phi : phi
    return distance

class Rect:
  # Which corner to ignore for angles < x
  ignore_corners = {
      90: 3, 180: 2,
      270: 1, 360: 0
  }

  def __init__(self, size, center):
    self.left = center[0] - size[0]/2
    self.right = center[0] + size[0]/2
    self.top = center[1] - size[1]/2
    self.bottom = center[1] + size[1]/2

  def move(self, center):
    self.center = center

  def corners(self):
    yield (self.left, self.top)
    yield (self.right, self.top)
    yield (self.right, self.bottom)
    yield (self.left, self.bottom)

  def corner_angles(self, origin = (0,0)):
    return [
      Angle(origin, c).distance(angle)
      for c in self.corners()
    ]

  def intersects_angle(self, angle, origin = (0,0)):
    distances = self.corner_angles(origin)
    return (min(distances) < 0 and max(distances) > 0)

  def outer_radius(self, angle):
    distances = self.corner_angles()
    if not min(distances) < 0 and max(distances) > 0:
      return False

    # We can ignore the closest corner
    # Line will then be between two of the remaining points
    ignore_corner = get_ignore(angle)
    middle_corner = distances[(ignore_corner + 2) % 4]
    if(middle_corner < 0):
    else:

  def get_ignore(self, angle):
    for (max_angle, corner) in ignore_corners.items():
      if angle < max_angle:
        return corner

    return None

  def intersects(self, rect):
    # origin top-left
    # "below" is >
    # "above" is <
    if rect.top > self.top:
      if rect.top < self.bottom:
        return True
    else:
      if rect.bottom > self.top:
        return True

    if rect.left > self.left:
      if rect.left < self.right:
        return True
    else:
      if rect.right > self.left:
        return True

    return False

class Layout:
  def __init__(self, angle_increment):
    self.rects = []
    self.outer_rects = {}
    self.angle = 0
    self.angle_increment = angle_increment

  def add_rect(self, size):
    if(len(self.rects) == 0):
      self.rects.push(Rect(size, (0,0)))
      return

  def get_radius(self, angle):
    try:
      outer_rect_idx = self.outer_rects[angle]
    except KeyError:
      outer_rect_idx = 0

    for i in range(len(self.rects) - 1, outer_rect_idx - 1, -1):
      # Update the outer-est rectangle



def arrange_ships(ships):
  it = iter(ships)
  ship = it.next()
  rects = []
  rects.append(Rect(ship['image_size'], (0,0)))

  for s in it:


