# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/classui/strip
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

from galicaster.core import context
from galicaster.classui import get_ui_path, get_image_path
from galicaster.classui.about import GCAboutDialog

class StripUI(gtk.Box):
    """
    GUI for the Welcoming - Distribution Screen
    """
    __gtype_name__ = 'StripUI'
    
    def __init__(self, back_page ):  
        gtk.Box.__init__(self)

        dispatcher = context.get_dispatcher()
        builder = gtk.Builder()
        builder.add_from_file(get_ui_path('strip.glade'))
        self.builder = builder
        self.strip = builder.get_object("stripbox")
        button = builder.get_object("previousbutton")
        button.connect("clicked", self.emit_signal, "change-mode", back_page)
        about = builder.get_object("aboutevent")
        about.connect("button-press-event", self.show_about_dialog)

        self.pack_start(self.strip,True,True,0)

    def emit_signal(origin, button, signal, value):
        dispatcher = context.get_dispatcher()
        dispatcher.emit(signal, value)

    def show_about_dialog(self, origin, button):
        dialog=GCAboutDialog()

    def resize(self): 
        size = context.get_mainwindow().get_size()
        altura = size[1]
        anchura = size[0]
        k = anchura / 1920.0

        pixbuf = gtk.gdk.pixbuf_new_from_file(get_image_path('logo.svg'))    
        pixbuf = pixbuf.scale_simple(
            int(pixbuf.get_width()*k),
            int(pixbuf.get_height()*k),
            gtk.gdk.INTERP_BILINEAR)
        align2 = self.builder.get_object("top_align")
        
        logo2 = self.builder.get_object("logo2")

        logo2.set_from_pixbuf(pixbuf)
        align2.set_padding(int(k*51),int(k*30),0,0)

        for name in ["previousbutton"]:
            button = self.builder.get_object(name)
            button.set_property("width-request", int(k*70) )
            button.set_property("height-request", int(k*70) )
            
            image = button.get_children()
            if type(image[0]) == gtk.Image:
                image[0].set_pixel_size(int(k*56))
