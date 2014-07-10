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


import glib
import gtk
glib.threads_init()
gtk.gdk.threads_init()

from galicaster import __version__
from galicaster.core import context
from galicaster import plugins

from galicaster.utils.dbusservice import DBusService
from galicaster.classui.recorderui import RecorderClassUI
from galicaster.classui.listing import ListingClassUI
from galicaster.classui.playerui import PlayerClassUI
from galicaster.classui.distrib import DistribUI

logger = context.get_logger()

REC = 0
PLA = 2
MMA = 1
DIS = 3

class Main():
    def __init__(self):
        DBusService(self)

        logger.info('galicaster.__version__: %r', __version__)
        logger.info('galicaster.__file__: %r', __file__)

        self.conf = context.get_conf()
        self.state = context.get_state()
        self.dispatcher = context.get_dispatcher()
        self.modules = self.conf.get_modules()
        self.load_modules()
        self.dispatcher.connect('net-up', self.check_net, True)
        self.dispatcher.connect('net-down', self.check_net, False)

    def load_modules(self):
        plugins.init()
        
        self.window = context.get_mainwindow()
               
        # Recorder
        self.recorder = RecorderClassUI()
        self.window.insert_page(self.recorder, 'REC', REC) 

        if 'scheduler' in self.modules:        
            self.scheduler = context.get_scheduler()

        if 'media_manager' in self.modules:
            self.dispatcher.connect('change-mode', self.change_mode)

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

        self.recorder.go_ahead() # allows record area to load devices and show preview

        if 'media_manager' in self.modules:            
            self.window.set_current_page(DIS)
            self.state.area = DIS
        else:
            self.window.set_current_page(REC)
            self.state.area = REC
            self.recorder.block()  

        context.get_heartbeat().init_timer()
        self.dispatcher.emit("galicaster-init")


    def emit_quit(self):
        self.dispatcher.emit('galicaster-notify-quit')

    def change_mode(self, origin, page):
        old_page = self.window.get_current_page()
        self.window.set_current_page(page)  
        self.state.area = page
        self.dispatcher.emit('galicaster-status', old_page, page)

    def check_net(self, origin, data):
        self.state.net = data
