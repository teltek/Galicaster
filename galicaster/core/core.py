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


import logging

import glib
import gtk
glib.threads_init()
gtk.gdk.threads_init() 

from galicaster.utils.dbusservice import DBusService
from galicaster.classui.recorderui import RecorderClassUI
from galicaster.classui.listing import ListingClassUI
from galicaster.classui.playerui import PlayerClassUI
from galicaster.classui.distrib import DistribUI

from galicaster.core import context
from galicaster import plugins


logger = logging.getLogger()

REC= 0
PLA= 2
MMA= 1
DIS= 3
PIN= 4 


class Main():
    def __init__(self):
        service = DBusService(self)
        self.conf = context.get_conf()
        self.state = context.get_state()
        self.dispatcher = context.get_dispatcher()

        self.modules = []
        self.modules.append('recorder')
             
        if self.conf.get_boolean('basic', 'admin'):
            self.modules.append('media_manager')
            self.modules.append('player')

        if self.conf.get_boolean('ingest', 'active'):
            self.modules.append('scheduler')

        if self.conf.get_boolean('basic', 'pin'):
            self.modules.append('pin')

        self.load_modules()
        self.dispatcher.connect('net-up', self.check_net, True)
        self.dispatcher.connect('net-down', self.check_net, False)

    def load_modules(self):
        self.window = context.get_mainwindow()
               
        # Recorder
        self.recorder = RecorderClassUI()
        self.window.insert_page(self.recorder, 'REC', REC) 

        if 'scheduler' in self.modules:        
            self.scheduler = context.get_scheduler()

        if 'media_manager' in self.modules:
            self.dispatcher.connect('change-mode', self.change_mode)
            self.dispatcher.connect('play-list', self.play_mp)

            # Distribution
            self.distribution = DistribUI()
            self.window.insert_page(self.distribution, 'DISTRIBUTION', DIS) 

            # Media Manager
            self.listing  = ListingClassUI()
            self.window.insert_page(self.listing, 'LIST', MMA)
        
        if 'player' in self.modules:
            self.player = PlayerClassUI()
            self.window.insert_page(self.player, 'PLAYER', PLA)

        self.window.start()

        if 'recorder' and 'media_manager' in self.modules:            
            self.window.set_current_page(DIS)
        else:
            self.window.set_current_page(REC)
            self.recorder.block()  

        plugins.init()
        context.get_heartbeat().init_timer()


    def emit_quit(self):
        self.dispatcher.emit('galicaster-notify-quit')


    def change_mode(self, origin, page):
        old_page = self.window.get_current_page()
        self.window.set_current_page(page)  
        self.state.area = page
        self.dispatcher.emit('galicaster-status', old_page, page)


    def play_mp(self,origin, mediapackage): 
        """
        Plays a mediapackage
        """
        self.change_mode(None, PLA)
        self.player.play_from_list(mediapackage)


    def check_net(self, origin, data):
        context.get_state().net = data
