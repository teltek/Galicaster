# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/recorder/recorder
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
Tests for `galicaster.recorder.recorder` modules.
"""

from os import path
import time

from gi.repository import Gst

from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase, skip
from nose.plugins.attrib import attr

from galicaster.recorder.recorder import Recorder
from tests.recorder.base import Base

@attr('nodefault', 'recorder')
class TestFunctions(TestCase, Base):
        
    def setUp(self):
        Base.setUp(self)

    def tearDown(self):
        Base.tearDown(self)

    def test_constructor(self):
        self.assertRaises(TypeError, Recorder)
        self.assertRaises(TypeError, Recorder, [])
        self.assertRaises(NameError, Recorder, [{'name': 'name'}])
        self.assertRaises(NameError, Recorder, [{'type': 'v4l2', 'caps': 'raw'}])
        self.assertRaises(NameError, Recorder, [{'device': 'v4l2', 'caps': 'raw'}])

        #valid
        Recorder(self.getVideoTestBin())
        Recorder(self.getVideoTestBin() + self.getOtherVideoTestBin() + self.getAudioTestBin())


    def test_get_display_areas_info(self):
        recorder = Recorder(self.getVideoTestBin() + self.getOtherVideoTestBin() + self.getAudioTestBin())
        self.assertEqual(recorder.get_display_areas_info(), ['sink-Bars', 'sink-Static'])
        recorder = Recorder([{'name': '1', 'device': 'videotest', 'path': self.tmppath}, 
                             {'name': '2', 'device': 'videotest', 'path': self.tmppath}])
        self.assertEqual(recorder.get_display_areas_info(), ['sink-1', 'sink-2'])


    def test_get_bins_info(self):
        recorder = Recorder([{'name': 'name', 'device': 'videotest', 'path': self.tmppath}])
        info = recorder.get_bins_info()
        self.assertEqual(info[0]['name'], 'name')
        self.assertEqual(info[0]['path'], self.tmppath)


    def test_preview(self):
        bins = self.getVideoTestBin()
        Base.test_preview(self, bins)

    def test_preview_multi(self):
        bins = self.getVideoTestBin() + self.getOtherVideoTestBin() + self.getAudioTestBin()
        Base.test_preview_multi(self, bins)

    def test_preview_and_record(self):
        bins = self.getVideoTestBin()
        Base.test_preview_and_record(self, bins)

    def test_preview_and_record_multi(self):
        bins = self.getVideoTestBin() + self.getOtherVideoTestBin() + self.getAudioTestBin()
        Base.test_preview_and_record_multi(self, bins)

    def test_record(self):
        bins = self.getVideoTestBin()
        Base.test_record(self, bins)


    def test_record_multi(self):
        bins = self.getVideoTestBin() + self.getOtherVideoTestBin() + self.getAudioTestBin()
        Base.test_record_multi(self, bins)

        
    def test_stop_on_paused(self):
        bins = self.getVideoTestBin()
        Base.test_stop_on_paused(self, bins)

    def test_preview_error(self):
        bins = self.getVideoTestBin()
        Base.test_preview_error(self, bins)

    def test_record_error(self):
        bins = self.getVideoTestBin()
        Base.test_record_error(self, bins)

    def test_pause_error(self):
        bins = self.getVideoTestBin()
        Base.test_pause_error(self, bins)

    def test_pause_only_recording(self):
        bins = self.getVideoTestBin()
        Base.test_pause_only_recording(self, bins)

    def test_pause_only_recording_and_stop(self):
        bins = self.getVideoTestBin()
        Base.test_pause_only_recording_and_stop(self, bins)
