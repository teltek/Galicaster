# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/core/conf
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
import socket
from os import path
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError
from unittest import TestCase

from tests import get_resource
from galicaster.core.conf import Conf
from galicaster.core.conf import Profile
from galicaster.core.conf import Track


class TestFunctions(TestCase):
        
    def setUp(self):
        conf_file = get_resource('conf/conf.ini')
        dist_file = get_resource('conf/conf-dist.ini')
        self.conf = Conf(conf_file,dist_file)


    def tearDown(self):
        del self.conf

    
    def test_init_no_file(self):
        primary_conf = path.join('/etc/galicaster','conf.ini')
        secondary_conf = path.abspath(path.join(path.dirname(__file__), '..', '..', 'conf.ini'))
        secondary_dist = path.abspath(path.join(path.dirname(__file__), '..', '..', 'conf-dist.ini'))
        # Conf loads default conf and conf-dist
        conf = Conf(conf_dist_file=secondary_dist)
        self.assertEqual( primary_conf if path.isfile(primary_conf) else secondary_conf,
                          conf.conf_file) 
        self.assertEqual( secondary_dist,
                          conf.conf_dist_file) 

    def test_init_all_files(self):
        conf_file = get_resource('conf/conf.ini')
        conf_dist_file = get_resource('conf/conf-dist.ini')
        conf = Conf(conf_file, conf_dist_file)
        self.assertEqual(conf_file, conf.conf_file)
        self.assertEqual(conf_dist_file, conf.conf_dist_file)


    def test_get_and_set(self):
        # GET data in conf-dist
        self.assertEqual('full', self.conf.get('ingest', 'workflow'))
        # GET data in conf
        self.assertEqual('track1', self.conf.get('track1', 'name'))
        # SET
        self.conf.set('section', 'key', 'value')
        self.assertEqual('value', self.conf.get('section', 'key'))
        

    def test_reload(self):
        self.conf.set('basic', 'temp', 'temporal')
        self.assertEqual('temporal', self.conf.get('basic', 'temp'))
        self.conf.reload()
        self.assertEqual('/tmp/repo', self.conf.get('basic', 'temp'))
        

    def test_get_tracks_in_mh_dict(self):
        conf = self.conf.get_tracks_in_mh_dict()
        self.assertEqual(len(conf), 3*3 +1)
        self.assertEqual(conf['capture.device.names'], 'track1,track3,track2')
        self.assertEqual(conf['capture.device.track2.outputfile'], 'SCREEN.mpeg')
        self.assertEqual(conf['capture.device.track2.src'], '/dev/null')

    def test_profile_with_no_profiles_in_files(self):
        conf_file = get_resource('conf/conf.ini')
        conf_dist_file = get_resource('conf/conf_dist.ini')
        profiles_dir = get_resource('conf/profiles')
        conf = Conf(conf_file, conf_dist_file, profiles_dir)

        self.assertEqual(len(conf.get_profiles()), 1)

    def test_init_track(self):
        track = Track()
        self.assertEqual(track.name, None)
        self.assertEqual(track.device, None)
        self.assertEqual(track.flavor, None)
        self.assertEqual(track.location, None)
        self.assertEqual(track.file, None)
        self.assertEqual(len(track), 5)

        track.name = 'v_name'
        track.device = 'v_device'
        track.flavor = 'v_flavor'
        track.location = 'v_location'
        track.file = 'v_file'

        self.assertEqual(track.name, 'v_name')
        self.assertEqual(track.device, 'v_device')
        self.assertEqual(track.flavor, 'v_flavor')
        self.assertEqual(track.location, 'v_location')
        self.assertEqual(track.file, 'v_file')
        self.assertEqual(track['name'], 'v_name')
        self.assertEqual(track['device'], 'v_device')
        self.assertEqual(track['flavor'], 'v_flavor')
        self.assertEqual(track['location'], 'v_location')
        self.assertEqual(track['file'], 'v_file')

        self.assertEqual(track.keys(), ['name', 'device', 'flavor', 'location', 'file'])
        self.assertEqual(track.values(), ['v_name', 'v_device', 'v_flavor', 'v_location', 'v_file'])
        self.assertEqual(track.basic(), {'name': 'v_name', 'device': 'v_device', 
                                        'flavor': 'v_flavor', 'location': 'v_location', 
                                        'file': 'v_file'})
        self.assertEqual(track.options(), {})
        

    def test_add_and_del_value_in_track(self):
        track = Track()
        track['new_key'] = 'new_value'
        self.assertEqual(len(track), 6)
        self.assertEqual(track['new_key'], 'new_value')
        self.assertEqual(track.keys(), ['name', 'device', 'flavor', 'location', 'file', 'new_key'])
        self.assertEqual(track.values(), [None, None, None, None, None, 'new_value'])
        self.assertEqual(track.basic(), {'name': None, 'device': None, 'flavor': None, 
                                        'location': None, 'file': None})
        self.assertEqual(track.options(), {'new_key': 'new_value'})

        del track['new_key']
        self.assertEqual(len(track), 5)
        self.assertEqual(track.keys(), ['name', 'device', 'flavor', 'location', 'file'])
        self.assertEqual(track.values(), [None, None, None, None, None])
        self.assertEqual(track.basic(), {'name': None, 'device': None, 'flavor': None, 
                                         'location': None, 'file': None})
        self.assertEqual(track.options(), {})
                

    def test_init_profile(self):
        profile = Profile()
        self.assertEqual(profile.name, 'New Profile')

        profile = Profile('test')
        self.assertEqual(profile.name, 'test')


    def test_add_track_to_profile(self):
        profile = Profile()
        self.assertEqual(0, len(profile.tracks))
        
        t1 = profile.new_track({})
        self.assertEqual(1, len(profile.tracks))
        
        t2 = Track()
        profile.add_track(t2)
        self.assertEqual(2, len(profile.tracks))

        profile.remove_track(t2)
        self.assertEqual(1, len(profile.tracks))
                

    def test_get_boolean(self):
        conf = Conf()
        for yes in ['True', 'true', 'yes', 'si', 'y', 'OK', 'Y', 'TRUE']:
            conf.set('s', 'k', yes)
            self.assertTrue(conf.get_boolean('s', 'k'), 'Check if {0} is True'.format(yes))

        for no in ['None', 'not', 'False', 'no', 'n']:
            conf.set('s', 'k', no)
            self.assertFalse(conf.get_boolean('s', 'k'), 'Check if {0} is False'.format(no))
        
    def test_get_lower(self):
        conf = Conf()
        for lower in ['RUBENRUA', 'RubenRua', 'RubenruA', 'rubenrua']:
            conf.set('s', 'k', lower)
            self.assertEqual(conf.get_lower('s', 'k'), 'rubenrua')

        self.assertEqual(conf.get_lower('s', 'k_not_exists'), None)


    def test_get_int(self):
        conf = Conf()
        conf.set('s', 'k', '10')
        self.assertEqual(conf.get_int('s', 'k'), 10)


    def test_get_list(self):
        conf = Conf()
        self.assertEqual(conf.get_list('s', 'k'), [])

        conf.set('s', 'k', '1 2 3 4 5 6')
        self.assertEqual(conf.get_list('s', 'k'), ['1', '2', '3', '4', '5', '6'])

        conf.set('s', 'k', 'one two three')
        self.assertEqual(conf.get_list('s', 'k'), ['one', 'two', 'three'])


    def test_get_dict(self):
        conf = Conf()
        self.assertEqual(conf.get_dict('s', 'k'), {})

        conf.set('s', 'k', 'k1:v1;k2:v2;k3:v3')
        self.assertEqual(conf.get_dict('s', 'k'), {'k1': 'v1', 'k2': 'v2', 'k3': 'v3'})


    def test_track_property(self):
        track = Track()
        track.name = 'name'
        self.assertEqual(track.name, 'name')
        self.assertEqual(track['name'], 'name')


    def test_get_hostname(self):
        conf = Conf()
        conf.set('config', 'ingest', None)
        conf.set('basic', 'admin', 'True')
        self.assertEqual('GCMobile-' + socket.gethostname(), conf.get_hostname())
        self.assertEqual(1, len(conf.get_tracks_in_mh_dict()))
        self.assertEqual({'capture.device.names': 'defaults'}, conf.get_tracks_in_mh_dict())
        conf.set('basic', 'admin', 'False')
        self.assertEqual('GC-' + socket.gethostname(), conf.get_hostname())


    def test_active_tag_default_profile(self):
        conf_file = get_resource('conf/conf_active.ini')
        dist_file = get_resource('conf/conf-dist.ini')
        conf = Conf(conf_file, dist_file)

        profile = conf.get_current_profile()

        self.assertEqual(1, len(profile.tracks))
