# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/core/dispatcher
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


"""
Unit tests for `galicaster.core.context` module.
"""

from unittest import TestCase
from galicaster.core.dispatcher import Dispatcher
from gi.repository import Gtk
from gi.repository import GObject

called = False

class TestFunctions(TestCase):

    def callback(self, emisor, value):
        value['called'] = True
        
    def callback_ui(self, emisor, value):
        global called
        called = True
        Gtk.main_quit()
        
    def emit_signal(self, dispatcher, signal, *args):
        dispatcher.emit(signal, args)
        
    def test_connect_and_emit(self):
        dispatcher = Dispatcher()

        dispatcher.connect('pr', self.callback)
        obj = {'called': False}

        dispatcher.emit('pr', obj)
        self.assertTrue(obj['called'])

        
    def test_connect_ui_and_emit(self):
        global called
        called = False
        
        dispatcher = Dispatcher()

        dispatcher.connect_ui('pr', self.callback_ui)
        obj = {'called': False}

        timeout_id = GObject.timeout_add_seconds(1, self.emit_signal, dispatcher, 'pr', obj)
        Gtk.main()
        self.assertTrue(called)


    def test_add_new_signal(self):
        dispatcher = Dispatcher()
        dispatcher.add_new_signal('test-signal', True)

        dispatcher.connect('test-signal', self.callback)        
        obj = {'called': False}
        dispatcher.emit('test-signal', obj)

        self.assertTrue(obj['called'])


        








