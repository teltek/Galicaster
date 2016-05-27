# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/appeareance
#
# Copyright (c) 2016, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""

"""

from gi.repository import Gdk

from galicaster.core import context
from galicaster.utils.systemcalls import write_dconf_settings


def init():
    global logger, hidecursor, settings, default_settings
    dispatcher = context.get_dispatcher()
    logger = context.get_logger()
    conf = context.get_conf()
            
    dispatcher.connect('init', configure_init)
    dispatcher.connect('quit', configure_quit)

    settings = conf.get_json('appeareance', 'settings')
    default_settings = conf.get_json('appeareance', 'defaultsettings')
    hidecursor = conf.get_boolean('appeareance', 'hidecursor')

        
def configure_init(signal=None):
    global logger, hidecursor, settings
    logger.info("On init: set appeareance settings")
    write_dconf_settings(settings, logger, logaserror=False)
    
    if hidecursor:
        hide_cursor()
    else:
        show_cursor()


def configure_quit(signal=None):
    global logger, hidecursor, default_settings
    logger.info("On exit: set default appeareance settings")
    write_dconf_settings(default_settings, logger, logaserror=False)
    if hidecursor:
        show_cursor()


# CURSOR
def hide_cursor():
    logger.info("Hide cursor")
    blank_cursor = Gdk.Cursor(Gdk.CursorType.BLANK_CURSOR)
    window = Gdk.get_default_root_window()
    window.set_cursor(blank_cursor)

def show_cursor(emiter=None):
    logger.info("Show cursor")
    arrow_cursor = Gdk.Cursor(Gdk.CursorType.ARROW)
    window = Gdk.get_default_root_window()
    window.set_cursor(arrow_cursor) 

