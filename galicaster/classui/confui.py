# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/classui/confui
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
from os import path

from galicaster.core import context
from galicaster.classui import get_ui_path


properties ={"Repository Folder":"repository", "MP default name":"zip", "Pipeline":"pipe", "Host":"host", "Username":"username",
             "Password":"password", "Workflow":"workflow", "Player":"player", "Recorder":"recorder", "Codec" : "codec",
             
             
             }

basic = [ "repository",  "codec"]
ingest = [ "host", "username", "password", "workflow" ] # FIXME take names from INI keys
screen = [ "player", "recorder"]
flavors = [ "presenter", "presentation", 
"other"]
devices = [ "vga2usb", "hauppauge", "v4l2", "pulse", "rtpvideo", "rtpaudio"]
track = [ "device", "location", "flavor", "file"]
nums = ["1","2","3","4","5","6"]

class ConfUI(gtk.Widget):
    """
    Handle a pop up configuration editor with realtime screen shifter
    """
    __gtype_name__ = 'ConfUI'
    
    def __init__(self,package = None, parent = None):
        self.gui = gtk.Builder()
        self.gui.add_from_file(get_ui_path('conf.glade'))

        self.conf=context.get_conf()
        
        dialog = self.gui.get_object("confdialog")
        if parent != None:
            dialog.set_transient_for(parent.get_toplevel())
        self.shifter1 = self.gui.get_object('playershift') 
        self.shifter2 = self.gui.get_object('recordshift') 
        self.shifter1.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.shifter1.connect("button-press-event",self.on_toggle) # CHANGE method name
        self.shifter2.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.shifter2.connect("button-press-event",self.on_toggle) # CHANGE method name
        if self.conf.get("screen","player") == "presentation":
            self.on_toggle(self.shifter1, None)
        if self.conf.get("screen","recorder") == "presentation":
            self.on_toggle(self.shifter2, None)
 
        self.populate_conf()
        response = dialog.run()        
        if response > 1: # FIXME, need a main
            print "Galicaster Configuration Update"
            self.update_conf()
        elif response == 1:
            print "Galicaster Configuration Update"# FIXME just apply changes dont close
            self.update_conf()
        else:       
            print "Cancel Configuration"
        dialog.destroy()

    def populate_conf(self): # FIXME, look for another way to do it, scalable
        for a in basic:
            entry = self.gui.get_object(a)
            if type(entry) is gtk.FileChooserButton:
                print self.conf.get("basic",a)
                entry.set_current_folder(self.conf.get("basic",a))                            
            else:
                entry.set_text(self.conf.get("basic",a))
        for a in ingest:
            entry = self.gui.get_object(a)     
            entry.set_text(self.conf.get("ingest",a))

        for num in nums:
            for a in track:
                entry = self.gui.get_object(a+num)
                if a=="device":
                    self.set_model_from_list(entry,devices)
                    entry.set_active(devices.index(self.conf.get("track" + num, a)))

                elif a=="flavor":
                    self.set_model_from_list(entry,flavors)
                    entry.set_active(flavors.index(self.conf.get("track" + num, a)))
                else:
                    entry.set_text(self.conf.get("track" + num, a))    
            if self.conf.get("track" + num, "active")=="True": #FIXME treat as boolean
                self.gui.get_object("checkbutton"+num).set_active(True)

    def set_model_from_list (self, cb, items):
        """Setup a ComboBox based on a list of strings."""           
        model = gtk.ListStore(str)
        for i in items:
            model.append([i])
        cb.set_model(model)
        cell = gtk.CellRendererText()
        cb.pack_start(cell, True)
        cb.add_attribute(cell, 'text', 0)


    def update_conf(self):
        print "Updating configuration"
        for a in basic:
            entry = self.gui.get_object(a)
            if type(entry) is gtk.FileChooserButton:
                self.conf.set("basic",a,entry.get_current_folder())
            else:
                self.conf.set("basic",a,entry.get_text())
        for a in ingest:
            entry = self.gui.get_object(a)
            self.conf.set("ingest",a,entry.get_text())

        for num in nums:
            for a in track:
                entry = self.gui.get_object(a+num)
                if type(entry) is gtk.ComboBox:
                    self.conf.set("track"+num, a, entry.get_active_text())
                else:
                    self.conf.set("track"+num, a, entry.get_text())
            if self.gui.get_object("checkbutton"+num).get_active():
                self.conf.set("track"+num,"active","True")
            else:
                self.conf.set("track"+num,"active","False")      

        entry = self.gui.get_object("playershift")
        button = entry.get_children()[0].get_children()[0].get_label()
        self.conf.set("screen","player",button.lower())
        entry = self.gui.get_object("recordshift")
        button = entry.get_children()[0].get_children()[0].get_label()
        self.conf.set("screen","recorder",button.lower())
        self.conf.update()


    def on_toggle(self, button, signal): # FIXME connect to Conf
        """
        Toggle preferences on shifting screen
        """
        box = button.get_children()[0]
        box.reorder_child(box.get_children()[1],1)
        box.reorder_child(box.get_children()[0],2)

    def shift_videos(self,signal): # Fixme, connect to Conf
        """
        Shifts videos
        """
        if self.function == self.GC_RECORDER :
           self.on_toggle(self.shifter2, None)  
           self.update_conf() #FIXME Sure??
        elif self.function == self.GC_PLAYER :
           self.on_toggle(self.shifter1, None)
           self.update_conf() #FIXME Sure??

gobject.type_register(ConfUI)
