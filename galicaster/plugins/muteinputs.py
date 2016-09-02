# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/muteinputs
#
# Copyright (c) 2016, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

from galicaster.core import context
from gi.repository import Pango, Gtk
from galicaster.core.core import PAGES
from galicaster.utils.resize import resize_button

conf = None
logger = None
recorder = None
dispatcher = None

def init():
    global conf, logger, recorder, dispatcher
    dispatcher = context.get_dispatcher()
    logger = context.get_logger()
    conf = context.get_conf()
    recorder = context.get_recorder()
    dispatcher.connect('init', manage_button)

def manage_button(element=None):
    recorder.enable_input()
    label = set_label(2,2,"Input status: ")
    label1 = set_label(0,1)
    context.get_mainwindow().insert_element(label,PAGES['REC'],"status_panel", "attach",left=0,top=4,width=1,height=1)
    context.get_mainwindow().insert_element(label1,PAGES['REC'],"status_panel", "attach", left=1,top=4,width=1,height=1)

    button = Gtk.ToggleButton()
    hbox = Gtk.Box()
    button.add(hbox)
    icon = Gtk.Image().new_from_icon_name("video-display",3)
    hbox.pack_start(icon,True,True,0)
    size = context.get_mainwindow().get_size()
    k1 = size[0] / 1920.0
    resize_button(button,size_image=k1*44,size_box=k1*46)

    to_disable = conf.get_list("muteinputs","bins")
    mute_type = conf.get_choice("muteinputs","mute_type", ["input", "preview"], "input")
    started_mute = conf.get_boolean("muteinputs","mute_on_startup")

    try:
        buttonREC = context.get_mainwindow().insert_element(button,PAGES['REC'],"buttonbox", "attach", left=6,top=0,width=1,height=1)
        buttonREC.connect("clicked",mute_inputs, mute_type, label1, to_disable)
    except Exception as exc:
        logger.error(exc)

    if started_mute:
        buttonREC.set_active(True)

    dispatcher.connect("recorder-ready", reload_mute, mute_type, label1, started_mute, button, to_disable)

    set_status_label(label1, mute_type)

def set_label(justify, halign, text=None):
    label = Gtk.Label(text)
    label.set_property("xalign", 1.0)
    label.set_property("xpad",10)
    label.set_property("wrap", True)
    label.set_property("justify",justify)
    label.set_property("ellipsize",3)
    label.set_property("halign",halign)

    size = context.get_mainwindow().get_size()
    k1 = size[0] / 1920.0
    label.set_use_markup(True)
    label.modify_font(Pango.FontDescription("Bold "+ str(int(k1*20))))

    return label


def set_status_label(label1, mute_type):
    global logger
    status = ""
    for elem in recorder.get_mute_status()[mute_type]:
        if recorder.get_mute_status()[mute_type][elem]:
            status+=" "+elem
    label1.set_text(status)
    logger.debug("Status label changed to: {}".format(status))

def mute_inputs(element, mute_type, label1, to_disable=[], button_status=None):
    global logger, recorder
    try:
        button_status = element.get_active()
    except Exception:
        pass

    if  button_status:
        if mute_type=="input":
            recorder.disable_input(to_disable)
        else:
            recorder.disable_preview(to_disable)
    else:
        if mute_type=="input":
            recorder.enable_input(to_disable)
        else:
            recorder.enable_preview(to_disable)

    set_status_label(label1, mute_type)

def reload_mute(element, mute_type, label1, started_mute, button, to_disable=[]):
    toggle = False
    if started_mute:
        toggle = True
    if not button.get_active() == toggle:
        button.set_active(toggle)
    else:
        mute_inputs(None, mute_type, label1, to_disable, button.get_active())
