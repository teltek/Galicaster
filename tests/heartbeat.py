# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/night
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


"""
Unit tests for `galicaster.scheduler.night` module.
"""

from datetime import datetime
from datetime import timedelta
from unittest import TestCase


from galicaster.scheduler.heartbeat import Heartbeat
from galicaster.core.dispatcher import Dispatcher

class TestFunctions(TestCase):

    def test_init(self):
        dispatcher = Dispatcher()
        
        time_ok = ['10:10', '23:04', '1:2']
        time_ko = ['10-10', '23:12234', 'doce', '1:_2', 'tonight']

        for t in time_ok:
            Heartbeat(dispatcher, 1, 2, t)

        for t in time_ko:
            self.assertRaises(ValueError, Heartbeat, dispatcher, 1, 2, t)
        
            
    # TODO improve test. Problem know datetime.now()
    def test_get_seg_until_next(self):
        dispatcher = Dispatcher()

        now = datetime.now()
        after_now = now + timedelta(minutes=1)
        n = Heartbeat(dispatcher, 1, 2, after_now.strftime('%H:%M'))
        seg = n.get_seg_until_next()

        self.assertLess(seg, 60)
        self.assertGreater(seg, 0)

        now = datetime.now()
        after_now = now - timedelta(hours=1)
        n = Heartbeat(dispatcher, 1, 2, after_now.strftime('%H:%M'))
        seg = n.get_seg_until_next()
        self.assertTrue(seg > 22 * 3600)
        self.assertTrue(seg < 24 * 3600)
        

    def test_get_two_seg_until_next(self):
        dispatcher = Dispatcher()

        now = datetime.now()
        after_now = now + timedelta(minutes=1)
        n = Heartbeat(dispatcher, 1, 2, after_now.strftime('%H:%M'))
        one = n.get_seg_until_next()
        two = n.get_seg_until_next()
        self.assertTrue(two - one < 2)

        
    def test_get_seg_until_next_now(self):
        dispatcher = Dispatcher()

        now = datetime.now()
        n = Heartbeat(dispatcher, 1, 2, now.strftime('%H:%M'))
        self.assertTrue(n.get_seg_until_next(), 24*60*60)
