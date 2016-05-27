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


from gi.repository import GLib
from gi.repository import Gdk
GLib.threads_init()
Gdk.threads_init()

import os
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

        self.change_cwd()

        self.conf = context.get_conf()
        self.dispatcher = context.get_dispatcher()
        self.modules = self.conf.get_modules()
        self.load_modules()

    def load_modules(self):        
        self.window = context.get_mainwindow()
        # Load plugins after loading the main window (fixes a problem with the plugin 'nocursor')
        plugins.init()

        # Recorder
        self.recorder = RecorderClassUI()
        self.window.insert_page(self.recorder, 'REC', REC) 
        
        if 'scheduler' in self.modules:        
            self.scheduler = context.get_scheduler()

        if 'media_manager' in self.modules:
            self.dispatcher.connect('action-view-change', self.change_mode)

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

        if 'media_manager' in self.modules:            
            self.window.set_current_page(DIS)
        else:
            self.window.set_current_page(REC)
            self.recorder.block()  

        context.get_heartbeat().init_timer()
        self.dispatcher.emit("init")


    def emit_quit(self):
        self.dispatcher.emit('quit')

    def change_mode(self, origin, page):
        old_page = self.window.get_current_page()
        self.window.set_current_page(page)  
        self.dispatcher.emit('view-changed', old_page, page)

    def check_net(self, origin, data):
        self.state.net = data

    def change_cwd(self):
        repo = context.get_repository()
        rectemp = repo.get_rectemp_path()

        logger.info("Changing current working dir (cwd) to {}".format(rectemp))
        os.chdir(rectemp)
