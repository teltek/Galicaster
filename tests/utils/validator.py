# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/utils/validator
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
from unittest import TestCase
from os import path

from galicaster.utils import validator

class TestFunctions(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_fill_track(self):
        track = {'device': 'videotest'}
        error, valid_track = validator.validate_track(track)
        self.assertEqual(error, None)
        self.assertTrue('name' in valid_track)
        self.assertTrue('flavor' in valid_track)
        self.assertTrue('location' in valid_track)
        self.assertTrue('file' in valid_track)
        self.assertTrue('caps' in valid_track)
        self.assertTrue('pattern' in valid_track)
        self.assertTrue('color1' in valid_track)
        self.assertTrue('color2' in valid_track)
        self.assertTrue('videoencoder' in valid_track)
        self.assertTrue('muxer' in valid_track)
        self.assertTrue('videosink' in valid_track)

    def test_validate_with_params(self):
        track = {'pattern': '10'}
        gc_params = { "pattern": {
            "type": "integer",
            "default": 0,
            "range": (0,20),
            "description": "Background pattern"}
        }
        error, valid_track = validator.validate_track(track, gc_params)
        self.assertEqual(error, None)

        # Invalid
        track['pattern'] = 'nonumber'
        error, valid_track = validator.validate_track(track, gc_params)
        self.assertNotEqual(error, None)
        self.assertEqual(valid_track['pattern'], 0)


    def test_validate_integer(self):
        track = {'device': 'videotest'}
        error, valid_track = validator.validate_track(track)
        self.assertEqual(error, None)

        # Valid
        track['pattern'] = '10'
        error, valid_track = validator.validate_track(track)
        self.assertEqual(error, None)
        self.assertEqual(valid_track['pattern'], 10)

        # Out of range
        track['pattern'] = '-10'
        error, valid_track = validator.validate_track(track)
        self.assertNotEqual(error, None)
        self.assertEqual(valid_track['pattern'], 0)

        # Invalid
        track['pattern'] = 'nonumber'
        error, valid_track = validator.validate_track(track)
        self.assertNotEqual(error, None)
        self.assertEqual(valid_track['pattern'], 0)


    def test_validate_float(self):
        track = {'device': 'audiotest'}
        error, valid_track = validator.validate_track(track)
        self.assertEqual(error, None)

        # Valid
        track['amplification'] = '2.0'
        error, valid_track = validator.validate_track(track)
        self.assertEqual(error, None)
        self.assertEqual(valid_track['amplification'], 2.0)

        # Out of range
        track['amplification'] = '-1.0'
        error, valid_track = validator.validate_track(track)
        self.assertNotEqual(error, None)
        self.assertEqual(valid_track['amplification'], 1.0)

        # Invalid
        track['amplification'] = 'nonumber'
        error, valid_track = validator.validate_track(track)
        self.assertNotEqual(error, None)
        self.assertEqual(valid_track['amplification'], 1.0)


    def test_validate_hexadecimal(self):
        track = {'device': 'screen'}
        error, valid_track = validator.validate_track(track)
        self.assertEqual(error, None)

        # Valid
        track['xid'] = '0x65CB00'
        error, valid_track = validator.validate_track(track)
        self.assertEqual(error, None)
        self.assertEqual(valid_track['xid'], 0x65CB00)

        # Out of range
        track['xid'] = '0xFFFFFG'
        error, valid_track = validator.validate_track(track)
        self.assertNotEqual(error, None)
        self.assertEqual(valid_track['xid'], 0)

        # Invalid
        track['xid'] = 'nonumber'
        error, valid_track = validator.validate_track(track)
        self.assertNotEqual(error, None)
        self.assertEqual(valid_track['xid'], 0)


    def test_validate_boolean(self):
        track = {'device': 'audiotest'}
        error, valid_track = validator.validate_track(track)
        self.assertEqual(error, None)

        # Valid
        track['player'] = 'True'
        error, valid_track = validator.validate_track(track)
        self.assertEqual(error, None)
        self.assertEqual(valid_track['player'], True)

        # Invalid
        track['player'] = 'noboolean'
        error, valid_track = validator.validate_track(track)
        self.assertNotEqual(error, None)
        self.assertEqual(valid_track['player'], 'True')


    def test_validate_flavor(self):
        track = {'device': 'videotest'}
        error, valid_track = validator.validate_track(track)
        self.assertEqual(error, None)

        # Valid
        track['flavor'] = 'presentation'
        error, valid_track = validator.validate_track(track)
        self.assertEqual(error, None)
        self.assertEqual(valid_track['flavor'], 'presentation')

        # Invalid
        track['flavor'] = 'noflavor'
        error, valid_track = validator.validate_track(track)
        self.assertNotEqual(error, None)
        self.assertEqual(valid_track['flavor'], 'presenter')

        # Valid (Test custom flavors)
        from galicaster.core import context as gc_context
        gc_conf = gc_context.get_conf()
        gc_conf.set('basic', 'custom_flavors', 'myflavor') # Add myflavor to list of valid flavors

        track['flavor'] = 'myflavor'
        error, valid_track = validator.validate_track(track)
        self.assertEqual(error, None)
        self.assertEqual(valid_track['flavor'], 'myflavor')


    def test_validate_select(self):
        track = {'device': 'videotest'}
        error, valid_track = validator.validate_track(track)
        self.assertEqual(error, None)

        # Valid
        track['videosink'] = 'fakesink'
        error, valid_track = validator.validate_track(track)
        self.assertEqual(error, None)
        self.assertEqual(valid_track['videosink'], 'fakesink')

        # Invalid
        track['videosink'] = 'novideosink'
        error, valid_track = validator.validate_track(track)
        self.assertNotEqual(error, None)
        self.assertEqual(valid_track['videosink'], 'xvimagesink')


    def test_validate_list(self):
        track = {'listparam': '[1,2,3,4]'}
        gc_params = { "listparam": {
            "type": "list",
            "default": []}
        }

        error, valid_track = validator.validate_track(track, gc_params)
        self.assertEqual(error, None)

        # Valid
        track['listparam'] = [1,2,3,4,5,6]
        error, valid_track = validator.validate_track(track, gc_params)
        self.assertEqual(error, None)

        # Invalid
        track['listparam'] = 'nolist'
        error, valid_track = validator.validate_track(track, gc_params)
        self.assertNotEqual(error, None)
        self.assertEqual(valid_track['listparam'], [])


    def test_validate_dict(self):
        track = {'dictparam': '{"1":"2","3":"4"}'}
        gc_params = { "dictparam": {
            "type": "dict",
            "default": {}}
        }

        error, valid_track = validator.validate_track(track, gc_params)
        self.assertEqual(error, None)
        self.assertEqual(valid_track['dictparam'], {'1':'2','3':'4'})

        # Valid
        track['dictparam'] = {1:2,3:4,5:6}
        error, valid_track = validator.validate_track(track, gc_params)
        self.assertEqual(error, None)
        self.assertEqual(valid_track['dictparam'], {1:2,3:4,5:6})

        # Invalid
        track['dictparam'] = 'nodict'
        error, valid_track = validator.validate_track(track, gc_params)
        self.assertNotEqual(error, None)
        self.assertEqual(valid_track['dictparam'], {})


    def test_validate_caps(self):
        track = {'device': 'videotest',
                 'caps': 'video/x-raw,framerate=20/1,width=640,height=480'}
        error, valid_track = validator.validate_track(track)
        self.assertEqual(error, None)

        #TODO: ...


    def test_validate_unknown_type(self):
        track = {'pattern': None}
        gc_params = { "pattern": {
            "type": "unknown",
            "default": 0,
            "range": (0,20),
            "description": "Background pattern"}
        }
        error, valid_track = validator.validate_track(track, gc_params)
        self.assertEqual(error, None)
        self.assertEqual(valid_track['pattern'], 0)
