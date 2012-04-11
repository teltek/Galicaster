# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/serializer
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


"""
Unit tests for `galicaster.serializer` module.
"""
from os import path
from xml.dom import minidom
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError
from unittest import TestCase

from galicaster.mediapackage import repository
from galicaster.mediapackage import mediapackage
from galicaster.mediapackage import serializer



class TestFunctions(TestCase):
    
    baseDir = path.join(path.dirname(path.abspath(__file__)), 'resources', 'mediapackage')
    path_track1 = path.join(baseDir, 'SCREEN.mpeg')
    path_track2 = path.join(baseDir, 'CAMERA.mpeg')
    path_catalog = path.join(baseDir, 'episode.xml') 
    path_attach = path.join(baseDir, 'attachment.txt')
    path_other = path.join(baseDir, 'manifest.xml')
    
    def setUp(self):
        self.track1 = mediapackage.Track(uri = self.path_track1, duration = 532, 
                                         flavor = "presentation/source", mimetype = "video/mpeg")
        self.track2 = mediapackage.Track(uri = self.path_track2, duration = 532, 
                                         flavor = "presenter/source", mimetype = "video/mpeg")
        self.catalog = mediapackage.Catalog(uri = self.path_catalog, flavor = "dublincore/episode", 
                                            mimetype = "text/xml")
        
    def tearDown(self):
        del self.track1
        del self.track2
        del self.catalog
        

    def test_serializer(self):
        mp = mediapackage.Mediapackage()
        mp.add(self.track1)
        mp.add(self.track2)
        mp.add(self.catalog)
        mp.status = mediapackage.PENDING
        mp.notes = u"Nota de Prueba <?php Caracteres ñ I'm raros >"

        try:
            parseString(serializer.set_manifest(mp))
        except ExpatError:
            raise AssertionError("Error in serializer.set_manifest")

        try:
            parseString(serializer.set_episode(mp))
        except ExpatError:
            raise AssertionError("Error in serializer.set_episode")

        try:
            parseString(serializer.set_properties(mp))
        except ExpatError:
            raise AssertionError("Error in serializer.set_properties")



    def test_save_in_zip(self):
        mp = mediapackage.Mediapackage()
        mp.add(self.track1)
        mp.add(self.track2)
        mp.add(self.catalog)
        mp.marshalDublincore()

        da = minidom.parseString(serializer.set_episode(mp))
        db = minidom.parse(self.path_catalog)

        for name in ["dcterms:title", "dcterms:identifier", "dcterms:created"]:
            try:
                self.assertEqual(da.getElementsByTagName(name)[0].firstChild.wholeText.strip().strip("\n"), 
                                 db.getElementsByTagName(name)[0].firstChild.wholeText.strip().strip("\n"))
            except IndexError:
                continue

