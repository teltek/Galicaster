# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/utils/systemcalls
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
import tempfile
import subprocess
from os import path
from datetime import datetime, timedelta

from unittest import TestCase
from nose.plugins.attrib import attr
from galicaster.utils import systemcalls

class TestFunctions(TestCase):
    
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_execute_empty_command(self):
        out = systemcalls.execute()
        self.assertEqual(out, False)

        out = systemcalls.execute([])
        self.assertEqual(out, False)

        out = systemcalls.execute(['inexistentcommand', 'params'])
        self.assertEqual(out, False)

        testfile = tempfile.NamedTemporaryFile()
        out = systemcalls.execute(['touch', testfile.name])
        self.assertEqual(out, True)
        self.assertTrue(path.exists(testfile.name))

        mtime = path.getmtime(testfile.name)
        last_modified_date = datetime.fromtimestamp(mtime)
        now = datetime.now()

        self.assertTrue(last_modified_date + timedelta(seconds=1) > now)
        self.assertTrue(last_modified_date - timedelta(seconds=1) < now)

    def test_execute_error(self):
        out = systemcalls.execute(['ls', 'non existent'])
        self.assertEqual(out, False)

    @attr('notravis')
    def test_write_dconf_settings(self):        
        systemcalls.write_dconf_settings(settings={'/org/compiz/profiles/unity/plugins/unityshell/launcher-hide-mode' : '1'})
        output = subprocess.check_output(['dconf', 'read', '/org/compiz/profiles/unity/plugins/unityshell/launcher-hide-mode'], stderr=subprocess.STDOUT)
        self.assertTrue(output, '1')

        systemcalls.write_dconf_settings(settings={'/org/compiz/profiles/unity/plugins/unityshell/launcher-hide-mode' : '0'})
        self.assertTrue(output, '0')

    def test_is_running(self):
        output = systemcalls.is_running("bash")
        self.assertNotEqual(output, None)

        output = systemcalls.is_running("inexistent")
        self.assertEqual(output, None)

        
