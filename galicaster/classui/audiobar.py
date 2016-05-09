# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/classui/audiobar
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


from gi.repository import Gtk, Gdk
from gi.repository import GObject
from gi.repository import Pango

from galicaster.core import context
from galicaster.classui import get_ui_path

class AudioBarClass(Gtk.Box):
    """
    Status Information of Galicaster
    """

    __gtype_name__ = 'AudioBarClass'

    def __init__(self, vertical = False):
        Gtk.Box.__init__(self)
	builder = Gtk.Builder()
        guifile=get_ui_path('audiobarv.glade')
        builder.add_from_file(guifile)
        self.bar = builder.get_object("audiobar")
        self.label_channel_players = builder.get_object("label_channels_player")
        self.vumeterL = builder.get_object("progressbarL")
        self.vumeterR = builder.get_object("progressbarR")
        self.rangeVum = 50
        self.stereo = True

    def get_vumeter(self):
        return self.vumeterL.get_fraction()

    def set_vumeter(self,element,data, data2, stereo):
        value = self.scale_data(data)
        value2 = self.scale_data(data2)
        self.vumeterL.set_fraction(value)
        self.vumeterR.set_fraction(value2)

        if not stereo and self.stereo:
            self.stereo = False
            self.label_channels_player.set_text("Mono")
        elif stereo and not self.stereo:
            self.stereo = True
            self.label_channels_player.set_text("Stereo")        

    def clear_vumeter(self):
        self.vumeterL.set_fraction(0)
        self.vumeterR.set_fraction(0)

    def scale_data(self,data):
        if data == "Inf":
            data = -100
        elif data < -self.rangeVum:
            data = -self.rangeVum
        elif data > 0:
            data = 0
        valor = (data+self.rangeVum)/float(self.rangeVum)
        return valor

    def resize(self,size):
        return True


GObject.type_register(AudioBarClass)
