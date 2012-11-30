# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/bins
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.



"""
Tests for `galicaster.recorder.pipeline` modules.
"""

from unittest import TestCase
from galicaster.recorder.pipeline.blackmagic import GCblackmagic
from galicaster.recorder.pipeline.v4l2 import GCv4l2
from galicaster.recorder.pipeline.hauppauge import GChauppauge

class TestFunctions(TestCase):

    def test_validate_name(self):
        track = GCv4l2({'name':'Invalid~', 'path':'/tmp/'})
        self.assertEqual(track.options['name'],"Invalid")   

    def test_validate_integer_out_of_range(self):
        try:
            track = GCv4l2({'path' : '/tmp/',
                        'videocrop-right' : 300})
        except SystemError:
            return True
        
    def test_validate_integer_not_valid(self):     
        try:
            track = GCv4l2({'path' : '/tmp',
                        'videocrop-right' : "10az"})
        except SystemError:
            return True
        self.assertEqual(track.options['path'], '/')
                   

    def test_validate_boolean_not_valid(self):   
        try:
            track = GChauppauge({'path' : '/tmp',
                        'player' : "disable"})
        except SystemError:
            return True
        #Force fail on test
        self.assertEqual(track.options['player'], 'fail')

    def test_validate_boolean_valid(self):   
        try:
            track = GChauppauge({'path' : '/tmp',
                        'player' : "fALse"})
        except SystemError:
            return True
        #Force fail on test
        self.assertEqual(track.options['player'], False)   
        
    def test_validate_flavor_not_valid(self):   
        try:
            track = GChauppauge({'path' : '/tmp',
                        'flavor' : 'presentacion'})
        except SystemError:
            return True
        #Force fail on test
        self.assertEqual(track.options['flavor'], 'fail')

    def test_validate_all_flavors_valid(self):   
        try:
            track1 = GChauppauge({'path' : '/tmp',
                                  'flavor' : 'presentation'})
            track2 = GChauppauge({'path' : '/tmp',
                                  'flavor' : 'presenter'})
            track3 = GChauppauge({'path' : '/tmp',
                                  'flavor' : 'other'})        
        except SystemError:
            pass
        
        self.assertEqual(track1.options['flavor'], 'presentation')
        self.assertEqual(track2.options['flavor'], 'presenter')
        self.assertEqual(track3.options['flavor'], 'other')

    def test_validate_select_not_valid(self):   
        try:
            track = GCblackmagic({'path' : '/tmp',
                                  'input' : 'thing'})
        except SystemError:
            return True
        # Force fail on test
        self.assertEqual(track.options['input'], 'fail')

    def test_validate_select_valid(self):   
        try:
            track = GCblackmagic({'path' : '/tmp',
                                  'input' : 'sdi'})
        except SystemError:
            pass
        self.assertEqual(track.options['input'], 'sdi')

    def test_blackmagic_no_audio(self):
        track = GCblackmagic({"audio-input":"none", "path":"/"})
        self.assertEqual(track.has_audio, False)
