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
Plugin to handle the Ubuntu 16 screensaver.

The screensaver will be disabled a TIME before the start of a scheduled recording, and as long as there is an active recording. The TIME is defined by classui.recorderui TIME_UPCOMING

In order for this to work correctly, any other screensaver tool must be disabled (i.e. power management, dpms, gnome-screensaver, etc.)

The screensaver will darken the screen after a given period of inactivity. This period can be configured using the 'screensaver' parameter in the conf.ini file, indicating the seconds of inactivity. By default 60 seconds.
"""

import os
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from galicaster.core import context
from galicaster.utils.systemcalls import execute
from galicaster.utils.systemcalls import write_dconf_settings

inactivity = None
logger = None
power_settings = None
default_power_settings = None

def init():
    global inactivity, logger, power_settings, default_power_settings
    dispatcher = context.get_dispatcher()
    logger = context.get_logger()
    conf = context.get_conf()

    inactivity_val = conf.get('screensaver', 'inactivity')
    try:
        inactivity = int(inactivity_val)
    except Exception as exc:
        raise Exception("Error trying to convert inactivity value to integer: {}".format(exc))

    dispatcher.connect('recorder-upcoming-event', deactivate_and_poke)
    dispatcher.connect('recorder-starting', deactivate_and_poke)
    dispatcher.connect('recorder-stopped', activate_and_poke)
    dispatcher.connect('quit', configure_quit)

    power_settings = conf.get_json('screensaver', 'powersettings')
    default_power_settings = conf.get_json('screensaver', 'defaultpowersettings')
    activate_screensaver()


def activate_and_poke(signal=None, mp=None):
    global logger
    poke_screen()
#    activate_screensaver()

    standby_time = inactivity
    suspend_time = inactivity + 5
    off_time = inactivity + 10
    execute(["xset", "dpms", str(standby_time), str(suspend_time), str(off_time)], logger)
    logger.debug("Activate screensaver")

def deactivate_and_poke(signal=None, mp=None):
    global logger
    deactivate_screensaver()
    poke_screen()
    logger.debug("Deactivate screensaver")

def deactivate_screensaver(signal=None):
    global logger
    execute(['xset', 'dpms', '0', '0', '0'], logger)
#    execute(['xset', '-dpms'], logger)

def activate_screensaver(signal=None, mp=None):
    global inactivity, logger, power_settings
    logger.info("Activate screensaver: set power settings and activate power saving mode for {} s".format(inactivity))

    standby_time = inactivity
    suspend_time = inactivity + 5
    off_time = inactivity + 10

    write_dconf_settings(power_settings, logger, logaserror=False)
    execute(["xset", "s", "off"], logger)
    execute(["xset", "+dpms"], logger)
    execute(["xset", "dpms", str(standby_time), str(suspend_time), str(off_time)], logger)
    os.system("dconf write /org/gnome/desktop/session/idle-delay 'uint32 0'")


def configure_quit(signal=None):
    global default_power_settings, logger
    logger.info("On exit: deactivate screensaver and set default power settings")

    write_dconf_settings(default_power_settings, logger, logaserror=False)
    execute(['xset', '-dpms'], logger)

def get_screensaver_method(method):
    dbus_loop = DBusGMainLoop()
    session = dbus.SessionBus(mainloop=dbus_loop)
    bus_name = "org.gnome.ScreenSaver"
    object_path = "/org/gnome/ScreenSaver"
    screen_saver = session.get_object(bus_name, object_path)
    return screen_saver.get_dbus_method(method)


def poke_screen(signal=None):
    global logger
    logger.info("Simulate user activity")
    poke = get_screensaver_method('SimulateUserActivity')
    poke(
        reply_handler=replying,
        error_handler=replying)
    execute(['xset','dpms','force','on'], logger)

def replying(data=None):
    pass
