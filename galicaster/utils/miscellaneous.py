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

from gi.repository import Gdk

def get_screenshot_as_pixbuffer():
    """makes screenshot of the current root window, yields Gtk.Pixbuf"""
    window = Gdk.get_default_root_window()
    x, y, width, height = window.get_geometry()
    pb = Gdk.pixbuf_get_from_window(window, x, y, width, height)
    return pb


