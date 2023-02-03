import math
import numpy as np
from Point import Point

class Segment:
    def __init__(self, start: Point = None, end: Point = None):
        self._start = start
        self._end = end


    def __get__(self) -> tuple[Point, Point]:
        return (self._start, self._end)


    def translate(self, dx: float = 0.0, dy: float = 0.0):
        self._start.translate(dx, dy)
        self._end.translate(dx, dy)

    
    def extend(self, dist):
        # segment is horizontal
        if (self._end.y - self._start.y == 0):
            self._start = Point(self._start.x - dist, self._start.y)
            self._end = Point(self._end.x + dist, self._end.y)
        # segment is vertical
        elif (self._end.x - self._start.x == 0):
            self._start = Point(self._start.x, self._start.y - dist)
            self._end = Point(self._end.x, self._end.y + dist)
        else:
            vector = (self._end.x - self._start.x, self._end.y - self._start.y)
            vector_l = math.sqrt(math.pow((self._end.x - self._start.x), 2) + math.pow(self._end.y - self._start.y, 2))
            vector_normalized = (vector[0] / vector_l, vector[1] / vector_l)
            self._end = Point(self._end.x + dist * vector_normalized[0], self._end.y + dist * vector_normalized[1])
            self._start = Point(self._start.x - dist * vector_normalized[0], self._start.y - dist * vector_normalized[1])


    def intersect(self, other_segment: "Segment" = None) -> Point | None:
        p_vect_a = np.cross(np.array([self.start.x, self.start.y, 1]), np.array([self.end.x, self.end.y, 1]))
        p_vect_b = np.cross(np.array([other_segment.start.x, other_segment.start.y, 1]), np.array([other_segment.end.x, other_segment.end.y, 1]))

        intersect = np.cross(p_vect_a, p_vect_b)

        if intersect[2] == 0:
            return None

        return Point(intersect[0] / intersect[2], intersect[1] / intersect[2])


    @property
    def start(self) -> Point:
        return self._start


    @start.setter
    def start(self, val: Point):
        self._start = val


    @property
    def end(self) -> Point:
        return self._end


    @end.setter
    def end(self, val: Point):
        self._end = val

        
    @property
    def length(self) -> float:
        return math.sqrt(math.pow(self._end.x - self._start.x, 2) + math.pow(self._end.y - self._start.y, 2))