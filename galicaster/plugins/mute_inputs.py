# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/mute_inputs
#
# Copyright (c) 2016, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

from galicaster.core import context
from gi.repository import Pango

from gi.repository import Gtk
from galicaster.core.core import PAGES

def init():
    global conf, logger, recorder, dispatcher
    dispatcher = context.get_dispatcher()
    logger = context.get_logger()
    conf = context.get_conf()
    recorder = context.get_recorder()
    dispatcher.connect('init', manage_button)

def manage_button(element=None):
    global conf, recorder, dispatcher

    label = set_label(2,2,"Input status: ")
    label1 = set_label(0,1)
    context.get_mainwindow().insert_button(label,PAGES['REC'],"status_panel", left=0,top=4,width=1,height=1)
    context.get_mainwindow().insert_button(label1,PAGES['REC'],"status_panel", left=1,top=4,width=1,height=1)

    button = Gtk.Button()
    hbox = Gtk.Box()
    button.add(hbox)
    icon = Gtk.Image().new_from_icon_name("video-display",3)
    hbox.pack_start(icon,True,True,0)

    to_disable = conf.get_list("mute_inputs","bins")
    mute_type = conf.get_choice("mute_inputs","mute_type", ["input", "source"], "input")
    started_mute = conf.get_boolean("mute_inputs","mute_on_startup")
    if started_mute:
        mute_inputs(None, mute_type, label1, to_disable)
        dispatcher.connect("recorder-ready", mute_inputs, mute_type, label1,  to_disable)
    else:
        dispatcher.connect("recorder-ready", mute_inputs, mute_type, label1)

    try:
        buttonREC = context.get_mainwindow().insert_button(button,PAGES['REC'],"buttonbox", left=6,top=0,width=1,height=1)
        buttonREC.connect("clicked",mute_inputs, mute_type, label1, to_disable)
    except Exception as exc:
        logger.error(exc)

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

def mute_inputs(element, mute_type, label1, to_disable=[]):
    global logger, recorder
    bins_disable = []
    bins_enable = []
    if not to_disable:
        for bin in recorder.get_mute_status().keys():
            try:
                if recorder.get_mute_status()[mute_type][bin]:
                    bins_disable.append(bin)
                else:
                    bins_enable.append(bin)
            except Exception as exc:
                logger.warning("Bin: "+bin+" not loaded in this profile")
    else:
        for bin in to_disable:
            try:
                if recorder.get_mute_status()[mute_type][bin]:
                    bins_disable.append(bin)
                else:
                    bins_enable.append(bin)
            except Exception as exc:
                logger.warning("Bin: "+bin+" not loaded in this profile")

    if bins_disable:
        if mute_type == "input":
            recorder.disable_input(bins_disable)
        else:
            recorder.disable_preview(bins_disable)
    if bins_enable:
        if mute_type == "input":
            recorder.enable_input(bins_enable)
        else:
            recorder.enable_preview(bins_enable)

    set_status_label(label1, mute_type)
