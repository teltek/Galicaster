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
import pango

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
        self.rangeVum = 40
	    #numbers
        label0 = gtk.Label("0 dB")
        label1 = gtk.Label("-3")
        label2 = gtk.Label("-6")
        label3 = gtk.Label("-12")
        label4 = gtk.Label("-24")
        label5 = gtk.Label("-40")	
	
        # set number's colour
	self.modify_widget_fgcolor (label0, gtk.gdk.color_parse("#D9211D")) # Red
	self.modify_widget_fgcolor (label1, gtk.gdk.color_parse("#D95E1D")) # Orange
	self.modify_widget_fgcolor (label2, gtk.gdk.color_parse("#D95E1D")) # Orange
	self.modify_widget_fgcolor (label3, gtk.gdk.color_parse("#068629")) # Green
	self.modify_widget_fgcolor (label4, gtk.gdk.color_parse("#068629")) # Green
	self.modify_widget_fgcolor (label5, gtk.gdk.color_parse("#068629")) # Green
    	
        labels= [label0,label1,label2,label3,label4,label5]
        for label in labels:
            label.set_justify(gtk.JUSTIFY_CENTER)
            alist = pango.AttrList()
            font=pango.FontDescription("bold")
            attr=pango.AttrFontDesc(font,0,-1)
            alist.insert(attr)
            label.set_attributes(alist)

        # set number's position
        self.attach(label0,100,110,0,1,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)	#0
        self.attach(label1,92,102,0,1,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)	#-3
        self.attach(label2,85,95,0,1,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)	#-6
        self.attach(label3,70,80,0,1,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)	#-12
        self.attach(label4,40,50,0,1,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)	#-24
        self.attach(label5,0,10,0,1,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)	#-40

        #marks
        mark0=gtk.VSeparator()
        mark1=gtk.VSeparator()
        mark2=gtk.VSeparator()
        mark3=gtk.VSeparator()
        mark4=gtk.VSeparator()
        mark5=gtk.VSeparator()

        # attach marks to widget   
        self.attach(mark0,105,106,1,2,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)	#0dB
        self.attach(mark1,97,98,1,2,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)	#-3
        self.attach(mark2,90,91,1,2,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)	#-6
        self.attach(mark3,75,76,1,2,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)	#-12
        self.attach(mark4,45,46,1,2,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)	#-24
        self.attach(mark5,5,6,1,2,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)		#-40

        self.attach(self.vumeter,5,105,2,4,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)

    def SetVumeter(self,element,data):
        value = self.scale_vumeter(data)
        self.vumeter.set_fraction(value)

    def ClearVumeter(self):
        self.vumeter.set_fraction(0)

    def scale_vumeter(self,data):
	
        data_aux = data
        conf = context.get_conf()
        dispatcher = context.get_dispatcher()
        minimum= float(conf.get('audio','min') or -70)

        if data == "Inf":
            valor = 0
        else:
            if data < -self.rangeVum:
                data = -self.rangeVum
            elif data > 0:
                data = 0
	    valor=(data+self.rangeVum)/float(self.rangeVum)
        if not self.mute:
	    if data_aux == "Inf" or data_aux < minimum:
                dispatcher.emit("audio-mute")
                self.mute = True
	if self.mute and data_aux > minimum+5.0:
            dispatcher.emit("audio-recovered")
            self.mute = False 
        return valor


    def modify_widget_fgcolor(self, widget, color):
        widget.modify_fg(gtk.STATE_NORMAL, color)
        widget.modify_fg(gtk.STATE_ACTIVE, color)
        widget.modify_fg(gtk.STATE_PRELIGHT, color)
        widget.modify_fg(gtk.STATE_SELECTED, color)

class AudioBarClass(gtk.Box):
    """
    Status Information of Galicaster
    """

    __gtype_name__ = 'AudioBarClass'

    def __init__(self, vertical = False):
        gtk.Box.__init__(self)
	builder = gtk.Builder()
        guifile=get_ui_path('audiobarv.glade')
        builder.add_from_file(guifile)
        self.bar = builder.get_object("audiobar")
        box = builder.get_object("vbox")
        self.volume = gtk.VolumeButton()
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


gobject.type_register(AudioBarClass)
