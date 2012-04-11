# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/core/core
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


import pygtk
pygtk.require('2.0')


import os
import sys
import types 
import shutil 
import glib
import logging

import gobject
gobject.threads_init()
import pygst
pygst.require('0.10')
import gst
import gst.interfaces
import gtk
import pango
gtk.gdk.threads_init() 

from galicaster import __version__
from galicaster.classui import message
from galicaster.core import context
from galicaster.classui.recorderui import RecorderClassUI
from galicaster.classui.recorderui import GC_RECORDING
from galicaster.classui.listing import ListingClassUI
from galicaster.classui.playerui import PlayerClassUI
from galicaster.classui.confui import ConfUI
from galicaster.classui.distrib import DistribUI
from galicaster.classui.strip import StripUI
from galicaster.classui.about import AboutMsg

from galicaster.scheduler.scheduler import Scheduler
from galicaster.mediapackage import deserializer
from galicaster.classui import openfile
from galicaster import plugins


basic = [ "repository", "zip", "pipe"]
ingest = [ "host", "username", "password", "workflow" ]
screen = [ "player"]

log = logging.getLogger()

REC= 0
PLA= 2
MMA= 1
DIS= 3
PIN= 4 

class Class():

    def __init__(self):
        """
        Core class
        """
        self.window = context.get_mainwindow()

        # signals and location
        self.conf = context.get_conf()
        self.dispatcher = context.get_dispatcher()

        self.modules = []
        self.modules.append("recorder")
             
        if self.conf.get("basic","admin") == "True":
            self.modules.append("media manager")
            self.modules.append("player")

        if self.conf.get("ingest", "active") == "True":
            self.modules.append("scheduler")

        if self.conf.get("basic", "pin") == "True":  
            self.modules.append("pin")
        self.load_modules()


    def load_modules(self):

        self.nbox = gtk.Notebook()
        self.nbox.set_show_tabs(False)
        self.window.add(self.nbox)

        self.resize = self.light_resize
        self.check_key = self.light_check_key
        self.function = REC

        # Recorder it's allways loaded
        # Recorder
        self.recorder = RecorderClassUI()
        self.nbox.insert_page(self.recorder, gtk.Label("REC"), REC) 
        self.dispatcher.connect("start-record", self.recorder.on_scheduled_start)
        self.dispatcher.connect("stop-record", self.recorder.on_scheduled_stop)

        if "scheduler" in self.modules:        
            self.scheduler = Scheduler()

        if "media manager" in self.modules:

            self.resize = self.regular_resize
            self.check_key = self.light_check_key

            # Distribution
            self.distribution = DistribUI()
            lbox3 = gtk.VBox()
            lbox3.pack_start(self.distribution,True,True,0)
            self.nbox.insert_page(lbox3, gtk.Label("DISTRIBUTION"), DIS) 

            # Media Manager
            self.listing  = ListingClassUI()
            # StripMM
            self.strip1 = StripUI(DIS)
            lbox = gtk.VBox()
            lbox.pack_start(self.strip1,False,False,0)
            lbox.pack_start(self.listing,True,True,0)

            self.dispatcher.connect("change-mode", self.change_mode_by_signal)
            self.dispatcher.connect("play-list", self.play_mp)
            self.nbox.insert_page(lbox, gtk.Label("LIST"), MMA) #FIXME add the listing object itself
        
        if "player" in self.modules:
            self.player = PlayerClassUI()
            # StripPlayer
            self.strip2 = StripUI(MMA)
            lbox2 = gtk.VBox()
            lbox2.pack_start(self.strip2,False,False,0)
            lbox2.pack_start(self.player,True,True,0)
            self.nbox.insert_page(lbox2, gtk.Label("PLAYER"), PLA)

        self.window.start()
        self.resize(0)
        self.is_fullscreen=True
       
        self.window.add_events(gtk.gdk.KEY_PRESS_MASK)

        self.window.connect("key-press-event",self.check_key)

        if "recorder" and "media manager" in self.modules:            
            self.nbox.set_current_page(DIS)
        else:
            self.nbox.set_current_page(REC)
            self.recorder.block()  


        plugins.init()

################################# KEYS AND CURSOR #########################

    def light_check_key(self,source,event): # TODO

        """
        Filter Ctrl combinations for quit,restart and configuration 
        """
        if ((event.state & gtk.gdk.SHIFT_MASK and event.state & gtk.gdk.CONTROL_MASK) 
            and event.state & gtk.gdk.MOD2_MASK and
            (event.keyval in [gtk.gdk.keyval_from_name('q'), gtk.gdk.keyval_from_name('Q')])):
            if self.recorder.status != GC_RECORDING:            
                self.dispatcher.emit('galicaster-quit')

        if ((event.state & gtk.gdk.CONTROL_MASK)  and
            (event.keyval in [gtk.gdk.keyval_from_name('r'), gtk.gdk.keyval_from_name('R')])):
            self.restart_preview(source)

        if ((event.state & gtk.gdk.CONTROL_MASK)  and
            (event.keyval in [gtk.gdk.keyval_from_name('m'), gtk.gdk.keyval_from_name('M')])):
            self.on_metadata(source)

        if ((event.state & gtk.gdk.CONTROL_MASK)  and
            event.keyval == gtk.gdk.keyval_from_name('Return') ):
            self.toggle_fullscreen(None)

        if ((event.state & gtk.gdk.CONTROL_MASK)  and
            (event.keyval in [gtk.gdk.keyval_from_name('1')])) :
            name = self.conf.get("screen","left")
            for track in self.conf.get_tracks():
                if track["name"] == name :
                    kind = self.conf.get(track,"device")
                    if kind == "mjpeg" or kind == "v4l2" :
                        self.video_control(None,track["location"])

        if ((event.state & gtk.gdk.CONTROL_MASK)  and
            (event.keyval in [gtk.gdk.keyval_from_name('2')])) :
            name = self.conf.get("screen","right")
            for track in self.conf.get_tracks():
                if track["name"] == name :
                    kind = track["device"]
                    if kind == "mjpeg" or kind == "v4l2" :
                        self.video_control(None,track["location"])        

        if ((event.state & gtk.gdk.CONTROL_MASK)  and
            (event.keyval in [gtk.gdk.keyval_from_name('3')])) :
            for track in self.conf.get_tracks():
                if track["device"] == "pulse" and track["active"] == "True":
                    self.volume_control(None) # FIXME not working as expected

        return True  
  

################################# CONTROL ###############################

    def change_mode(self, origin, page):
        self.dispatcher.emit("galicaster-status", 
                             self.nbox.get_current_page(), page)
        self.nbox.set_current_page(page)
        self.function = page

    def change_mode_by_signal(self, origin, page):
        self.dispatcher.emit("galicaster-status", 
                             self.nbox.get_current_page(), page)
        self.nbox.set_current_page(page)
        self.function = page

    def preferences(self,button):
        log.info('Configuration Window')
        novo = ConfUI(parent=self.window)
        self.recorder.reload_state_and_permissions()

    def devices(self,button):
        log.info('Device Configuration Window')
        self.novo = DeviceUI(parent=self.window)

    def volume_control(self,button):
        gvc_path=glib.find_program_in_path('gnome-volume-control')
        glib.spawn_async([gvc_path])       
        return True

    def video_control(self,button,device):
        log.info("guvcView executed")
        guvc_path=glib.find_program_in_path('guvcview')  
        glib.spawn_async([guvc_path,'-o','-d',device])       
        return True

    def play_mp(self,origin, mediapackage): 
        """
        Plays a mediapackage
        """
        self.player.play_from_list(mediapackage)
        self.change_mode(None, PLA)


######################### DEVELOPER BAR ######################

    def toggle_fullscreen(self,button): 
        if not self.window.is_fullscreen:
            self.window.fullscreen()            
            self.window.is_fullscreen = True
            self.resize(0)
        elif self.window.is_fullscreen:
            self.window.unfullscreen()
            self.window.is_fullscreen = False
            self.resize(1)
        return True

    def restart_preview(self,button): 
        self.recorder.restart()
        return True

    def on_metadata(self,button): 
        self.recorder.on_edit_meta(None) 


    def light_resize(self,elemente,event=None): 

        if elemente==0:
            screen=self.window.get_screen()
            anchura = screen.get_width()
            if anchura not in [1024,1280,1920]:
                anchura = 1920
            self.recorder.resize([anchura, screen.get_height()])   
        elif elemente == 1: # FORCE 1024x768 MODE
            anchura = 1024
            self.recorder.resize([anchura,768])
        else:
            self.recorder.resize(self.window.get_size())


    def regular_resize(self,elemente,event=None) :
        if elemente==0:
            screen=self.window.get_screen()
            anchura = screen.get_width()
            if anchura not in [1024,1280,1920]:
                anchura = 1920
            altura = screen.get_height()
            size= [anchura, altura]
            self.recorder.resize(size)
            self.listing.resize(size)
            self.player.resize(size)
            self.distribution.resize(size)
            self.strip1.resize(size)
            self.strip2.resize(size)

        elif elemente == 1: # FORCE 1024x768 MODE
            anchura = 1024
            self.recorder.resize([anchura,768])
            self.listing.resize([anchura,768])
            self.player.resize([anchura,768])
            self.distribution.resize([anchura,768])
            self.strip1.resize([anchura,768])
            self.strip2.resize([anchura,768])
   
        else: 
            size = self.window.get_size()
            self.recorder.resize(size)
            self.listing.resize(size) 
            self.player.resize(size) 
            self.distribution.resize(size) 
            self.strip1.resize(size)
            self.strip2.resize(size)
        
        return True
