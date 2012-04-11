# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/dbusservice
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
Use dbus to only limit a single instance running of your app.
"""

import dbus, dbus.glib, dbus.service

class DBusService(dbus.service.Object):
    def __init__(self, app):

        if dbus.SessionBus().request_name("es.teltek.Galicaster") != dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER:
            method = dbus.SessionBus().get_object("es.teltek.Galicaster", "/es/teltek/Galicaster").get_dbus_method("show_window")
            method()
            raise SystemError("Galicaster already running")
        else:
            self.app = app
            bus_name = dbus.service.BusName('es.teltek.Galicaster', bus = dbus.SessionBus())
            dbus.service.Object.__init__(self, bus_name, '/es/teltek/Galicaster')

    @dbus.service.method(dbus_interface='es.teltek.Galicaster')
    def show_window(self):
        # TODO Parece no cojer el foco.
        self.app.window.present()
