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
from galicaster.classui.strip import StripUI
from galicaster.classui.profile import ProfileUI as ListProfile
from galicaster.utils.resize import relabel

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
        self.strip = StripUI(None,0)
	dbox.pack_start(self.strip,False,False,0)
	dbox.reorder_child(self.strip,0)
        
        release = dbuilder.get_object("release_label")
        release.set_label("Galicaster "+__version__)

        recorder = dbuilder.get_object("button1")        
        manager = dbuilder.get_object("button2")
        quit_button =  dbuilder.get_object("button3")
        shutdown_button =  dbuilder.get_object("button4")

        profile_button = dbuilder.get_object("profile_button")
        self.selected = dbuilder.get_object("selected_profile")
        self.update_selected_profile()
        self.handlers = {}
        
        #Connect signals
        dispatcher = context.get_dispatcher()
        dispatcher.connect("reload-profile", self.update_selected_profile)
        self.handlers[recorder] = recorder.connect("clicked", self.emit_signal, "change_mode", 0)
        self.handlers[manager] = manager.connect("clicked", self.emit_signal, "change_mode", 1)
        self.handlers[quit_button] = quit_button.connect("clicked", self.emit_signal, "galicaster-quit")
        self.handlers[shutdown_button] = shutdown_button.connect("clicked", self.emit_signal, "galicaster-shutdown")
        self.handlers[profile_button] = profile_button.connect("clicked", self.on_profile_button)
        
        for key, value in self.strip.handlers.iteritems():            
            self.handlers[key]=value

        conf = context.get_conf()
        quit_button.set_visible(conf.get_boolean("basic", "quit"))
        shutdown_button.set_visible(conf.get_boolean("basic", "shutdown"))
        self.pack_start(dbox, True, True, 0)


    def on_profile_button(self, origin):
        parent = self.get_toplevel()
        ListProfile(parent)

    def update_selected_profile(self, button = None):
        profile = context.get_conf().get_current_profile()
             
        if self.selected.get_text() != profile.name:
            self.selected.set_text("Profile: "+profile.name)          

    def emit_signal(origin, button, signal, value=None):
        dispatcher = context.get_dispatcher()
        if value != None:
            dispatcher.emit(signal, value)
        else:
            dispatcher.emit(signal)

    def get_all_buttons(self):
        return self.handlers.keys()

    def block_handlers(self, block):
        for key,value in self.handlers.iteritems():
            if block:
                key.handler_block(value)
            else:
                key.handler_unblock(value)

    def resize(self): 
        size = context.get_mainwindow().get_size()

        anchura = size[0]
        k = anchura / 1920.0

        builder= self.builder

        l1 = builder.get_object("reclabel")
        l2 = builder.get_object("mmlabel")
        l3 = builder.get_object("selected_profile")
        i1 = builder.get_object("recimage")
        i2 = builder.get_object("mmimage")
        b1 = builder.get_object("button1")
        b2 = builder.get_object("button2")
	relabel(l1,k*48,True)
        relabel(l2,k*48,True)  
        relabel(l3,k*26,True)  
        i1.set_pixel_size(int(k*120))
        i2.set_pixel_size(int(k*120))
        b1.set_property("width-request", int(anchura/3.5) )
        b2.set_property("width-request", int(anchura/3.5) )
        b1.set_property("height-request", int(anchura/3.5) )
        b2.set_property("height-request", int(anchura/3.5) )
   
        self.strip.resize()
