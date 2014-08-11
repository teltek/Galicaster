# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/shortcuts
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import gtk
from galicaster.core import context


def init():
    window = context.get_mainwindow()
    window.add_events(gtk.gdk.KEY_PRESS_MASK)
    window.connect('key-press-event', check_key)


def is_the_key(key, event):
    return ((event.state & gtk.gdk.CONTROL_MASK)  and
            (event.keyval in [gtk.gdk.keyval_from_name(key), gtk.gdk.keyval_from_name(key.upper())]))

def check_key(source, event):
    """
    Filter Ctrl combinations for quit,restart and configuration 
    """
    dispatcher = context.get_dispatcher()
    window = context.get_mainwindow()
    if ((event.state & gtk.gdk.SHIFT_MASK and event.state & gtk.gdk.CONTROL_MASK) 
        and event.state & gtk.gdk.MOD2_MASK and
        (event.keyval in [gtk.gdk.keyval_from_name('q'), gtk.gdk.keyval_from_name('Q')])):
        
        if not context.get_recorder.is_recording():
            dispatcher.emit('galicaster-quit')

    if ((event.state & gtk.gdk.CONTROL_MASK)  and
        event.keyval == gtk.gdk.keyval_from_name('Return') ):
        window.toggle_fullscreen(None)
                
    return True  
    
