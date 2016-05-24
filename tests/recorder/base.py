# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/recorder/base
#
# Copyright (c) 2014, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

import time
from os import path
from tempfile import mkdtemp
from shutil import rmtree
from unittest import TestCase, skip

from gi.repository import Gst

from galicaster.utils.mediainfo import get_duration
from galicaster.recorder.recorder import Recorder

class Base(object):

    def assertCorrectRecording(self, bins, duration=0):
        for bin in bins:
            self.assertTrue(path.exists(path.join(self.tmppath, bin['file'])))
            if duration:
                self.assertTrue(path.getsize(path.join(self.tmppath, bin['file'])) > 0)
                self.assertEqual(get_duration(path.join(self.tmppath, bin['file'])), duration)
            else:
                self.assertTrue(path.getsize(path.join(self.tmppath, bin['file'])) == 0)
    
    
    def setUp(self):
        self.tmppath = mkdtemp()

    def tearDown(self):
        rmtree(self.tmppath)


    def getVideoTestBin(self):
        return [{'name': 'Static',
                 'device': 'videotest',
                 'location': 'default',
                 'pattern': '1',
                 'file': 'SCREEN.avi',
                 'flavor': 'presentation',
                 'caps': 'video/x-raw,framerate=25/1,width=640,height=480',
                 'color1': '4294967295',
                 'color2': '4278190080',
                 'path': self.tmppath}]

    def getOtherVideoTestBin(self):
        return [{'name': 'Bars', 
                 'device': 'videotest',
                 'location': 'default',
                 'pattern': '0',
                 'file': 'CAMERA.avi',
                 'caps': 'video/x-raw,framerate=25/1,width=640,height=480',
                 'color1': '4294967295',
                 'color2': '4278190080',
                 'flavor': 'presenter',
                 'path': self.tmppath}]
    
    def getAudioTestBin(self):
        return [{'name': 'Noise',
                 'device': 'audiotest',
                 'file': 'sound.mp3',
                 'frequency': '440',
                 'volume': '0.3',
                 'player': 'True',
                 'vumeter': 'True',
                 'amplification': '1.0',
                 'flavor': 'presenter',
                 'path': self.tmppath}]
    

    def test_preview(self, bins):
        recorder = Recorder(bins)
        recorder.preview()
        self.assertEqual(recorder.get_status()[1], Gst.State.PLAYING)
        time.sleep(2)
        recorder.stop()
        self.assertEqual(recorder.get_recorded_time(), 0)
        self.assertCorrectRecording(bins, 0)


    def test_preview_multi(self, bins):
        recorder = Recorder(bins)
        recorder.preview()
        self.assertEqual(recorder.get_status()[1], Gst.State.PLAYING)
        time.sleep(4)
        recorder.stop()
        self.assertEqual(recorder.get_recorded_time(), 0)
        self.assertCorrectRecording(bins, 0)


    def test_preview_and_record(self, bins):
        recorder = Recorder(bins)
        recorder.preview_and_record()
        self.assertEqual(recorder.get_status()[1], Gst.State.PLAYING)
        time.sleep(2)
        recorder.stop()
        self.assertTrue(recorder.get_recorded_time() > 0)
        self.assertCorrectRecording(bins, 2)


    def test_preview_and_record_multi(self, bins):
        recorder = Recorder(bins)
        recorder.preview_and_record()
        self.assertEqual(recorder.get_status()[1], Gst.State.PLAYING)
        time.sleep(4)
        recorder.stop()
        self.assertTrue(recorder.get_recorded_time() > 0)
        self.assertCorrectRecording(bins, 4)


    def test_record(self, bins):
        recorder = Recorder(bins)
        recorder.preview()
        self.assertEqual(recorder.get_status()[1], Gst.State.PLAYING)
        time.sleep(2)
        self.assertEqual(recorder.get_recorded_time(), 0)

        recorder.record()
        time.sleep(2)
        recorder.stop()
        self.assertTrue(recorder.get_recorded_time() > 0)
        self.assertCorrectRecording(bins, 2)


    def test_record_multi(self, bins):
        recorder = Recorder(bins)
        recorder.preview()
        self.assertEqual(recorder.get_status()[1], Gst.State.PLAYING)
        time.sleep(4)
        self.assertEqual(recorder.get_recorded_time(), 0)

        recorder.record()
        time.sleep(4)
        recorder.stop()
        self.assertTrue(recorder.get_recorded_time() > 0)
        self.assertCorrectRecording(bins, 4)


    def test_stop_on_paused(self, bins):
        recorder = Recorder(bins)
        recorder.preview()
        self.assertEqual(recorder.get_status()[1], Gst.State.PLAYING)
        time.sleep(2)
        self.assertEqual(recorder.get_recorded_time(), 0)

        recorder.record()
        time.sleep(2)
        recorder.pause()
        time.sleep(2)
        recorder.stop()

        self.assertTrue(recorder.get_recorded_time() > 0)
        self.assertCorrectRecording(bins, 2)


    def test_preview_error(self, bins):
        recorder = Recorder(bins)
        recorder.preview()
        self.assertEqual(recorder.get_status()[1], Gst.State.PLAYING)
        time.sleep(2)

        rec_time = recorder.get_recorded_time()
        self.assertEqual(rec_time, 0)
        recorder.record()
        time.sleep(2)
        recorder.stop(True)
        self.assertEqual(recorder.get_status()[1], Gst.State.NULL)


    def test_record_error(self, bins):
        recorder = Recorder(bins)
        recorder.preview()
        self.assertEqual(recorder.get_status()[1], Gst.State.PLAYING)
        time.sleep(2)
        rec_time = recorder.get_recorded_time()
        self.assertEqual(rec_time, 0)
        recorder.record()
        time.sleep(2)
        recorder.stop(True)
        self.assertEqual(recorder.get_status()[1], Gst.State.NULL)


    def test_pause_error(self, bins):
        recorder = Recorder(bins)
        recorder.preview()
        self.assertEqual(recorder.get_status()[1], Gst.State.PLAYING)
        time.sleep(2)
        rec_time = recorder.get_recorded_time()
        #self.assertEqual(rec_time, 0)
        recorder.pause()
        time.sleep(2)
        recorder.stop(True)
        self.assertEqual(recorder.get_status()[1], Gst.State.NULL)


    def test_pause_only_recording(self, bins):
        recorder = Recorder(bins)
        recorder.preview()
        self.assertEqual(recorder.get_status()[1], Gst.State.PLAYING)
        time.sleep(2)
        self.assertEqual(recorder.get_recorded_time(), 0)
        recorder.record()
        time.sleep(2)
        recorder.pause_recording()
        time.sleep(2)
        recorder.resume_recording()
        time.sleep(1)
        recorder.stop()
        self.assertCorrectRecording(bins, 3)

    def test_pause_only_recording_and_stop(self, bins):
        recorder = Recorder(bins)
        recorder.preview()
        self.assertEqual(recorder.get_status()[1], Gst.State.PLAYING)
        time.sleep(2)
        self.assertEqual(recorder.get_recorded_time(), 0)
        recorder.record()
        time.sleep(2)
        recorder.pause_recording()
        time.sleep(2)
        recorder.stop()
        self.assertCorrectRecording(bins, 2)
