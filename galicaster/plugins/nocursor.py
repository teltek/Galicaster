# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/nocursor
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
"""

from gi.repository import Gtk
from galicaster.core import context

def init():
    dispatcher = context.get_dispatcher()
    dispatcher.connect('galicaster-notify-quit', show_cursor)
    hide_cursor()
            

def hide_cursor(): 
    pixmap = Gdk.Pixmap(None, 1, 1, 1)
    color = Gdk.Color()
    invisible = Gdk.Cursor.new(pixmap, pixmap, color, color, 0, 0)
    window=Gdk.get_default_root_window()
    window.set_cursor(invisible)

def show_cursor(emiter=None):
    window=Gdk.get_default_root_window()
    window.set_cursor(Gdk.Cursor.new(Gdk.CursorType.ARROW)) 
