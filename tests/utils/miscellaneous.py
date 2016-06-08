# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/utils/miscellaneous
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
import urllib, mimetypes

from unittest import TestCase
from nose.plugins.attrib import attr
from galicaster.core import context
from galicaster import __version__

conf = context.get_conf()
from galicaster.utils import miscellaneous


class TestFunctions(TestCase):
    
    def setUp(self):
        self.conf = conf

    def tearDown(self):
        del self.conf

    @attr('notravis')
    def test_screenshot(self):
        pb = miscellaneous.get_screenshot_as_pixbuffer()
        ifile = tempfile.NamedTemporaryFile(suffix='.png')
        pb.savev(ifile.name, "png", [], ["100"])
        imagefile = open(ifile.name, 'r')
        self.assertIsNotNone(imagefile)

        # TODO: use https://github.com/ahupp/python-magic ??
        # Check 1
        url = urllib.pathname2url(imagefile.name)
        self.assertEqual(mimetypes.guess_type(url)[0], 'image/png')
        # Check 2
        mimeType = subprocess.check_output(['file', '-ib', imagefile.name]).strip()
        self.assertTrue('image/png' in mimeType)

    def test_get_footer(self):
        self.assertEqual(miscellaneous.get_footer(), "Galicaster "+ __version__ + "  -  " + self.conf.get_hostname())
