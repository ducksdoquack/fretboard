#!/usr/bin/env python

import math
import inkex
from inkex import Group, PathElement, ClipPath, Polygon
from Point import Point
from Segment import Segment


class Fretboard(inkex.GenerateExtension):

    def __init__(self):
        inkex.GenerateExtension.__init__(self)
        self._taper_factor = None
        self._taper_angle = None
        self._fretboard_length = None
        self._skew = None
        self._bass_string = Segment()
        self._treble_string = Segment()
        self._nut = Segment()
        self._frets= []
        self._fb_sides = []


    def add_arguments(self, pars):
        pars.add_argument("--scale_length_bass", type=float, default=863.6, help="Scale length (bass side if fanned frets enabled)")
        pars.add_argument("--strings", type=int, default=4, help="Number of strings")
        pars.add_argument("--draw_strings", type=inkex.Boolean, default=True, help="Draw the fretboard with the strings")
        pars.add_argument("--extend_strings", type=inkex.Boolean, default=False, help="Extend the strings past the nut and bridge")
        pars.add_argument("--fanned", type=inkex.Boolean, default=False, help="Enable fanned fret mode")
        pars.add_argument("--scale_length_treble", type=float, default=863.6, help="Scale length of treble side")
        pars.add_argument("--fan_pivot", type=int, default=7, help="Horizontal fret")
        pars.add_argument("--nut_width", type=float, default=44.0, help="Width of the nut")
        pars.add_argument("--strings_spacing_at_nut", type=float, default=11.5, help="Distances between the strings at the nut")
        pars.add_argument("--strings_spacing_at_bridge", type=float, default=18.0, help="Distances between the strings at the bridge")
        pars.add_argument("--frets", type=int, default=19, help="Number of frets")
        pars.add_argument("--bass_compensation", type=float, default=8.0)
        pars.add_argument("--treble_compensation", type=float, default=4.0)


    def generate(self):
        if not self.check_input_values():
            return

        if self.options.fanned == False:
            self.options.scale_length_treble = self.options.scale_length_bass

        fretboard_group = Group.new('fretboard')
        strings_group = Group.new('strings')
        frets_group = Group.new('frets')
        bridge_group = Group.new('bridge')
        clip_contour_group = Group.new('contour')
        fb_side_group = Group.new('fb_side')

        strings_group.append(self.strings())
        frets_group.append(self.nut())
        frets_group.append(self.frets())
        bridge_group.append(self.bridge())
        clip_contour_group.append(self.clip_contour())
        fb_side_group.append(self.fb_sides())

        # Clipping the frets with contour
        clip = ClipPath()
        clip.append(PathElement(d=str(clip_contour_group.get_path())))
        clip_id = self.svg.get_unique_id('clipPath')
        clip.set('id', clip_id)
        self.svg.defs.append(clip)
        frets_group.set('clip-path', 'url(#{})'.format(str(clip_id)))

        fretboard_group.append(frets_group)
        fretboard_group.append(bridge_group)
        fretboard_group.append(strings_group)
        fretboard_group.append(fb_side_group)
        
        fretboard_group.set('fill', 'none')
        fretboard_group.set('stroke', 'black')
        fretboard_group.set('stroke-width', '0.5')
        
        return fretboard_group


    def check_input_values(self):
        try:
            if self.options.scale_length_bass < 0:
                raise inkex.utils.AbortExtension("Bass side scale length should be positive.")
            elif self.options.scale_length_bass < self.options.scale_length_treble:
                raise inkex.utils.AbortExtension("Bass side scale length should be longer than treble side.")

            if self.options.scale_length_treble < 0:
                raise inkex.utils.AbortExtension("Treble side scale length should be positive.")
            
            if self.options.strings <= 0:
                raise inkex.utils.AbortExtension("Number of strings should be 1 or more")
            
            if self.options.fan_pivot > self.options.frets or self.options.fan_pivot < 0:
                raise inkex.utils.AbortExtension(f"The horizontal fret should be between 0 and {self.options.frets}.")
            
            if self.options.nut_width < 0:
                raise inkex.utils.AbortExtension("Nut width should be positive.")
            
            if self.options.strings_spacing_at_nut < 0:
                raise inkex.utils.AbortExtension("String spacing at nut should be positive.")

            if self.options.strings_spacing_at_bridge < 0:
                raise inkex.utils.AbortExtension("String spacing at bridge width should be positive.")

        except inkex.utils.AbortExtension as e:
            inkex.utils.errormsg(e)
            return False
        
        return True

    
    def nut(self):
        nut = PathElement()
        self._nut.start = Point(self._bass_string.start.x, self._bass_string.start.y)
        self._nut.end = Point(self._treble_string.start.x, self._treble_string.start.y)
        nut_segment = Segment(Point(self._bass_string.start.x, self._bass_string.start.y), Point(self._treble_string.start.x, self._treble_string.start.y))
        nut_segment.extend(40)

        nut.path = f"M {nut_segment.start.x} {nut_segment.start.y} L {nut_segment.end.x} {nut_segment.end.y}"
        return nut
    

    def bridge(self):
        bridge = PathElement()
        path = []
        # theorical
        bridge_theorical_segment = Segment(Point(self._bass_string.end.x, self._bass_string.end.y), Point(self._treble_string.end.x, self._treble_string.end.y))
        bridge_theorical_segment.extend(40)
        path.append(f"M {bridge_theorical_segment.start.x} {bridge_theorical_segment.start.y} L {bridge_theorical_segment.end.x} {bridge_theorical_segment.end.y}")
        # compensated
        bridge_compensated_segment = Segment(Point(self._bass_string.end.x, self._bass_string.end.y + self.options.bass_compensation), Point(self._treble_string.end.x, self._treble_string.end.y + self.options.treble_compensation))
        bridge_compensated_segment.extend(40)
        path.append(f"M {bridge_compensated_segment.start.x} {bridge_compensated_segment.start.y} L {bridge_compensated_segment.end.x} {bridge_compensated_segment.end.y}")
        
        bridge.path = ''.join(path)
        return bridge


    def frets(self):
        fret = PathElement()
        path = []
        
        # the latest fret is the fingerboard end
        for n in range(1, self.options.frets + 2):
            fret_start_point = self.find_coord_on_segment(self._bass_string, self.distance_to_nut(self.options.scale_length_bass, n))
            fret_end_point = self.find_coord_on_segment(self._treble_string, self.distance_to_nut(self.options.scale_length_treble, n))
            # save real positions
            self._frets.append(Segment(fret_start_point, fret_end_point))
            # draw extended segments
            fret_segment = Segment(Point(fret_start_point.x, fret_start_point.y), Point(fret_end_point.x, fret_end_point.y))
            fret_segment.extend(40)
            path.append(f"M {fret_segment.start.x} {fret_segment.start.y} L {fret_segment.end.x} {fret_segment.end.y}")

        fret.path = ''.join(path)
        return fret


    def clip_contour(self):
        points = []

        string_to_fb_side = (self.options.nut_width - (self.options.strings_spacing_at_nut * (self.options.strings - 1))) / 2
        fb_side_bass = Segment(Point(self._bass_string.start.x - string_to_fb_side, self._bass_string.start.y), Point(self._bass_string.end.x - string_to_fb_side, self._bass_string.end.y))
        fb_side_bass.extend(100)
        self._fb_sides.append(fb_side_bass)
        fb_side_treble = Segment(Point(self._treble_string.start.x + string_to_fb_side, self._treble_string.start.y), Point(self._treble_string.end.x + string_to_fb_side, self._treble_string.end.y))
        fb_side_treble.extend(100)
        self._fb_sides.append(fb_side_treble)
        
        # LEFT
        points.append(f"{fb_side_bass.end.x},{fb_side_bass.end.y} {fb_side_bass.start.x},{fb_side_bass.start.y}")
        # TOP
        points.append(f" {fb_side_treble.start.x},{fb_side_treble.start.y}")
        # RIGHT
        points.append(f" {fb_side_treble.end.x},{fb_side_treble.end.y}")
        
        return Polygon(points = ''.join(points))

    
    def fb_sides(self):
        upper_left = self._nut.intersect(self._fb_sides[0])
        upper_right = self._nut.intersect(self._fb_sides[1])
        lower_left = self._frets[self.options.frets].intersect(self._fb_sides[0])
        lower_right = self._frets[self.options.frets].intersect(self._fb_sides[1])

        return Polygon(points = f"{upper_left.x},{upper_left.y} {upper_right.x},{upper_right.y} {lower_right.x},{lower_right.y} {lower_left.x},{lower_left.y}")
    
    
    def outer_strings(self):
        dx = ((self.options.strings_spacing_at_bridge * (self.options.strings - 1)) / 2) - ((self.options.strings_spacing_at_nut * (self.options.strings - 1)) / 2)
        
        # BASS
        self._bass_string.start = Point(0, 0)
        #dx = ((self.options.strings_spacing_at_bridge - self.options.strings_spacing_at_nut) * self.options.strings) / 2
        dy = math.sqrt(math.pow(self.options.scale_length_bass, 2) - math.pow(dx, 2))
        self._bass_string.end = Point(-dx, dy)

        # TREBLE
        self._treble_string.start = Point(0, 0)
        #dx = ((self.options.strings_spacing_at_bridge - self.options.strings_spacing_at_nut) * self.options.strings) / 2
        dy = math.sqrt(math.pow(self.options.scale_length_treble, 2) - math.pow(dx, 2))
        self._treble_string.end = Point(dx, dy)

        # TRANSLATE FROM PIVOT (0, 0)
        tx = self.options.strings_spacing_at_nut * (self.options.strings - 1)
        ty = self.find_coord_on_segment(self._bass_string, self.distance_to_nut(self.options.scale_length_bass, self.options.fan_pivot)).y - \
             self.find_coord_on_segment(self._treble_string, self.distance_to_nut(self.options.scale_length_treble, self.options.fan_pivot)).y
        self._treble_string.translate(dx = tx, dy = ty)


    def strings(self):
        self.outer_strings()
        inner_strings = PathElement()
        path = []
        
        outer_dx = ((self.options.strings_spacing_at_bridge * (self.options.strings - 1)) / 2) - ((self.options.strings_spacing_at_nut * (self.options.strings - 1)) / 2)
        
        for string in range(0, self.options.strings):
            start_x = self._bass_string.start.x + self.options.strings_spacing_at_nut * string
            start_y = self._bass_string.start.y + (self._treble_string.start.y * (string / (self.options.strings - 1)))

            end_x = self._bass_string.end.x + self.options.strings_spacing_at_bridge * string
            end_y = self._bass_string.end.y - ((self._bass_string.end.y - self._treble_string.end.y) * (string / (self.options.strings - 1)))
            
            string_segment = Segment(Point(start_x, start_y), Point(end_x, end_y))
            
            if self.options.extend_strings:
                string_segment.extend(200)

            if self.options.draw_strings:
                path.append(f"M {string_segment.start.x} {string_segment.start.y} L {string_segment.end.x} {string_segment.end.y}")

        inner_strings.path = ''.join(path)

        return inner_strings


    @staticmethod
    def distance_to_nut(scale, n):
        # d = s – (s / (2 ^ (n / 12)))
        # d = distance from nut
        # s = scale length
        # n = fret number
        return scale - (scale / (pow(2, (n / 12))))


    # Given a distance from segment origin (x1, y1), find the coordinate of the point on that segment
    @staticmethod
    def find_coord_on_segment(segment, dist):
        scale_factor = dist / segment.length
        return Point(((segment.end.x - segment.start.x) * scale_factor) + segment.start.x, ((segment.end.y - segment.start.y)* scale_factor) + segment.start.y)


if __name__ == '__main__':
    Fretboard().run()