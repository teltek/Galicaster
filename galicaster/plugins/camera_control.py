# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/camera_control
#
# Copyright (c) 2016, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

import thread

from galicaster.core import context
from galicaster.core.core import PAGES
from galicaster.classui import get_ui_path

import galicaster.utils.pysca as pysca

from gi.repository import Gtk, GObject, Pango

def init():
    global conf,logger, pan, tilt
    dispatcher = context.get_dispatcher()
    conf = context.get_conf()
    logger = context.get_logger()

    pysca.connect("/dev/ttyUSB0")
    logger.info("Cam connected")
    pysca.pan_tilt_home(1)
    pan = 0
    tilt = 0

    dispatcher.connect('init',load_tabs)

def load_tabs(element):
    global logger
    try:
        builder = context.get_mainwindow().nbox.get_nth_page(PAGES["REC"]).gui
    except Exception as error:
        logger.debug("La vista no existe")
        return None

    notebook = builder.get_object("data_panel")
    builder = Gtk.Builder()
    label = Gtk.Label("Camera Control")

    builder.add_from_file(get_ui_path("camera_control.glade"))
    notebook2 = builder.get_object("notebook1")
    label2 = builder.get_object("label2")
    label3 = builder.get_object("label3")
    label_style(label)
    label_style(label2)
    label_style(label3)
    notebook.append_page(notebook2,label)
    builder.connect_signals(Handler())

    # up = builder.get_object("button1")
    # up.connect("pressed", on_press)
    # up.connect("released", on_release)

def on_press(self):
    # kick off time out
    print "on_press"
    self._repeat = True
    timeout = 50
    GObject.timeout_add(timeout, on_up, self)

def on_release(self):
    # remove timeout
    self._repeat = False

# def on_up(self):
#     global tilt, pan
#     print "Up"
#     return self._repeat
    # tilt += 200
    # if tilt > 0x0ff0:
    #     tilt = 0x0ff0
    # thread.start_new_thread (pysca.pan_tilt, (1,100,100,self.convert(pan),self.convert(tilt)))


def label_style(label):
    label.set_property("ypad",10)
    label.set_property("xpad",10)
    label.set_property("vexpand-set",True)
    label.set_property("vexpand",True)

    size = context.get_mainwindow().get_size()
    k1 = size[0] / 1920.0
    label.set_use_markup(True)
    label.modify_font(Pango.FontDescription(str(int(k1*20))))
    return label


class Handler:
    def on_press(self, *args):
        movements = {"up":self.on_up,"down":self.on_down,"left":self.on_left,"right":self.on_right,"up_left":self.on_up_left,"up_right":self.on_up_right,"down_left":self.on_down_left,"down_right":self.on_down_right}
        print args[0].get_name()
        movement = args[0].get_name()
        # kick off time out
        self._repeat = True
        timeout = 50
        GObject.timeout_add(timeout, movements[movement])

    def on_release(self, *args):
        # remove timeout
        pysca.pan_tilt(1,0,0)
        self._repeat = False

    def on_up(self, *args):
        global tilt, pan
        print "Up"
        # tilt += 200
        # if tilt > 0x0ff0:
        #     tilt = 0x0ff0
        # pysca.pan_tilt(1,100,100,self.convert(pan),self.convert(tilt))
        pysca.pan_tilt(1,0,10)
#        return self._repeat

    def on_right(self, *args):
        global tilt, pan
        print "Right"
        # pan  += 200
        # if pan > 0x1e1b:
        #     pan = 0x1e1b
        # pysca.pan_tilt(1,100,100,self.convert(pan),self.convert(tilt))
        pysca.pan_tilt(1,-10)
#        return self._repeat

    def on_down(self, *args):
        global tilt, pan
        print "Down"
        # tilt -= 200
        # if tilt < -((0xffff-0xfc75)+1):
        #     tilt = -((0xffff-0xfc75)+1)
        # pysca.pan_tilt(1,100,100,self.convert(pan),self.convert(tilt))
        pysca.pan_tilt(1,0,-10)
#        return self._repeat

    def on_left(self, *args):
        global tilt, pan
        print "Left"
        # pan -= 200
        # if pan < -0x1e1b:
        #     pan = -0x1e1b
        # pysca.pan_tilt(1,100,100,self.convert(pan),self.convert(tilt))
        pysca.pan_tilt(1,10)
#        return self._repeat

    def on_up_left(self):
        global tilt,pan
        pysca.pan_tilt(1,10,8)

    def on_up_right(self):
        global tilt,pan
        pysca.pan_tilt(1,-10,8)

    def on_down_left(self):
        global tilt,pan
        pysca.pan_tilt(1,10,-8)

    def on_down_right(self):
        global tilt,pan
        pysca.pan_tilt(1,-10,-8)

    def on_load_presets(self, *args):
        global tilt,pan
        preset = args[0].get_name().split(" ")[1]
        print "Load " + preset
        pysca.recall_memory(1,preset)

    def on_save_presets(self, *args):
        preset = args[0].get_name().split(" ")[1]
        pysca.set_memory(1,preset)

    def on_edit(self, *args):
        print "edit label"
        print args
        args[0].set_label("huehuehue")

    def on_zoom(self, *args):
        print "zoom"
        zoom = args[0].get_value()
        if zoom == 100:
            pysca.set_zoom(1,0x4000)
        else:
            print args[0].get_value()*(0x4000/100)
            pysca.set_zoom(1,zoom*(0x4000/100))

    # def convert(self, value):
    #     if value < 0:
    #       return 0xffff + value
    #     else:
    #         return value
