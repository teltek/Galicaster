# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/utils/series
#
# Copyright (c) 2014, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


"""
Unit tests for `galicaster.utils.series` module.
"""
import tempfile
import subprocess
from os import path
from datetime import datetime, timedelta

from unittest import TestCase
from galicaster.utils import series

class TestFunctions(TestCase):
    
    def setUp(self):
        pass

    def tearDown(self):
        pass


    def test_size(self):
        self.assertEqual(series.size(1099511627776), '1.0 TB')
        self.assertEqual(series.size(1073741824), '1.0 GB')
        self.assertEqual(series.size(1048576), '1.0 MB')
        self.assertEqual(series.size(2048), '2.0 KB')
        self.assertEqual(series.size(1000000), '976.56 KB')
        
    def test_date(self):
        self.assertEqual(series.date('2015-12-12T14:14:14'), '12-12-2015 14:14')

        
    def test_time(self):
        self.assertEqual(series.time(600), '10:00')
        self.assertEqual(series.time(3600), ' 1:00:00')
        self.assertEqual(series.time(103600), '28:46:40')

        
    def test_long_time(self):
        difference = (datetime.now() + timedelta(minutes=4)) - datetime.now()
        self.assertEqual(series.long_time(difference), "03:59")

        difference = (datetime.now() + timedelta(hours=5, minutes=30)) - datetime.now()
        self.assertEqual(series.long_time(difference), "05:29:59")

        difference = (datetime.now() + timedelta(days=5)) - datetime.now()
        self.assertEqual(series.long_time(difference), "5 days")

    
    def test_list(self):
        self.assertEqual(series.list([]), "")
        self.assertEqual(series.list(["one","two", "three"]), "one, two, three")

    def test_str2bool(self):
        self.assertEqual(series.str2bool(False), False)
        self.assertEqual(series.str2bool("False"), False)
        self.assertEqual(series.str2bool("false"), False)
        self.assertEqual(series.str2bool("FaLse"), False)

        self.assertTrue(series.str2bool("True"))
        self.assertTrue(series.str2bool("true"))
        self.assertTrue(series.str2bool("TrUe"))
        self.assertTrue(series.str2bool("t"))
        self.assertTrue(series.str2bool("1"))
        self.assertTrue(series.str2bool("Yes"))
        self.assertTrue(series.str2bool("YEs"))
        self.assertTrue(series.str2bool("YES"))

