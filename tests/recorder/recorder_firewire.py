# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/recorder/recorder_firewire
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
Tests for `galicaster.recorder.bins.firewire` module.
"""

from os import path
import time

from gi.repository import Gst

from unittest import TestCase, skip
from nose.plugins.attrib import attr

from tests.recorder.base import Base

@attr('nodefault', 'recorder_firewire')
class TestFunctions(TestCase, Base):

    firewire_bin = [{'name'     : 'firewire',
                     'device'   : 'firewire',
                     'path'     :  '/tmp/',
                     'file'     : 'FIREWIRE.dv'}]

    def setUp(self):
        Base.setUp(self)
        self.firewire_bin[0]['path'] = self.tmppath
        
    def tearDown(self):
        Base.tearDown(self)


    def test_preview(self):
        bins = self.firewire_bin
        Base.test_preview(self, bins)

    def test_preview_multi(self):
        bins = self.firewire_bin + self.getVideoTestBin() + self.getAudioTestBin()
        Base.test_preview_multi(self, bins)

    def test_preview_and_record(self):
        bins = self.firewire_bin
        Base.test_preview_and_record(self, bins)

    def test_preview_and_record_multi(self):
        bins = self.firewire_bin + self.getVideoTestBin() + self.getAudioTestBin()
        Base.test_preview_and_record_multi(self, bins)

    def test_record(self):
        bins = self.firewire_bin
        Base.test_record(self, bins)

    def test_record_multi(self):
        bins = self.firewire_bin + self.getVideoTestBin() + self.getAudioTestBin()
        Base.test_record_multi(self, bins)

    #TODO
    def todo_test_stop_on_paused(self):
        bins = self.firewire_bin
        Base.todo_test_stop_on_paused(self, bins)

    def test_preview_error(self):
        bins = self.firewire_bin
        Base.test_preview_error(self, bins)

    def test_record_error(self):
        bins = self.firewire_bin
        Base.test_record_error(self, bins)

    def test_pause_error(self):
        bins = self.firewire_bin
        Base.test_pause_error(self, bins)
