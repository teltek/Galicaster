# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/screensaver
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
Plugin to handle the Ubuntu 12 gnome-screensaver.

The screensaver will be disabled a TIME before the start of a scheduled recording, and as long as there is an active recording. The TIME is defined by classui.recorderui TIME_UPCOMING

In order for this to work correctly, any other screensaver tool must be disabled (i.e. power management, dpms, gnome-screensaver, etc.)

The screensaver will darken the screen after a given period of inactivity. This period can be configured using the 'screensaver' parameter in the conf.ini file, indicating the seconds of inactivity. By default 60 seconds.
"""

import os
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from galicaster.core import context

inactivity = '60' # seconds

def init():
    global inactivity
    dispatcher = context.get_dispatcher()
    inactivity = context.get_conf().get('screensaver', 'inactivity')
    dispatcher.connect('upcoming-recording', deactivate_and_poke)
    dispatcher.connect('starting-record', deactivate_and_poke)
    dispatcher.connect('restart-preview', configure)
    dispatcher.connect('galicaster-notify-quit', configure_quit)
    configure()

def get_screensaver_method(method):
    dbus_loop = DBusGMainLoop()
    session = dbus.SessionBus(mainloop=dbus_loop)
    bus_name = "org.gnome.ScreenSaver"
    object_path = "/org/gnome/ScreenSaver"
    screen_saver = session.get_object(bus_name, object_path)
    return screen_saver.get_dbus_method(method)

def activate_screensaver(signal=None):
    configure()

def deactivate_screensaver(signal=None):
    os.system('xset dpms 0 0 0')

def deactivate_and_poke(signal=None):
    deactivate_screensaver()
    poke_screen()

def configure(signal=None):
    global inactivity
    os.system('xset +dpms')
    os.system('xset dpms 0 0'+inactivity)

def configure_quit(signal=None):
    os.system('xset -dpms')

def poke_screen(signal=None):
    poke = get_screensaver_method('SimulateUserActivity')
    a = poke(
        reply_handler=replying,
        error_handler=replying) 

def replying(data=None):
    pass
