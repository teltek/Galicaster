# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/ical
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
from os import path
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase
from datetime import datetime


from galicaster.mediapackage import repository
from galicaster.utils import ical

class TestFunctions(TestCase):
    
    baseDir = path.join(path.dirname(path.abspath(__file__)), 'resources', 'ical')


    def setUp(self):
        self.tmppath = mkdtemp()

    def tearDown(self):
        rmtree(self.tmppath)
    
    def test_ical(self):   
        repo = repository.Repository(self.tmppath)
        
        events = ical.get_events_from_file_ical(path.join(self.baseDir, 'test.ical'))
        
        for event in events:
            ical.create_mp(repo, event)

        
        next = repo.get_next_mediapackage()
        self.assertEqual(next.getDate(), datetime.strptime('2012-08-25 17:00:00', '%Y-%m-%d %H:%M:%S'))

        nexts = repo.get_next_mediapackages()
        self.assertEqual(nexts[0].getDate(), datetime.strptime('2012-08-25 17:00:00', '%Y-%m-%d %H:%M:%S'))
            


