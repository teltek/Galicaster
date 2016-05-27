# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/recorder/bins
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.



"""
Tests for `galicaster.recorder.bins` modules.
"""

from unittest import TestCase
from galicaster.recorder.bins.blackmagic import GCblackmagic
from galicaster.recorder.bins.v4l2 import GCv4l2
from galicaster.recorder.bins.datapath import GCdatapath
from galicaster.recorder.bins.rtp import GCrtp
from galicaster.recorder.bins.pulse import GCpulse
from galicaster.recorder.bins.autoaudio import GCautoaudio
from galicaster.recorder.bins.firewire import GCfirewire
from galicaster.utils import validator

class TestFunctions(TestCase):

    def test_validate_name(self):
        msg, options = validator.validate_track({'device': 'v4l2', 'name':'Invalid~', 'path':'/tmp/'})
        track = GCv4l2(options)
        self.assertEqual(track.options['name'],"Invalid")   

    def test_validate_integer_out_of_range(self):
        msg, options = validator.validate_track({'device': 'v4l2', 'path' : '/tmp/',
                                                 'videocrop-right' : 300})
        track = GCv4l2(options)
        self.assertEqual(options['videocrop-right'], 0)
        
    def test_validate_integer_not_valid(self):     
        msg, options = validator.validate_track({'device': 'v4l2', 'path' : '/tmp',
                                                 'videocrop-right' : "10az"})
        track = GCv4l2(options)
        self.assertEqual(options['videocrop-right'], 0)
                   

    def test_validate_boolean_not_valid(self):   
        msg, options = validator.validate_track({'device': 'v4l2', 'path' : '/tmp',
                                                 'player' : "disable"})
        track = GCv4l2(options)
        self.assertEqual(track.options['player'], 'disable')

    def test_validate_boolean_valid(self):   
        msg, options = validator.validate_track({'device': 'pulse', 'path' : '/tmp',
                                                 'player' : "fALse"})
        track = GCautoaudio(options)
        
        self.assertEqual(track.options['player'], False)   
        
    def test_validate_flavor_not_valid(self):   
        msg, options = validator.validate_track({'device': 'v4l2', 'path' : '/tmp','flavor' : 'presentacion'})
        track = GCv4l2(options)
        #Force fail on test
        self.assertEqual(track.options['flavor'], 'presenter')

    def test_validate_all_flavors_valid(self):   
        msg, options = validator.validate_track({'device': 'v4l2', 'path' : '/tmp',
                                                 'flavor' : 'presentation'})
        track1 = GCv4l2(options)
        msg, options = validator.validate_track({'device': 'v4l2', 'path' : '/tmp',
                                                 'flavor' : 'presenter'})
        track2 = GCv4l2(options)
        msg, options = validator.validate_track({'device': 'v4l2', 'path' : '/tmp','flavor' : 'other'})
        track3 = GCv4l2(options )
        
        self.assertEqual(track1.options['flavor'], 'presentation')
        self.assertEqual(track2.options['flavor'], 'presenter')
        self.assertEqual(track3.options['flavor'], 'other')

    def test_validate_select_not_valid(self):   
        msg, options = validator.validate_track({'device': 'blackmagic', 'path' : '/tmp',
                                                 'input' : 'thing'})
        track = GCblackmagic(options)
        self.assertEqual(track.options['input'], 'sdi')

    def test_validate_select_valid(self):   
        msg, options = validator.validate_track({'device': 'blackmagic', 'path' : '/tmp',
                                                 'input' : 'sdi'})
        track = GCblackmagic(options)
        self.assertEqual(track.options['input'], 'sdi')

    def test_blackmagic_no_audio(self):
        msg, options = validator.validate_track({"device": "blackmagic", "audio-input":"none", "path":"/"})
        track = GCblackmagic(options)
        self.assertEqual(track.has_audio, False)

    def test_datapath_is_v4l2(self):
        msg, options = validator.validate_track({"device": "datapath", "file":"VIDEO.avi", "path":"/"})
        track1 = GCdatapath(options)
        msg, options = validator.validate_track({"device": "v4l2","file":"VIDEO.avi", "path":"/"})
        track2 = GCv4l2(options)
        self.assertEqual(track1.options['file'],track2.options['file'])

    def test_rtp_types(self):
        v = "mpeg4"
        a = "mp3"
        msg, options = validator.validate_track({"device": "rtp", "cameratype":v,"audiotype":a, "muxer": "avimux", "path":"/"})
        track = GCrtp(options)
        self.assertEqual(track.options['cameratype'], v)
        self.assertEqual(track.options['audiotype'], a)
        v = "h264"
        a = "aac"
        msg, options = validator.validate_track({"device": "rtp", "cameratype":v,"audiotype":a, "muxer": "mp4mux", "path":"/"})
        track2 = GCrtp(options)
        self.assertEqual(track2.options['cameratype'], v)
        self.assertEqual(track2.options['audiotype'], a)

    def test_pulse_audio_activated(self):
        msg, options = validator.validate_track({"device": "pulse", "vumeter":"true", "player":"true", "path":"/"})
        track = GCpulse(options)
        self.assertEqual(track.options['vumeter'], True)
        self.assertEqual(track.options['player'], True)
        
    def test_autoaudio_activated(self):
        msg, options = validator.validate_track({"device": "autoaudio", "vumeter":"true", "player":"true", "path":"/"})
        track = GCautoaudio(options)
        self.assertEqual(track.options['vumeter'], True)
        self.assertEqual(track.options['player'], True)
