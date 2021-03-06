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
        #self._two_pipelines()
        #self._two_bins()
        #self._overlaid()
        self._overlaid('nveglglessink')

    def _overlaid(self, sinkname='nvhdmioverlaysink'):
        self.add_pipeline('main')
        pl = self.pipelines['main']
        
        def make_capture():
            b1 = Gst.Bin.new('cam1')
            pl.add(b1)
            dec1 = self._add_capture(b1)
            gp1 = Gst.GhostPad.new('src', dec1.get_static_pad('src'))
            b1.add_pad(gp1)
            return b1

        def make_capture_boxed():
            b1 = Gst.Bin.new('cam1')
            pl.add(b1)
            dec1 = self._add_capture(b1, 640, 480)

            box_b1 = Gst.ElementFactory.make('videobox', 'box_b1')
            box_b1.set_property('top', -50)
            box_b1.set_property('left', -50)
            box_b1.set_property('border-alpha', 0)
            b1.add(box_b1)
            dec1.link(box_b1)

            gp1 = Gst.GhostPad.new('src', box_b1.get_static_pad('src'))
            b1.add_pad(gp1)
            return b1

        def make_logitech_boxed():
            b2 = Gst.Bin.new('cam2')
            pl.add(b2)
            dec2 = self._add_logitech(b2, 640, 480)
            
            conv = Gst.ElementFactory.make('nvvidconv', None)
            b2.add(conv)
            dec2.link(conv)
            
            box_b2 = Gst.ElementFactory.make('videobox', 'box_b2')
            box_b2.set_property('top', -50)
            box_b2.set_property('left', -50)
            box_b2.set_property('border-alpha', 0)
            b2.add(box_b2)
            conv.link_filtered(box_b2, Gst.caps_from_string('video/x-raw, format=(string)I420'))

            gp2 = Gst.GhostPad.new('src', box_b2.get_static_pad('src'))
            b2.add_pad(gp2)
            return b2

        def make_logitech():
            b2 = Gst.Bin.new('cam2')
            pl.add(b2)
            dec2 = self._add_logitech(b2)
            
            conv = Gst.ElementFactory.make('nvvidconv', None)
            b2.add(conv)
            dec2.link(conv)

            cf = Gst.ElementFactory.make('capsfilter', None)
            cf.set_property('caps', Gst.caps_from_string('video/x-raw, format=(string)I420'))
            b2.add(cf)
            conv.link(cf)

            gp2 = Gst.GhostPad.new('src', cf.get_static_pad('src'))
            b2.add_pad(gp2)
            return b2


        #b1 = make_capture()
        #b2 = make_logitech_boxed()
        b1 = make_logitech()
        b2 = make_capture_boxed()


        mix = Gst.ElementFactory.make('videomixer', 'mix')
        pl.add(mix)
        #conv = Gst.ElementFactory.make('nvvidconv', None)
        #pl.add(conv)
        #mix.link(conv)

        out = Gst.ElementFactory.make(sinkname, 'output')
        out.set_property('sync', False)
        pl.add(out)
        #conv.link(out)
        mix.link_filtered(out, Gst.caps_from_string('video/x-raw, width=(int)1920, height=(int)1080'))

        b1.link(mix)
        b2.link(mix)


    def _add_capture(self, bin, w=1920, h=1080):
        src = Gst.ElementFactory.make('v4l2src', 'hdmicapture')
        src.set_property('device', '/dev/video1')
        bin.add(src)

        cf = Gst.ElementFactory.make('capsfilter', None)
        cf.set_property('caps', Gst.caps_from_string('video/x-raw, format=(string)I420, framerate=(fraction)30/1, width=(int)%d, height=(int)%d' % (w,h)))
        bin.add(cf)

        src.link(cf)
        return cf

    def _add_logitech(self, bin, w=1920, h=1080):
        src = Gst.ElementFactory.make('v4l2src', 'logitech')
        src.set_property('device', '/dev/video0')
        bin.add(src)

        dec = Gst.ElementFactory.make('omxh264dec', None)
        bin.add(dec)

        src.link_filtered(dec, Gst.caps_from_string('video/x-h264, framerate=(fraction)30/1, width=(int)%d, height=(int)%d' % (w,h)))
        return dec


    def _two_bins(self, sinkname='nvhdmioverlaysink'):
        self.add_pipeline('main')
        pl = self.pipelines['main']
        
        b1 = Gst.Bin.new('cam1')
        pl.add(b1)
        dec = self._add_logitech(b1)
        #dec = self._add_logitech(b1, 640, 480)
        #dec = self._add_capture(b1)
        #dec = self._add_capture(b1, 640, 480)
        gp1 = Gst.GhostPad.new('src', dec.get_static_pad('src'))
        b1.add_pad(gp1)

        b2 = Gst.Bin.new('out')
        pl.add(b2)
        out = Gst.ElementFactory.make(sinkname, 'output')
        out.set_property('sync', False)
        b2.add(out)
        gp2 = Gst.GhostPad.new('sink', out.get_static_pad('sink'))
        b2.add_pad(gp2)

        b1.link(b2)


    def _two_pipelines(self, sinkname='nvhdmioverlaysink'):
        self.add_pipeline('cam1')
        pl = self.pipelines['cam1']
        dec = self._add_logitech(pl)
        gp1 = Gst.GhostPad.new('src', dec.get_static_pad('src'))
        pl.add_pad(gp1)

        self.add_pipeline('hdmiout')
        pl2 = self.pipelines['hdmiout']
        out = Gst.ElementFactory.make(sinkname, 'output')
        out.set_property('sync', False)
        pl2.add(out)
        gp2 = Gst.GhostPad.new('sink', out.get_static_pad('sink'))
        pl2.add_pad(gp2)

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
