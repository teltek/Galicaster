# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/galicaster/utils/beep
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import gconf


GCONF_KEY = "/apps/gnome-screensaver/idle_activation_enabled"

def activate_screensaver():
    return gconf.client_get_default().set_bool(GCONF_KEY, True)

def deactivate_screensaver():
    return gconf.client_get_default().set_bool(GCONF_KEY, False)

def toggle_screensaver():
    new_value = not get_screensaver_activation_status()
    return gconf.client_get_default().set_bool(GCONF_KEY, new_value)

def get_screensaver_activation_status():
    return gconf.client_get_default().get_bool(GCONF_KEY)

