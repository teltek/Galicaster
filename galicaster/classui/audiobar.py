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


import gtk
import gobject
import os
from os import path
import math

from galicaster.core import context
from galicaster.classui import get_ui_path

class AudioBarClass(gtk.Box):
    """
    Status Information of Galicaster
    """

    __gtype_name__ = 'AudioBarClass'

    def __init__(self, vertical = False):
        gtk.Box.__init__(self)
	builder = gtk.Builder()
        self.mute = False
        self.vertical = vertical
        if vertical:
            guifile=get_ui_path('audiobarv.glade')
        else:
            guifile=get_ui_path('audiobar.glade')
        builder.add_from_file(guifile)
        self.bar = builder.get_object("audiobar")
        box = builder.get_object("vbox")
        if vertical:
            self.volume = gtk.VolumeButton()
            self.volume.set_value(0.5)
            box.pack_end(self.volume,False,True,0)
        #self.add(self.bar)  # FIXME configure box
        builder.connect_signals(self)
        self.vumeter=builder.get_object("vumeter")
        


    def GetVumeter(self):
        return self.vumeter.get_fraction()

    def SetVumeter(self,element,data):
        value = self.scale_vumeter(data)
        self.vumeter.set_fraction(value)

    def scale_vumeter(self,data):
        conf = context.get_conf()
        dispatcher = context.get_dispatcher()
        minimum= float(conf.get('audio','min'))
        maximum= float(conf.get('audio','max'))

        if data == "Inf":
            valor = 0.0
        elif data < minimum:
            valor = 0.0
        elif data > maximum:
            valor = 1.0
        else:
            valor = (data-minimum)/(maximum-minimum)

        if not self.vertical:
            if not self.mute:
                if data == "Inf" or data < -68:
                    dispatcher.emit("audio-mute")
                    self.mute = True
            if self.mute and valor > 0.0:                
                dispatcher.emit("audio-recovered")
                self.mute = False 
        return valor


    def resize(self,size): # FIXME change alignments and 
        altura = size[1]
        anchura = size[0]

        k = anchura / 1920.0 # we assume 16:9 or 4:3?
        self.proportion = k
        
        def relabel(label,size,bold):           
            if bold:
                modification = "bold "+str(size)
            else:
                modification = str(size)
            label.modify_font(pango.FontDescription(modification))

        if self.vertical:
            self.vumeter.set_property("width-request",int(k*50))
       
        return True


gobject.type_register(AudioBarClass)
