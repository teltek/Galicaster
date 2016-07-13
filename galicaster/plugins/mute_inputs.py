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

from gi.repository import Gtk
from galicaster.core.core import PAGES

def init():
    global conf, logger
    dispatcher = context.get_dispatcher()
    logger = context.get_logger()
    conf = context.get_conf()
    dispatcher.connect('init', manage_button)

def manage_button(element=None):
    global conf

    button = Gtk.Button()
    hbox = Gtk.Box()
    button.add(hbox)
    icon = Gtk.Image().new_from_icon_name("video-display",3)
    hbox.pack_start(icon,True,True,0)

    to_disable = conf.get_list("mute_inputs","bins")
    mute_type = conf.get("mute_inputs","mute_type")
    try:
        buttonREC = context.get_mainwindow().insert_button(button,PAGES['REC'],"buttonbox", left=6,top=0,width=1,height=1)
        buttonREC.connect("clicked",mute_inputs, mute_type, to_disable)
    except Exception as exc:
        logger.error(exc)


def mute_inputs(element, mute_type, to_disable=[]):
    recorder = context.get_recorder()
    bins_disable = []
    bins_enable = []
    if not to_disable:
        for bin in recorder.recorder.bins.keys():
            if recorder.recorder.mute_status[mute_type][bin]:
                bins_disable.append(bin)
            else:
                bins_enable.append(bin)
    else:
        for bin in to_disable:
            if recorder.recorder.mute_status[mute_type][bin]:
                bins_disable.append(bin)
            else:
                bins_enable.append(bin)


    if bins_disable:
        if mute_type == "input":
            recorder.disable_input(bins_disable)
        else:
            recorder.disable_preview(bins_disable)
    else:
        if mute_type == "input":
            recorder.enable_input(bins_enable)
        else:
            recorder.enable_preview(bins_enable)
