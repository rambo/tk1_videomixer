#!/usr/bin/env python3
# Ideas and code stolen from https://raw.githubusercontent.com/kulve/gst-multiwindow/master/multiwindow.py
from os import path
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, Gtk
import argparse
import math
from time import sleep
from collections import OrderedDict

# Needed for window.get_xid(), xvimagesink.set_window_handle(), respectively:
from gi.repository import GdkX11, GstVideo

# Initialize
GObject.threads_init()
Gst.init(None)



class Player(object):
    pipelines = OrderedDict()
    buses = OrderedDict()

    def __init__(self):
        self.mainloop = GObject.MainLoop()
        self._two_bins()

    def _two_bins(self):
        self.add_pipeline('main')
        pl = self.pipelines['main']
        
        b1 = Gst.Bin.new('cam1')
        pl.add(b1)
        src = Gst.ElementFactory.make('v4l2src', 'webcam')
        src.set_property('device', '/dev/video0')
        b1.add(src)
        
        dec = Gst.ElementFactory.make('omxh264dec', 'decoder')
        b1.add(dec)

        src.link(dec)

        gp1 = Gst.GhostPad.new('src', dec.get_static_pad('src'))
        b1.add_pad(gp1)


        b2 = Gst.Bin.new('out')
        pl.add(b2)
        out = Gst.ElementFactory.make('nvhdmioverlaysink', 'output')
        out.set_property('sync', False)
        b2.add(out)
        gp2 = Gst.GhostPad.new('sink', out.get_static_pad('sink'))
        b2.add_pad(gp2)
        
        
        b1.link(b2)



    def _two_pipelines(self):
        self.add_pipeline('cam1')
        pl = self.pipelines['cam1']

        src = Gst.ElementFactory.make('v4l2src', 'webcam')
        src.set_property('device', '/dev/video0')
        pl.add(src)
        
        dec = Gst.ElementFactory.make('omxh264dec', 'decoder')
        pl.add(dec)

        self.add_pipeline('hdmiout')
        pl2 = self.pipelines['hdmiout']

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

    def add_pipeline(self, name):
        pipeline = Gst.Pipeline(name)
        self.pipelines[name] = pipeline
        # Create bus to get events from GStreamer pipeline
        bus = pipeline.get_bus()
        self.buses[name] = bus
        bus.add_signal_watch()
        bus.connect('message::error', self.on_error)

    def on_error(self, bus, msg):
        print('on_error():', msg.parse_error())

    def run(self):
        for name in self.pipelines:
            self.pipelines[name].set_state(Gst.State.PLAYING)
        self.mainloop.run()

    def quit(self):
        for name in reversed(self.pipelines):
            print("nulling %s" % name)
            self.pipelines[name].set_state(Gst.State.NULL)
        self.mainloop.quit()



if __name__ == '__main__':
    p = Player()
    p.hook_signals()
    try:
        p.run()
    except KeyboardInterrupt:
        p.quit()
