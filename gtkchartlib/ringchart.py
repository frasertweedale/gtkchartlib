# This file is part of gtkchartlib
# Copyright (C) 2011 Fraser Tweedale
#
# gtkchartlib is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Ring chart widget with nice colours, tooltips and highlighting.
#
# A ring chart (aka radial tree or multi-level pie chart) is used to
# visualise hierarchical data in concentric circles.  Can also be
# easily used a regular one-level pie chart.
#
# The basic design (and some ideas about how to implement it) came from
# gnome-utils baobab Disk Usage Analyser, Copyright (C) 2008 Igalia,
# distributed under the terms of the GNU General Public License version
# 2 or later.
#   http://git.gnome.org/browse/gnome-utils/
#
# The colours are from the Tango palette:
#   http://tango.freedesktop.org/Tango_Icon_Theme_Guidelines

from __future__ import division

import math
import sys

import gtk

if gtk.pygtk_version < (2, 12, 0):
    sys.exit("PyGtk 2.12 or later required")


colours = [
    (0.94, 0.16, 0.16),
    (0.68, 0.49, 0.66),
    (0.45, 0.62, 0.82),
    (0.54, 0.89, 0.20),
    (0.91, 0.73, 0.43),
    (0.99, 0.68, 0.25),
]


class RingChartItem(object):
    """Binds some value with ringchart attributes.

    A RingChartItem may be a child of a RingChart (i.e. a top-level item)
    or a child of another RingChartItem.

    The value must be a float, or must support conversion to float.

    The "tooltip" attribute specifies tooltip text.  If None, no tooltip
    will be shown for the item.

    """
    def __init__(self, value, parent=None, items=None, tooltip=None):
        """Initialise the RingChartItem.

        Raises ValueError if a negative value is provided; negative values
        do not make sense in radial charts.
        """
        if value < 0:
            raise ValueError("RingChart does not support negative values.")
        super(RingChartItem, self).__init__()
        self.value = value
        self.parent = parent
        self.tooltip = tooltip
        self.highlighted = False  # don't start out highlighted
        self.items = items
        if items:
            self.set_items(items)

    def set_items(self, items):
        """Add a sequence of child RingGraphItem objects to this item."""
        for item in items:
            item.parent = self
        self.items = items

    def __float__(self):
        return float(self.value)

    def calc_proportion(self, depth=1):
        """Set the dimensions of this RingChartItem.

        The dimensions are the proportion of the parent and the depth.

        Returns the maximum depth of the tree of items.
        """
        self.proportion = float(self) / float(self.parent)
        self.depth = 1

        if not self.items:
            return depth
        return max(map(lambda x: x.calc_proportion(depth + 1), self.items))

    def calc_angle(self, minangle):
        """Calculate the angle of this RingChartItem.

        Return the maximum angle.
        """
        self.angle = self.parent.angle * self.proportion
        self.minangle = minangle
        self.maxangle = minangle + self.angle

        if self.items:
            angle = minangle
            for item in self.items:
                angle = item.calc_angle(angle)

        # calculate the colour for this angle
        persex = self.minangle / math.pi * 3
        colour_a, frac = divmod(persex, 1)
        colour_b = (colour_a + 1) % 6
        self.colour = map(
            lambda a, b: a - (a - b) * frac,
            colours[int(colour_a)],
            colours[int(colour_b)]
        )

        return self.maxangle

    def occupies_point(self, rad, angle, recurse=True):
        if rad < self.minrad:
            return False  # radius is too small
        if angle < self.minangle or angle > self.maxangle:
            return False  # not in angle range
        if rad < self.maxrad:
            return self  # exactly this item
        if not recurse or not self.items:
            return False  # recursion disabled no children to check
        for item in self.items:
            match = item.occupies_point(rad, angle)
            if match:
                return match
        return False  # no match among children

    def draw(self, cr, x, y, minrad, thickness, chartdepth):
        """Draw a RingChartItem and child items."""
        if self.depth > chartdepth:
            return

        # store centre and radii
        self.x = x
        self.y = y
        self.minrad = minrad
        self.maxrad = minrad + thickness

        self._draw(cr)

        # draw items
        if self.items:
            for item in self.items:
                item.draw(cr, x, y, self.maxrad, thickness, chartdepth)

    def _draw(self, cr, highlight=False):
        revolution = not (self.minangle - self.maxangle) % (2 * math.pi)
        colour = map(lambda x: x + (1 - x) / 2, self.colour) \
            if highlight else self.colour
        cr.arc(self.x, self.y, self.minrad, self.minangle, self.maxangle)
        if revolution:
            # do not draw line between arcs
            cr.new_sub_path()
        cr.arc_negative(self.x, self.y, self.maxrad,
                        self.maxangle, self.minangle)
        if not revolution:
            # do draw line between arcs
            cr.close_path()
        cr.set_source_rgb(*colour)
        cr.fill_preserve()
        cr.set_line_width(1)
        cr.set_source_rgb(0, 0, 0)
        cr.stroke()

    def highlight(self, cr):
        """Highlight this exact RingChartItem."""
        if self.highlighted:
            return
        self._draw(cr, highlight=True)
        self.highlighted = True

    def unhighlight(self, cr):
        """Unhighilght this RingChartItem."""
        if not self.highlighted:
            return
        self._draw(cr)
        self.highlighted = False


class RingChart(gtk.DrawingArea):
    __gsignals__ = {
        'expose-event': 'override',
        'query-tooltip': 'override',
        'motion-notify-event': 'override',
    }

    def __init__(self, items, chartdepth=5, inner=None):
        super(RingChart, self).__init__()
        self.set_has_tooltip(True)

        self.items = items
        for item in self.items:
            item.parent = self

        self.chartdepth = chartdepth
        self.depth = 0  # initial depth

        self.value = sum(map(float, items))
        self.angle = 2 * math.pi

        # calculate item proportions
        self.itemdepth = max(map(lambda x: x.calc_proportion(), self.items))

        # set inner based on itemdepth, unless explicitly set
        if inner is None:
            inner = False if self.itemdepth == 1 else True
        self.inner = inner

        # calculate item angles
        angle = 0
        for item in self.items:
            angle = item.calc_angle(angle)

        # there is no item highlighted (yet)
        self.highlighted = None

    def __float__(self):
        return float(self.value)

    def cartesian_to_polar(self, x, y):
        """Convert window cartesian coords to graph-origin polar coords.

        Return (r, theta) with theta 0..2*pi.
        """
        relx = x - self.x
        rely = y - self.y
        r = math.sqrt(rely ** 2 + relx ** 2)
        theta = math.atan2(rely, relx)
        theta = theta if theta > 0 else theta + math.pi * 2
        return r, theta

    def do_expose_event(self, event):
        cr = self.window.cairo_create()

        depth = min(self.chartdepth, self.itemdepth)

        x, y, w, h = self.allocation

        self.x = w / 2
        self.y = h / 2
        self.maxrad = (min(w, h) - 10) / 2
        thickness = self.maxrad / (depth + int(self.inner))
        self.minrad = thickness if self.inner else 0

        for item in self.items:
            item.draw(cr, self.x, self.y, self.minrad, thickness, depth)

    def do_query_tooltip(self, x, y, keyboard_mode, tooltip):
        if keyboard_mode:
            return False

        # convert point to polar coordinates
        rad, angle = self.cartesian_to_polar(x, y)

        if rad < self.maxrad and rad > self.minrad:
            # we are (or might be) in the graph

            # find the RingChartItem that the pointer is in
            for item in self.items:
                match = item.occupies_point(rad, angle)
                if match:
                    tooltip.set_text(match.tooltip)
                    return True

        return False

    def do_motion_notify_event(self, event):
        rad, angle = self.cartesian_to_polar(event.x, event.y)

        # if we have a currently highlighted item, are we in it?
        cr = None
        if self.highlighted:
            if not self.highlighted.occupies_point(rad, angle, recurse=False):
                # no, we have left it.  unhighlight
                cr = self.window.cairo_create()
                self.highlighted.unhighlight(cr)
                self.highlighted = None
            else:
                # we are still in it.  nothing to do
                return
        for item in self.items:
            match = item.occupies_point(rad, angle)
            if match:
                cr = cr or self.window.cairo_create()
                self.highlighted = match
                self.highlighted.highlight(cr)
