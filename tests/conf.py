# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/conf
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


"""
Unit tests for `galicaster.core.conf` module.
"""
from os import path
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError
from unittest import TestCase

from galicaster.core.conf import Conf


class TestFunctions(TestCase):
    
    
    def setUp(self):
        conf_file = path.join(path.dirname(path.abspath(__file__)), 'resources', 'conf', 'conf.ini')
        self.conf = Conf(conf_file)

    def tearDown(self):
        del self.conf
    
    def test_init_no_file(self):
        conf_file = path.abspath(path.join(path.dirname(__file__), '..', 'conf.ini'))
        conf_dist_file = path.abspath(path.join(path.dirname(__file__), '..', 'conf-dist.ini'))
        conf = Conf()
        self.assertEqual(conf_file, conf.conf_file)
        self.assertEqual(conf_dist_file, conf.conf_dist_file)

    def test_init_no_dist_file(self):
        conf_file = path.join(path.dirname(path.abspath(__file__)), 'resources', 'conf', 'conf.ini')
        conf_dist_file = path.join(path.dirname(path.abspath(__file__)), 'resources', 'conf', 'conf-dist.ini')
        conf = Conf(conf_file)
        self.assertEqual(conf_file, conf.conf_file)
        self.assertEqual(conf_dist_file, conf.conf_dist_file)

    def test_init_all_files(self):
        conf_file = path.join(path.dirname(path.abspath(__file__)), 'resources', 'conf', 'conf.ini')
        conf_dist_file = path.join(path.dirname(path.abspath(__file__)), 'resources', 'conf', 'conf-dist.ini')
        conf = Conf(conf_file, conf_dist_file)
        self.assertEqual(conf_file, conf.conf_file)
        self.assertEqual(conf_dist_file, conf.conf_dist_file)

    def test_get_and_set(self):
        # GET data in conf-dist
        self.assertEqual('full', self.conf.get('ingest', 'workflow'))
        # GET data in conf
        self.assertEqual('track1', self.conf.get('track1', 'name'))
        # GET data in conf (and conf-dist)
        self.assertEqual('presentation', self.conf.get('screen', 'left'))
        # SET
        self.conf.set('section', 'key', 'value')
        self.assertEqual('value', self.conf.get('section', 'key'))
        

    def test_reload(self):
        self.conf.set('basic', 'temp', 'temporal')
        self.assertEqual('temporal', self.conf.get('basic', 'temp'))
        self.conf.reload()
        self.assertEqual('/tmp/repo', self.conf.get('basic', 'temp'))
        

    def test_get_bins(self):
        self.assertEqual(len(self.conf.getBins('/tmp')), 3)
        #FIXME add more

    def test_get_tracks_in_mh_dict(self):
        conf = self.conf.get_tracks_in_mh_dict()
        self.assertEqual(len(conf), 3*3 +1)
        self.assertEqual(conf['capture.device.names'], 'track1,track2,track3')
        self.assertEqual(conf['capture.device.track2.outputfile'], 'SCREEN.mpeg')
        

        

