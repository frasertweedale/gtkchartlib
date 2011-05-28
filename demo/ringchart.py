#!/usr/bin/env python

import gtk

import gtkchartlib.ringchart

win = gtk.Window()
win.set_title('RingChart demo')
win.connect('delete-event', gtk.main_quit)

event_box = gtk.EventBox()

win.add(event_box)

values = [1, 2, 3, 4]
items = map(gtkchartlib.ringchart.RingChartItem, values)
for item in items:
    item.tooltip = str(item.value)
    items2 = map(
        lambda x: gtkchartlib.ringchart.RingChartItem(x, tooltip=str(x)),
        map(lambda x: item.value * x / sum(values), map(float, values))
    )
    item.set_items(items2)
w = gtkchartlib.ringchart.RingChart(items)
event_box.add(w)

win.show_all()

gtk.main()
