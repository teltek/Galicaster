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

from unittest import TestCase
from galicaster.recorder.recorder import Recorder


class TestFunctions(TestCase):

    def setUp(self):
        self.default_bins = [{'name': 'Bars', 
                              'pattern': '0',
                              'caps': 'video/x-raw-yuv,framerate=25/1,width=640,height=480',
                              'color1': '4294967295',
                              'color2': '4278190080',
                              'location': 'default',
                              'file': 'CAMERA.avi',
                              'device': 'videotest',
                              'flavor': 'presenter',
                              'path': '/home/rubenrua/Repository/rectemp'},
                             {'name': 'Static',
                              'device': 'videotest',
                              'location': 'default',
                              'file': 'SCREEN.avi',
                              'flavor': 'presentation',
                              'caps': 'video/x-raw-yuv,framerate=25/1,width=640,height=480',
                              'pattern': '1',
                              'color1': '4294967295',
                              'color2': '4278190080',
                              'path': '/home/rubenrua/Repository/rectemp'},
                             {'name': 'Noise',
                              'device': 'audiotest',
                              'location': 'default',
                              'file': 'sound.mp3',
                              'flavor': 'presenter',
                              'pattern': 'pink-noise',
                              'frequency': '440',
                              'volume': '0.3',
                              'player': 'True',
                              'vumeter': 'True',
                              'amplification': '1.0',
                              'path': ' /home/rubenrua/Repository/rectemp'}]
                             
    def test_constructor(self):
        recorder = Recorder(self.default_bins)
        self.assertRaises(TypeError, Recorder)
        self.assertRaises(NameError, Recorder, [{'name': 'name'}])
