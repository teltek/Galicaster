# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/utils/nautilus
#
# Copyright (c) 2014, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


"""
Unit tests for `galicaster.utils.nautilus` module.
"""
import tempfile
import subprocess
from os import path
from datetime import datetime, timedelta

from unittest import TestCase
from galicaster.utils import nautilus, systemcalls

class TestFunctions(TestCase):
    
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_open_folder(self):
        return_code = nautilus.open_folder('/tmp')
        self.assertTrue(return_code)
