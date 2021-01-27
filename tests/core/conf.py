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
import shutil
import os
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError
from unittest import TestCase

from tests import get_resource
from galicaster.core.conf import Conf
from galicaster.core.conf import Profile
from galicaster.core.conf import Track


class TestFunctions(TestCase):

    def setUp(self):
        self.conf_file = get_resource('conf/conf.ini')
        self.backup_conf_file =get_resource('conf/conf.backup.ini')
        dist_file = get_resource('conf/conf-dist.ini')

        shutil.copyfile(self.conf_file,self.backup_conf_file)
        self.conf = Conf(self.conf_file,dist_file)
        self.conf.reload()

    def tearDown(self):
        shutil.copyfile(self.backup_conf_file,self.conf_file)
        os.remove(self.backup_conf_file)
        del self.conf


    def touch(self, fname, times=None):
        with open(fname, 'a'):
            os.utime(fname, times)

    def test_init_no_file(self):
        primary_conf = os.path.join('/etc/galicaster','conf.ini')
        secondary_conf = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'conf.ini'))
        secondary_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'conf-dist.ini'))
        # Conf loads default conf and conf-dist
        conf = Conf(conf_dist_file=secondary_dist)
        self.assertEqual( primary_conf if os.path.isfile(primary_conf) else secondary_conf,
                          conf.conf_file)
        self.assertEqual( secondary_dist,
                          conf.conf_dist_file)

    def test_init_all_files(self):
        conf_file = get_resource('conf/conf.ini')
        conf_dist_file = get_resource('conf/conf-dist.ini')
        conf = Conf(conf_file, conf_dist_file)
        self.assertEqual(conf_file, conf.conf_file)
        self.assertEqual(conf_dist_file, conf.conf_dist_file)


    def test_invalid_ini(self):
        conf_file = get_resource('conf/conf.ini')
        conf_dist_file = get_resource('conf/conf_dist.ini')
        profiles_dir = get_resource('conf/profiles')
        conf = Conf(conf_file, conf_dist_file, profiles_dir)
        conf.reload()
        old_conf = self.conf.get_all()

        content = ''
        with open(get_resource('conf/conf.ini'), 'r') as content_file:
                content = content_file.read()

        # Override conf file
        f = open(get_resource('conf/conf.ini'),'w')
        f.write('testing wrong config file')
        f.close()

        conf_dist_file = get_resource('conf/conf_dist.ini')
        profiles_dir = get_resource('conf/profiles')
        conf = Conf(conf_file, conf_dist_file, profiles_dir)
        conf.reload()
        new_conf = self.conf.get_all()

        self.assertEqual(old_conf, new_conf)

        # Override conf file
        f = open(get_resource('conf/conf.ini'),'w')
        f.write(content)
        f.close()


    def test_active_tag_default_profile(self):
        conf_file = get_resource('conf/conf_active.ini')
        backup_conf_active = get_resource('conf/conf_active.backup.ini')
        dist_file = get_resource('conf/conf-dist.ini')

        shutil.copyfile(conf_file, backup_conf_active)
        conf = Conf(conf_file, dist_file)
        conf.reload()
        profile = conf.get_current_profile()
        self.assertEqual(1, len(profile.tracks))
        shutil.copyfile(backup_conf_active, conf_file)
        os.remove(backup_conf_active)

    def test_profile_with_no_profiles_in_files(self):
        conf_file = get_resource('conf/conf.ini')
        conf_dist_file = get_resource('conf/conf_dist.ini')
        profiles_dir = get_resource('conf/profiles')
        conf = Conf(conf_file, conf_dist_file, profiles_dir)
        conf.reload()
        self.assertEqual(len(conf.get_profiles()), 1)


    def test_get_and_set(self):
        # GET data in conf-dist
        self.assertEqual('full', self.conf.get('ingest', 'workflow'))
        # GET data in conf
        self.assertEqual('track1', self.conf.get('track1', 'name'))
        # SET
        self.conf.set('section', 'key', 'value')
        self.assertEqual('value', self.conf.get('section', 'key'))


    def test_get_all(self):
        full = self.conf.get_all()
        user_conf = self.conf.get_all(False)
        self.assertTrue(len(full) > len(user_conf))


    def test_reload(self):
        self.conf.set('basic', 'temp', 'temporary')
        self.assertEqual('temporary', self.conf.get('basic', 'temp'))
        self.conf.set('basic', 'temp', 'newtemporary')
        self.assertEqual('newtemporary', self.conf.get('basic', 'temp'))
        self.conf.remove_option('basic', 'temp')
        self.assertEqual(None, self.conf.get('basic', 'temp'))
        self.conf.reload()
        self.assertEqual('newtemporary', self.conf.get('basic', 'temp'))


    def test_get_tracks_in_oc_dict(self):
        conf = self.conf.get_tracks_in_oc_dict()
        self.assertEqual(len(conf), 3*3 +1)
        self.assertEqual(conf['capture.device.names'], 'track1,track3,track2')
        self.assertEqual(conf['capture.device.track2.outputfile'], 'SCREEN.mpeg')
        self.assertEqual(conf['capture.device.track2.src'], '/dev/null')


    def test_init_track(self):
        track = Track()
        self.assertEqual(track.name, '')
        self.assertEqual(track.device, '')
        self.assertEqual(track.flavor, '')
        self.assertEqual(track.location, '')
        self.assertEqual(track.file, '')
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

        self.assertEqual(list(track.keys()), ['name', 'device', 'flavor', 'location', 'file'])
        self.assertEqual(list(track.values()), ['v_name', 'v_device', 'v_flavor', 'v_location', 'v_file'])
        self.assertEqual(track.basic(), {'name': 'v_name', 'device': 'v_device',
                                        'flavor': 'v_flavor', 'location': 'v_location',
                                        'file': 'v_file'})
        self.assertEqual(track.options(), {})


    def test_add_and_del_value_in_track(self):
        track = Track()
        track['new_key'] = 'new_value'
        self.assertEqual(len(track), 6)
        self.assertEqual(track['new_key'], 'new_value')
        self.assertEqual(list(track.keys()), ['name', 'device', 'flavor', 'location', 'file', 'new_key'])
        self.assertEqual(list(track.values()), ['', '', '', '', '', 'new_value'])
        self.assertEqual(track.basic(), {'name': '', 'device': '', 'flavor': '',
                                        'location': '', 'file': ''})
        self.assertEqual(track.options(), {'new_key': 'new_value'})

        del track['new_key']
        self.assertEqual(len(track), 5)
        self.assertEqual(list(track.keys()), ['name', 'device', 'flavor', 'location', 'file'])
        self.assertEqual(list(track.values()), ['', '', '', '', ''])
        self.assertEqual(track.basic(), {'name': '', 'device': '', 'flavor': '',
                                         'location': '', 'file': ''})
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
        for yes in ['True', 'true', 'yes', 'si', 'y', 'OK', 'Y', 'TRUE']:
            self.conf.set('s', 'k', yes)
            self.assertTrue(self.conf.get_boolean('s', 'k'), 'Check if {0} is True'.format(yes))

        for no in ['None', 'not', 'False', 'no', 'n']:
            self.conf.set('s', 'k', no)
            self.assertFalse(self.conf.get_boolean('s', 'k'), 'Check if {0} is False'.format(no))

        self.conf.set('s', 'k', "1")
        self.assertFalse(self.conf.get_boolean('s', 'k', False))

    def test_get_lower(self):
        for lower in ['RUBENRUA', 'RubenRua', 'RubenruA', 'rubenrua']:
            self.conf.set('s', 'k', lower)
            self.assertEqual(self.conf.get_lower('s', 'k'), 'rubenrua')

        self.assertEqual(self.conf.get_lower('s', 'k_not_exists', None), None)

        self.conf.set('s', 'k', 'TEST')
        self.assertEqual(self.conf.get_lower('s', 'k'), 'test')

        self.conf.set('s', 'k2', "1234")
        self.assertEqual(self.conf.get_lower('s', 'k2', 'testing'), 'testing')


    def test_get_int(self):
        self.conf.set('s', 'k', '10')
        self.assertEqual(self.conf.get_int('s', 'k'), 10)

      #  self.conf.set('s', 'k2', 'test')
      #  self.assertEqual(self.conf.get_int('s', 'k2', 20), 20)


    def test_get_hour(self):
        self.conf.set('s', 'k', '12:34')
        self.assertEqual(self.conf.get_hour('s', 'k'), '12:34')

        self.conf.set('s', 'k2', 'test')
        self.assertEqual(self.conf.get_hour('s', 'k2', '11:11'), '11:11')


    def test_get_list(self):
        self.assertEqual(self.conf.get_list('s', 'k'), [])

        self.conf.set('s', 'k', '1 2 3 4 5 6')
        self.assertEqual(self.conf.get_list('s', 'k'), ['1', '2', '3', '4', '5', '6'])

        self.conf.set('s', 'k', 'one two three')
        self.assertEqual(self.conf.get_list('s', 'k'), ['one', 'two', 'three'])


    def test_get_choice(self):
        self.assertEqual(self.conf.get_choice('s', 'k', ['1','2','3'], '2'), '2')

        self.conf.set('s', 'k', '1')
        self.assertEqual(self.conf.get_choice('s', 'k', ['1','2','3']), '1')

        self.conf.set('s', 'k', 'TEST')
        self.assertEqual(self.conf.get_choice('s', 'k', ['1','2','3', 'test']), 'test')


    def test_get_choice_uppercase(self):
        self.assertEqual(self.conf.get_choice_uppercase('s', 'k', ['1','2','3'], '2'), '2')

        self.conf.set('s', 'k', '1')
        self.assertEqual(self.conf.get_choice_uppercase('s', 'k', ['1','2','3']), '1')

        self.conf.set('s', 'k', 'test')
        self.assertEqual(self.conf.get_choice_uppercase('s', 'k', ['1','2','3', 'TEST']), 'TEST')


    def test_get_dict(self):
        self.assertEqual(self.conf.get_dict('s', 'k'), {})

        self.conf.set('s', 'k', 'k1:v1;k2:v2;k3:v3')
        self.assertEqual(self.conf.get_dict('s', 'k'), {'k1': 'v1', 'k2': 'v2', 'k3': 'v3'})


    def test_get_json(self):
        self.assertEqual(self.conf.get_json('s', 'k'), {})

        self.conf.set('s', 'k', '{"a":{"a1":"value1", "a2":"value2"},"b": "value3"}')
        self.assertEqual(self.conf.get_json('s', 'k'), {"a": {"a1": "value1", "a2": "value2"}, "b": "value3"})


    def test_track_property(self):
        track = Track()
        track.name = 'name'
        self.assertEqual(track.name, 'name')
        self.assertEqual(track['name'], 'name')


    def test_get_hostname(self):
        conf = Conf(self.conf_file)
        conf.set('config', 'ingest', "None")
        conf.set('basic', 'admin', 'True')
        conf.set('ingest', 'hostname', "None")
        self.assertEqual('GCMobile-' + socket.gethostname(), conf.get_hostname())
        self.assertEqual(1, len(conf.get_tracks_in_oc_dict()))
        self.assertEqual({'capture.device.names': 'defaults'}, conf.get_tracks_in_oc_dict())
        conf.set('basic', 'admin', 'False')
        conf.set('ingest', 'hostname', None)
        self.assertEqual('GC-' + socket.gethostname(), conf.get_hostname())
        name = "123456_654321"
        conf.set('ingest', 'hostname', name)
        self.assertEqual(name, conf.get_hostname())
        a = conf.remove_option('ingest', 'hostname')


    def test_get_ip_address(self):
        valid = True
        try:
            addr = self.conf.get_ip_address()
            socket.inet_aton(addr)
        except socket.error:
            valid = False
        self.assertTrue(valid)


    def test_set_section(self):
        self.assertEqual(self.conf.set_section(None, {}), False)
        self.assertEqual(self.conf.set_section('k', {"a": "1", "b" :"2"}), True)

    def test_get_section(self):
        self.assertEqual(self.conf.set_section('k', {"a": "1", "b" :"2"}), True)
        self.assertEqual(self.conf.get_section('k'), {"a": "1", "b" :"2"})
        self.assertEqual(self.conf.get_section('kkkkkk'), {})


    def test_get_user_section(self):
        self.assertEqual(self.conf.set_section('k', {"a": "1", "b" :"2"}), True)
        self.assertEqual(self.conf.get_user_section('k'), {"a": "1", "b" :"2"})
        self.assertEqual(self.conf.get_user_section('kkkkkk'), {})

    def test_get_sections(self):
        self.conf.remove_sections()
        self.assertEqual(self.conf.get_sections(), ['basic'])
        self.assertEqual(self.conf.get_user_sections(), [])

    def test_get_modules(self):
        self.assertEqual(self.conf.get_modules(), ['recorder', 'scheduler'])
        self.conf.set('basic', 'admin', 'True')
        self.assertEqual(self.conf.get_modules(), ['recorder', 'scheduler', 'media_manager', 'player'])
        self.conf.set('ingest', 'active', 'True')
        self.assertEqual(self.conf.get_modules(), ['recorder', 'scheduler', 'media_manager', 'player', 'ocservice'])

    def test_get_color_style(self):
        self.assertEqual(self.conf.get_color_style(), False)
        self.conf.set('color', 'classic', 'True')
        self.assertTrue(self.conf.get_color_style())

    def test_get_free_profile(self):
        profile_name = self.conf.get_free_profile()
        self.assertEqual(profile_name, self.conf.get_free_profile())
        self.touch(profile_name)
        self.assertNotEqual(profile_name, self.conf.get_free_profile())
        os.remove(profile_name)


    def test_get_palette(self):
        self.conf.set('color', 'none', "None")
        self.conf.set('color','nightly', "None")
        self.conf.set('color','pending', "None")
        self.conf.set('color','processing', "None")
        self.conf.set('color','done', "None")
        self.conf.set('color','failed', "None")
        self.assertEqual(self.conf.get_palette(), [None, None, None, None, None, None])

        self.conf.set('color', 'none', "#FFFFF0")
        self.conf.set('color','nightly', "#FFFFF1")
        self.conf.set('color','pending', "#FFFFF2")
        self.conf.set('color','processing', "#FFFFF3")
        self.conf.set('color','done', "#FFFFF4")
        self.conf.set('color','failed', "#FFFFF5")
        self.assertEqual(self.conf.get_palette(), ["#FFFFF0", "#FFFFF1", "#FFFFF2", "#FFFFF3", "#FFFFF4", "#FFFFF5"])

    def test_export_to_file(self):
        p_name = list(self.conf.get_profiles().keys())[0]
        p = self.conf.get_profiles()[p_name]

        p.path = "/tmp/test_profile1.ini"
        p.export_to_file()
        self.assertTrue(os.path.exists(p.path))
        os.remove(p.path)
