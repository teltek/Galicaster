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
        box = builder.get_object("vbox")
        self.volume = Gtk.VolumeButton()
        self.volume.set_value(0.5)
        box.pack_end(self.volume,False,True,0)
        builder.connect_signals(self)
        self.vumeter=builder.get_object("vumeter")
        self.rangeVum = 40

    def GetVumeter(self):
        return self.vumeter.get_fraction()

    def SetVumeter(self,element,data):
        value = self.scale_vumeter(data)
        self.vumeter.set_fraction(value)

    def ClearVumeter(self):
        self.vumeter.set_fraction(0)

    def scale_vumeter(self,data):

        if data == "Inf":
            data = -100
        elif data < -self.rangeVum:
            data = -self.rangeVum
        elif data > 0:
            data = 0
        valor = (data+self.rangeVum)/float(self.rangeVum)
        return valor

    def resize(self,size):
        k = size[0] / 1920.0
        self.proportion = k
        self.vumeter.set_property("width-request",int(k*50))
        return True


GObject.type_register(AudioBarClass)
