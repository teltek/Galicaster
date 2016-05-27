# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       test/plugins/cleanstale
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""

"""
from os import path
from shutil import rmtree
from tempfile import mkdtemp, mkstemp
import datetime

from unittest import TestCase

from galicaster.core.conf import Conf
from galicaster.mediapackage import repository
from galicaster.mediapackage import mediapackage

from galicaster.plugins import cleanstale

from galicaster.core import context



class TestFunctions(TestCase):

    def setUp(self):
        self.tmppath = mkdtemp()

        repo = repository.Repository(self.tmppath)
        context.set('repository', repo)

        conf = Conf()
        context.set('conf', conf)
        

    def tearDown(self):
        rmtree(self.tmppath)

    def test_cleanstale_plugin(self):
        dispatcher = context.get_dispatcher()
        repo = context.get_repository()
        conf = context.get_conf()
        now = datetime.datetime.utcnow()

        mp = mediapackage.Mediapackage(identifier="1", title='MP#1', date=(now - datetime.timedelta(days=1)))
        repo.add(mp)
        mp = mediapackage.Mediapackage(identifier="2", title='MP#2', date=(now - datetime.timedelta(days=30)))
        repo.add(mp)
        mp = mediapackage.Mediapackage(identifier="3", title='MP#3', date=(now - datetime.timedelta(days=60)))
        repo.add(mp)
        mp = mediapackage.Mediapackage(identifier="4", title='MP#4', date=(now + datetime.timedelta(days=1)))
        repo.add(mp)
        mp = mediapackage.Mediapackage(identifier="5", title='MP#5', date=(now + datetime.timedelta(days=30)))
        repo.add(mp)

        
        conf.set('cleanstale','maxarchivaldays', '70')
        cleanstale.init()        
        self.assertEqual(len(repo), 5)
        
        conf.set('cleanstale','maxarchivaldays', '50')
        cleanstale.init()
        dispatcher.emit('timer-nightly')
        self.assertEqual(len(repo), 4)
        conf.set('cleanstale','maxarchivaldays', '20')
        cleanstale.init()
        dispatcher.emit('timer-nightly')
        self.assertEqual(len(repo), 3)
