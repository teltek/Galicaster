# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/mediapackage/serializer
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
import zipfile
import json
from os import path,remove
from shutil import rmtree
from tempfile import mkdtemp, mkstemp
from xml.dom import minidom
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError
from unittest import TestCase
from unittest import skip

from tests import get_resource
from galicaster.mediapackage import repository
from galicaster.mediapackage import mediapackage
from galicaster.mediapackage import serializer


class TestFunctions(TestCase):
    
    baseDir = get_resource('mediapackage')
    path_track1 = path.join(baseDir, 'SCREEN.mpeg')
    path_track2 = path.join(baseDir, 'CAMERA.mpeg')
    path_catalog = path.join(baseDir, 'episode.xml') 
    path_attach = path.join(baseDir, 'attachment.txt')
    path_other = path.join(baseDir, 'manifest.xml')
    path_gc = path.join(baseDir, 'galicaster.xml')

    def setUp(self):
        self.track1 = mediapackage.Track(uri = self.path_track1, duration = 532, 
                                         flavor = "presentation/source", mimetype = "video/mpeg")
        self.track2 = mediapackage.Track(uri = self.path_track2, duration = 532, 
                                         flavor = "presenter/source", mimetype = "video/mpeg")
        self.catalog = mediapackage.Catalog(uri = self.path_catalog, flavor = "dublincore/episode", 
                                            mimetype = "text/xml")
        self.gc_catalog = mediapackage.Catalog(uri = self.path_gc, flavor = "galicaster", 
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
        mp.status = mediapackage.SCHEDULED
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
            json.loads(serializer.set_properties(mp))
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

    def test_save_system_zip(self):
        mp = mediapackage.Mediapackage()
        mp.add(self.track1,mediapackage.TYPE_TRACK, "presentation/source", "video/mpeg", 532)
        mp.add(self.track2,mediapackage.TYPE_TRACK, "presenter/source", "video/mpeg", 532)
        mp.add(self.catalog,mediapackage.TYPE_CATALOG, "catalog/source","xml")
        tmppath = mkdtemp()
        repo = repository.Repository(tmppath)
        repo.add(mp)
        path_zip = "system.zip"

        serializer.save_system_zip(mp,path_zip)
        zfile = zipfile.ZipFile(path_zip,'r')
        files=zfile.namelist()
        
        for element in mp.getElements():
            self.assertTrue(path.split(element.getURI())[1] in files)
        rmtree(tmppath)
        remove(path_zip)
        
    @skip("skip")
    def test_operation_status(self):
        mp = mediapackage.Mediapackage()
        mp.add(self.track1)
        mp.operations["ingest"] = 4
        mp.marshalDublincore()
        da = minidom.parseString(serializer.set_properties(mp))
        name = "key:ingest"
        try:
            self.assertEqual(da.getElementsByTagName(name)[0].firstChild.wholeText.strip().strip("\n"), 
                             da.getElementsByTagName(name)[0].firstChild.wholeText.strip().strip("\n"))
        except IndexError:
            pass

