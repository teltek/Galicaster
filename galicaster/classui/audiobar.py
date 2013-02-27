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

from galicaster.core import context
from galicaster.classui import get_ui_path


class Vumeter(gtk.Table):

    __gtype_name__ = 'Vumeter'

    def __init__(self):
        gtk.Table.__init__(self)
        self.resize(4,110)
        self.set_homogeneous(True)
        self.mute = False
        self.vumeter=gtk.ProgressBar()
        #numbers
        minimum = gtk.Label("-100")
        maximum = gtk.Label("0dB")
        mark = gtk.Label("-10")
        sixty = gtk.Label("-60")
        thirty = gtk.Label("-30")

        labels= [minimum,sixty,thirty,mark,maximum]
        for label in labels:
            label.set_justify(gtk.JUSTIFY_CENTER)

        #marks
        mark100=gtk.VSeparator()
        mark60=gtk.VSeparator()
        mark30=gtk.VSeparator()
        mark10=gtk.VSeparator()
        mark0=gtk.VSeparator()

        # attach to widget
        self.attach(mark100,5,6,1,2,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)#-100
        self.attach(mark60,45,46,1,2,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)#-60
        self.attach(mark30,75,76,1,2,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)#-30
        self.attach(mark10,95,96,1,2,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)#-10
        self.attach(mark0,105,106,1,2,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)#0       
        
        self.attach(minimum,0,10,0,1,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)#-100
        self.attach(sixty,40,50,0,1,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)#-60
        self.attach(thirty,70,80,0,1,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)#-30
        self.attach(mark,90,100,0,1,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)#-10
        self.attach(maximum,100,110,0,1,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)#0

        self.attach(self.vumeter,5,105,2,4,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)

    def SetVumeter(self,element,data):
        value = self.scale_vumeter(data)
        self.vumeter.set_fraction(value)

    def ClearVumeter(self):
        self.vumeter.set_fraction(0)

    def scale_vumeter(self,data):
        conf = context.get_conf()
        dispatcher = context.get_dispatcher()
        minimum= float(conf.get('audio','min') or -80)

        if data == "Inf":
            valor = 0
        else:
            if data < -100:
                data = -100
            elif data > 0:
                data = 0
            valor=(data+100)/100.0

        if not self.mute:
            if data == "Inf" or data < minimum:
                dispatcher.emit("audio-mute")
                self.mute = True
        if self.mute and data > minimum+5.0:
            dispatcher.emit("audio-recovered")
            self.mute = False 

        return valor

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
        builder.connect_signals(self)
        self.vumeter=builder.get_object("vumeter")

    def GetVumeter(self):
        return self.vumeter.get_fraction()

    def SetVumeter(self,element,data):
        value = self.scale_vumeter(data)
        self.vumeter.set_fraction(value)

    def ClearVumeter(self):
        self.vumeter.set_fraction(0)

    def scale_vumeter(self,data):
        conf = context.get_conf()
        dispatcher = context.get_dispatcher()
        minimum= float(conf.get('audio','min'))

        if data == "Inf":
            valor = 0.0
        elif data < minimum:
            valor = 0.0
        elif data > 0:
            valor = 1.0
        else:
            valor = (data+100)/100

        if not self.vertical:
            if not self.mute:
                if data == "Inf" or data < -68:
                    dispatcher.emit("audio-mute")
                    self.mute = True
            if self.mute and valor > 0.0:                
                dispatcher.emit("audio-recovered")
                self.mute = False 
        return valor


    def resize(self,size):
        k = size[0] / 1920.0
        self.proportion = k
        
        if self.vertical:
            self.vumeter.set_property("width-request",int(k*50))
       
        return True


gobject.type_register(AudioBarClass)
