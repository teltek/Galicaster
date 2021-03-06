# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/utils/sidebyside
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


"""
Unit tests for `galicaster.mediapackage` module.
"""
from unittest import TestCase
from os import path
import tempfile

from gi.repository import GLib
if getattr(GLib, "threads_init", None) is not None:
    GLib.threads_init()

from tests import get_resource
from galicaster.utils import sidebyside


class TestFunctions(TestCase):
    
    base_dir = get_resource('sbs')
    
    def test_sbs_with_embeded_audio(self):   
        out = tempfile.NamedTemporaryFile()
        screen = path.join(self.base_dir, 'SCREEN_NO_AUDIO.mp4')
        camera = path.join(self.base_dir, 'CAMERA.mp4')
        out = sidebyside.create_sbs(out.name, camera, screen)
        self.assertTrue(out)


    def test_sbs_with_audio(self):   
        out = tempfile.NamedTemporaryFile()
        screen = path.join(self.base_dir, 'SCREEN.mp4')
        camera = path.join(self.base_dir, 'CAMERA.mp4')
        audio = path.join(self.base_dir, 'AUDIO.mp3')
        out = sidebyside.create_sbs(out.name, camera, screen, audio)
        self.assertTrue(out)

    def test_sbs_with_two_embeded_audio(self):   
        out = tempfile.NamedTemporaryFile()
        screen = path.join(self.base_dir, 'SCREEN.mp4')
        camera = path.join(self.base_dir, 'CAMERA.mp4')
        out = sidebyside.create_sbs(out.name, camera, screen)
        self.assertTrue(out)

    def test_sbs_without_audio(self):   
        out = tempfile.NamedTemporaryFile()
        screen = path.join(self.base_dir, 'SCREEN_NO_AUDIO.mp4')
        camera = path.join(self.base_dir, 'CAMERA_NO_AUDIO.mp4')
        out = sidebyside.create_sbs(out.name, camera, screen)
        self.assertTrue(out)

    def test_sbs_no_input_file(self):   
        out = tempfile.NamedTemporaryFile()
        screen = path.join(self.base_dir, 'NO_SCREEN.mp4')
        camera = path.join(self.base_dir, 'CAMERA.mp4')
        self.assertRaises(IOError, sidebyside.create_sbs, out.name, camera, screen)

    def test_sbs_less_than_two_files(self):   
        out = tempfile.NamedTemporaryFile()
        screen = path.join(self.base_dir, 'SCREEN.mp4')
        camera = path.join(self.base_dir, 'CAMERA.mp4')
        self.assertRaises(IOError, sidebyside.create_sbs, out.name, None, camera)





