#!/usr/bin/env python3
# Ideas and code stolen from https://raw.githubusercontent.com/kulve/gst-multiwindow/master/multiwindow.py
from os import path
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, Gtk
import argparse
import math
from time import sleep

# Needed for window.get_xid(), xvimagesink.set_window_handle(), respectively:
from gi.repository import GdkX11, GstVideo

# Initialize
GObject.threads_init()
Gst.init(None)



class Player(object):
    pipelines = []
    buses = []

    def __init__(self):
        self.add_pipeline()
        pl = self.pipelines[0]

        src = Gst.ElementFactory.make('v4l2src', 'webcam')
        src.set_property('device', '/dev/video0')
        pl.add(src)
        
        dec = Gst.ElementFactory.make('omxh264dec', 'decoder')
        pl.add(dec)

        self.add_pipeline()
        pl2 = self.pipelines[1]

        out = Gst.ElementFactory.make('nvhdmioverlaysink', 'output')
        out.set_property('sync', False)
        pl2.add(out)
        ghost = Gst.GhostPad.new('sink', out.get_static_pad('sink'))
        pl2.add_pad(ghost)

        src.link(dec)
        #dec.link(out)

        ghost2 = Gst.GhostPad.new('src', dec.get_static_pad('src'))
        pl.add_pad(ghost2)

        pl.link(pl2)


    def hook_signals(self):
        """Hooks POSIX signals to correct callbacks, call only from the main thread!"""
        import signal as posixsignal
        posixsignal.signal(posixsignal.SIGTERM, self.quit)
        posixsignal.signal(posixsignal.SIGQUIT, self.quit)

    def add_pipeline(self):
        pipeline = Gst.Pipeline()
        self.pipelines.append(pipeline)
        # Create bus to get events from GStreamer pipeline
        bus = pipeline.get_bus()
        self.buses.append(bus)
        bus.add_signal_watch()
        bus.connect('message::error', self.on_error)

    def on_error(self, bus, msg):
        print('on_error():', msg.parse_error())

    def run(self):
        for pl in self.pipelines:
            pl.set_state(Gst.State.PLAYING)
        Gtk.main()

    def quit(self):
        for pl in self.pipelines:
            pl.set_state(Gst.State.NULL)
        Gtk.main_quit()


if __name__ == '__main__':
    p = Player()
    p.hook_signals()
    p.run()
