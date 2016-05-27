# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/shutdown
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
Add shutdown and close session capabilities to the application
A button appears on the Welcome area
"""

import dbus
from dbus.bus import BusConnection
from dbus.mainloop.glib import DBusGMainLoop

def get_dbus_method(method_name):
    dbus_loop = DBusGMainLoop()
    connection = BusConnection(mainloop=dbus_loop)
    bus_name = "org.gnome.SessionManager"
    object_path = "/org/gnome/SessionManager"
    session_object = connection.get_object(bus_name,object_path)
    interface = dbus.Interface(session_object, bus_name)
    method = interface.get_dbus_method(method_name)
    return method

def shutdown(signal=None):
    poweroff = get_dbus_method('RequestShutdown')
    poweroff(reply_handler=None, error_handler=None) 
    
def close_session(signal=None): # Not used but usable
    logout = get_dbus_method('Logout')
    logout(2,reply_handler=None, error_handler=None) 
