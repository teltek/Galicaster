# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/ui/distribui
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


from os import path
import gtk
import pango

from galicaster.core import context
from galicaster.classui import get_ui_path, get_image_path
from galicaster import __version__

class DistribUI(gtk.Box):
    """
    GUI for the Welcoming - Distribution Screen
    """
    __gtype_name__ = 'DistribUI'
    
    def __init__(self):  
        gtk.Box.__init__(self)
        dbuilder= gtk.Builder()
        dbuilder.add_from_file(get_ui_path('distrib.glade'))
        self.builder = dbuilder
        dbox = dbuilder.get_object("distbox")
        release = dbuilder.get_object("release_label")
        release.set_label("Galicaster "+__version__)
        br = dbuilder.get_object("button1")
        bm = dbuilder.get_object("button2")
        bq =  dbuilder.get_object("button3")
        dispatcher = context.get_dispatcher()
        br.connect("clicked", self.emit_signal, "change_mode",0 )
        bm.connect("clicked", self.emit_signal, "change_mode",1 )
        bq.connect("clicked", self.emit_signal, "galicaster-quit")
        about = dbuilder.get_object("aboutevent")
        about.connect("button-press-event", self.emit_signal2,"show-about")

        conf = context.get_conf()

        if conf.get("screen", "quit") not in ["False","false","None","none"]:
            bq.set_visible(True)

        self.pack_start(dbox,True,True,0)

    def emit_signal(origin, button, signal, value=None):

        dispatcher = context.get_dispatcher()
        if value != None:
            dispatcher.emit(signal,value)
        else:
            dispatcher.emit(signal)

    def emit_signal2(origin, button, event, signal):
        dispatcher = context.get_dispatcher()
        dispatcher.emit(signal)

    def resize(self,size): 
        altura = size[1]
        anchura = size[0]
        k = anchura / 1920.0

        def relabel(label,size,bold):           
            if bold:
                modification = "bold "+str(size)
            else:
                modification = str(size)
            label.modify_font(pango.FontDescription(modification))
   

        builder= self.builder
        logos = builder.get_object("logo_align")
        logos.set_padding(int(k*56),int(k*45),int(k*120),int(k*120))
        disal = builder.get_object("dis_align")
        disal.set_padding(int(k*25),int(k*25),int(k*50),int(k*50))

        l1 = builder.get_object("reclabel")
        l2 = builder.get_object("mmlabel")
        i1 = builder.get_object("recimage")
        i2 = builder.get_object("mmimage")
        b1 = builder.get_object("button1")
        b2 = builder.get_object("button2")
	relabel(l1,k*48,True)
        relabel(l2,k*48,True)  
        i1.set_pixel_size(int(k*120))
        i2.set_pixel_size(int(k*120))
        b1.set_property("width-request", int(k*500) )
        b2.set_property("width-request", int(k*500) )
        b1.set_property("height-request", int(k*500) )
        b2.set_property("height-request", int(k*500) )
   
        lclass = builder.get_object("logo2")
        lcompany = builder.get_object("logo1")
        iclass=gtk.gdk.pixbuf_new_from_file(get_image_path("logo"+str(anchura)+".png"))
        icompany=gtk.gdk.pixbuf_new_from_file(get_image_path("teltek"+str(anchura)+".png"))
        lclass.set_from_pixbuf(iclass)
        lcompany.set_from_pixbuf(icompany)
