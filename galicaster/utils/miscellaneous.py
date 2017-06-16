# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/miscellaneous
#
# Copyright (c) 2016, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

import datetime

import os
import os.path
import traceback

from gi.repository import Gdk
from galicaster import __version__
from galicaster.core import context

conf = context.get_conf()

def get_screenshot_as_pixbuffer():
    """makes screenshot of the current root window, yields Gtk.Pixbuf"""
    window = Gdk.get_default_root_window()
    x, y, width, height = window.get_geometry()
    pb = Gdk.pixbuf_get_from_window(window, x, y, width, height)
    return pb


def get_footer():
    return "Galicaster "+ __version__ + "  -  " + conf.get_hostname()

def round_microseconds(date):
    fraction = date.microsecond / 1000000.0
    rounded = round(fraction, 0)

    if not rounded < 1:
        date = date + datetime.timedelta(seconds=1)
    return datetime.datetime(date.year, date.month, date.day, date.hour, date.minute, date.second)

def get_timezone():
    tzname = os.environ.get('TZ')
    if tzname:
        pass
    elif os.path.exists('/etc/timezone'):
        tzname = open('/etc/timezone').read().rstrip()

    return tzname

def count_files(folder):
    try:
        path, dirs, files = os.walk(folder).next()
        return len(files)
    except Exception as exc:
        print traceback.format_exc()
        print exc
