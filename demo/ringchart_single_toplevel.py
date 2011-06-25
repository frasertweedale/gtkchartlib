#!/usr/bin/env python

from __future__ import division

import gtk

import gtkchartlib.ringchart

win = gtk.Window()
win.set_title('RingChart demo')
win.connect('delete-event', gtk.main_quit)

event_box = gtk.EventBox()

win.add(event_box)

items = [gtkchartlib.ringchart.RingChartItem(1, tooltip='100%')]
items2 = map(
    lambda x: gtkchartlib.ringchart.RingChartItem(x, tooltip='33%'),
    [1 / 3, 1 / 3, 1 / 3]
)
items[0].set_items(items2)

w = gtkchartlib.ringchart.RingChart(items)
event_box.add(w)

win.show_all()

gtk.main()
