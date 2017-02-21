# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/cameracontrol
#
# Copyright (c) 2016, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

import Queue

from galicaster.core import context
from galicaster.core.core import PAGES
from galicaster.classui import get_ui_path, get_image_path

import galicaster.utils.pysca as pysca

from gi.repository import Gtk, Gdk, GObject, Pango, GdkPixbuf

from galicaster.utils.queuethread import T


dispatcher = None
conf = None
logger = None
jobs = None
event_handler = None

def init():
    global conf, logger, event_handler, jobs
    dispatcher = context.get_dispatcher()
    conf = context.get_conf()
    logger = context.get_logger()

    path = conf.get('cameracontrol','path')
    pysca.connect(path)
    pysca.set_zoom(1,0)
    pysca.pan_tilt_home(1)
    dispatcher.connect('init',load_ui)
    pysca.osd_off(1)
    logger.info("Cam connected")


    icons = ["left","right","up1","down1","up_right","up_left","down_left","down_right","plus","minus"]
    icontheme = Gtk.IconTheme()
    for name in icons:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(get_image_path(name+".svg"))
        icontheme.add_builtin_icon(name,20,pixbuf)

    dispatcher.connect("action-key-press", on_key_press)
    dispatcher.connect("action-key-release", on_key_release)


    event_handler = Handler()
    jobs = Queue.Queue()
    t = T(jobs)
    t.setDaemon(True)
    t.start()

def load_ui(element):
    try:
        builder = context.get_mainwindow().nbox.get_nth_page(PAGES["REC"]).gui
    except Exception:
        logger.debug("The view not exist")
        return None

    notebook = builder.get_object("data_panel")
    builder = Gtk.Builder()
    label = Gtk.Label("Camera Control")

    builder.add_from_file(get_ui_path("camera_control.glade"))
    notebook2 = builder.get_object("notebook1")
    label2 = builder.get_object("label2")
    label3 = builder.get_object("label3")
    label1 = builder.get_object("label1")
    label4 = builder.get_object("label4")
    label_style(label)
    label_style(label2, True)
    label_style(label3, True)
    label_style(label1, True, 12)
    label_style(label4, True, 12)
    notebook.append_page(notebook2,label)
    builder.connect_signals(event_handler)

    zoom_levels = conf.get_int('cameracontrol','zoom_levels')
    max_speed_pan_tilt = conf.get('cameracontrol','max_speed_pan_tilt')
    speed_zoom = builder.get_object("adjustment1")
    speed_pan_tilt = builder.get_object("adjustment2")
    speed_zoom.set_upper(zoom_levels)
    speed_pan_tilt.set_upper(int(max_speed_pan_tilt,16))

    speed_pan_tilt.set_value(int(max_speed_pan_tilt,16)/2)
    speed_zoom.set_value(zoom_levels/2)

    grid = builder.get_object("grid1")
    size = context.get_mainwindow().get_size()
    k1 = size[0] / 1920.0
    for button in grid.get_children():
        try:
            image = button.get_children()
            if type(image[0]) == Gtk.Image:
                image[0].set_pixel_size(k1*40)
        except:
            pass

    admin = conf.get_boolean('basic','admin')
    for widget in ["grid2","grid3"]:
        for button in builder.get_object(widget):
            if admin and "save" in button.get_name():
                button.show_all()
            image = button.get_children()
            if type(image[0]) == Gtk.Image:
                image[0].set_pixel_size(int(k1*40))
            else:
                image[0].set_use_markup(True)
                image[0].modify_font(Pango.FontDescription(str(int(k1*20))))

def label_style(label, only_text=None, fsize=20):
    if not only_text:
        label.set_property("ypad",10)
        label.set_property("xpad",10)
        label.set_property("vexpand-set",True)
        label.set_property("vexpand",True)

    size = context.get_mainwindow().get_size()
    k1 = size[0] / 1920.0
    label.set_use_markup(True)
    label.modify_font(Pango.FontDescription(str(int(k1*fsize))))
    return label

def on_key_press(element, source, event):
    if context.get_mainwindow().get_current_page() == PAGES["REC"]:
        if event.keyval == Gdk.keyval_from_name("Up"):
            logger.debug("Key pressed: up")
            event_handler.on_up()

        if event.keyval == Gdk.keyval_from_name("Right"):
            logger.debug("Key pressed: right")
            event_handler.on_right()

        if event.keyval == Gdk.keyval_from_name("Down"):
            logger.debug("Key pressed: down")
            event_handler.on_down()

        if event.keyval == Gdk.keyval_from_name("Left"):
            logger.debug("Key pressed: left")
            event_handler.on_left()

        if event.keyval == Gdk.keyval_from_name("plus"):
            logger.debug("Key pressed: zoom_in")
            event_handler.zoom_in()

        if event.keyval == Gdk.keyval_from_name("minus"):
            logger.debug("Key pressed: zoom_out")
            event_handler.zoom_out()


def on_key_release(element, source, event):
    if event.keyval == Gdk.keyval_from_name("Up") or event.keyval == Gdk.keyval_from_name("Right") or event.keyval == Gdk.keyval_from_name("Down") \
       or event.keyval == Gdk.keyval_from_name("Left") or event.keyval == Gdk.keyval_from_name("plus") or event.keyval == Gdk.keyval_from_name("minus"):
        event_handler.on_release()


zoom_speed = 0
move_speed = 0

class Handler:
    def on_press(self, *args):
        global logger
        movements = {"up":self.on_up,"down":self.on_down,"left":self.on_left,"right":self.on_right,"up_left":self.on_up_left,"up_right":self.on_up_right,"down_left":self.on_down_left,"down_right":self.on_down_right,"zoom_in":self.zoom_in,"zoom_out":self.zoom_out}
        movement = args[0].get_name()
        logger.debug("Button pressed: "+movement)
        self._repeat = True
        timeout = 50
        GObject.timeout_add(timeout, movements[movement])

    def on_release(self, *args):
        jobs.put((pysca.clear_commands, (1,)))
        jobs.put((pysca.zoom, (1, "stop")))
        self._repeat = False

    def on_up(self, *args):
        jobs.put((pysca.pan_tilt, (1,0,move_speed)))

    def on_right(self, *args):
        jobs.put((pysca.pan_tilt, (1,move_speed,0)))

    def on_down(self, *args):
        jobs.put((pysca.pan_tilt, (1,0,-move_speed)))

    def on_left(self, *args):
        jobs.put((pysca.pan_tilt, (1,-move_speed,0)))

    def on_up_left(self):
        jobs.put((pysca.pan_tilt, (1,-move_speed,move_speed-2)))

    def on_up_right(self):
        jobs.put((pysca.pan_tilt, (1,move_speed,move_speed-2)))

    def on_down_left(self):
        jobs.put((pysca.pan_tilt, (1,-move_speed,-move_speed+2)))

    def on_down_right(self):
        jobs.put((pysca.pan_tilt, (1,move_speed,-move_speed+2)))

    def on_load_presets(self, *args):
        preset = args[0].get_name().split(" ")[1]
        jobs.put((pysca.recall_memory, (1,preset)))
        logger.debug("Load camera preset: "+preset)

    def on_save_presets(self, *args):
        preset = args[0].get_name().split(" ")[1]
        jobs.put((pysca.set_memory, (1,preset)))
        logger.debug("Save camera preset: "+preset)

    def zoom_in(self, *args):
        jobs.put((pysca.zoom, (1,"tele",zoom_speed)))

    def zoom_out(self, *args):
        jobs.put((pysca.zoom, (1,"wide",zoom_speed)))

    def on_zoom_speed(self, *args):
        global zoom_speed
        zoom_speed = args[0].get_value()
        logger.debug("Zoom speed set to: "+str(zoom_speed))

    def on_move_speed(self, *args):
        global move_speed
        move_speed = args[0].get_value()
        logger.debug("Pan/Tilt speed set to: "+str(move_speed))
