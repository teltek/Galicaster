# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/utils/mediainfo
#
# Copyright (c) 2014, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


"""
Unit tests for `galicaster.utils.mediainfo` module.
"""
from unittest import TestCase
from os import path

from tests import get_resource
from galicaster.utils import mediainfo

class TestFunctions(TestCase):
    
    base_dir = get_resource('sbs')
    
    def test_get_duration(self):   
        screen = path.join(self.base_dir, 'SCREEN.mp4')
        camera = path.join(self.base_dir, 'CAMERA.mp4')
        audio = path.join(self.base_dir, 'AUDIO.mp3')

        self.assertEqual(mediainfo.get_duration(screen), 1)
        self.assertEqual(mediainfo.get_duration(camera), 1)
        self.assertEqual(mediainfo.get_duration(audio) , 1)
