# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/cursor
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
TODO Add description
"""

import os
from galicaster.core import context

inactivity = '60'

def init():
    dispatcher = context.get_dispatcher()
    inactivity = context.get_conf().get('screensaver', 'inactivity')
        
    dispatcher.connect('upcoming-recording', deactivate_screensaver)
    dispatcher.connect('starting-record', deactivate_screensaver)
    dispatcher.connect('restart-preview', activate_screensaver)
    activate_screensaver()


def deactivate_screensaver(origin=None):
    os.system('xset s off')
    poke_screen()
            

def activate_screensaver(signal=None):
    os.system('xset s ' + inactivity)
    set_default_configuration()


def poke_screen(signal=None):
    os.system('dbus-send --session --dest=org.gnome.ScreenSaver --type=method_call  /org/gnome/ScreenSaver org.gnome.ScreenSaver.SimulateUserActivity')


def set_default_configuration():
    os.system('xset s blank')
    os.system('xset s expose')
