# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/player/player
#
# Copyright (c) 2014, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.


"""
Unit tests for `galicaster.player.player` module.
"""
from unittest import TestCase
from os import path
import time

from gi.repository import GLib
if getattr(GLib, "threads_init", None) is not None:
    GLib.threads_init()

from tests import get_resource
from galicaster.player import Player


class TestFunctions(TestCase):

    base_dir = get_resource('sbs')

    def test_play_with_audio(self):
        screen = path.join(self.base_dir, 'SCREEN.mp4')

        files = {"SCREEN": screen}
        players = {}
        player = Player(files, players)
        player.play()
        player.stop()

    def test_play_without_audio(self):
        screen = path.join(self.base_dir, 'SCREEN_NO_AUDIO.mp4')

        files = {"SCREEN": screen}
        players = {}
        player = Player(files, players)
        player.play()
        player.stop()

    def test_play_two_videos_without_audio(self):
        screen = path.join(self.base_dir, 'SCREEN_NO_AUDIO.mp4')
        camera = path.join(self.base_dir, 'CAMERA_NO_AUDIO.mp4')

        files = {"SCREEN": screen, "CAMERA": camera}
        players = {}
        player = Player(files, players)
        player.play()
        player.stop()

    def test_play_two_videos_and_audio(self):
        screen = path.join(self.base_dir, 'SCREEN_NO_AUDIO.mp4')
        camera = path.join(self.base_dir, 'CAMERA_NO_AUDIO.mp4')
        audio = path.join(self.base_dir, 'AUDIO.mp3')

        files = {"SCREEN": screen, "CAMERA": camera, "AUDIO": audio}
        players = {}
        player = Player(files, players)
        player.play()
        player.stop()

    def test_play_two_videos_audio_embedded(self):
        screen = path.join(self.base_dir, 'SCREEN.mp4')
        camera = path.join(self.base_dir, 'CAMERA.mp4')

        files = {"SCREEN": screen, "CAMERA": camera}
        players = {}
        player = Player(files, players)
        player.play()
        player.stop()
