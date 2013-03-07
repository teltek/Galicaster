# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/mediapackage
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
Unit tests for `galicaster.mediapackage` module.
"""
from os import path
from unittest import TestCase

from galicaster.mediapackage import mediapackage
from galicaster.mediapackage import fromXML


class TestFunctions(TestCase):
    
    baseDir = path.join(path.dirname(path.abspath(__file__)), '..', 'resources', 'mediapackage')
    path_track1 = path.join(baseDir, 'SCREEN.mpeg')
    path_track2 = path.join(baseDir, 'CAMERA.mpeg')
    path_catalog = path.join(baseDir, 'episode.xml') 
    path_attach = path.join(baseDir, 'attachment.txt')
    path_capture_agent_properties = path.join(baseDir, 'org.opencastproject.capture.agent.properties')
    path_other = path.join(baseDir, 'manifest.xml')
    
    def setUp(self):
        self.track1 = mediapackage.Track(uri = self.path_track1, duration = 532, flavor = "presentation/source")
        self.track2 = mediapackage.Track(uri = self.path_track2, duration = 532, flavor = "presenter/source")
        self.catalog = mediapackage.Catalog(uri = self.path_catalog, flavor = "catalog/source")
        self.attach = mediapackage.Attachment(uri = self.path_attach, flavor = "attachment/source")        
        self.other = mediapackage.Other(uri = self.path_other, flavor = "other/source")
        
    def tearDown(self):
        del self.track1
        del self.track2
        del self.catalog
        del self.attach
        del self.other
    
    def test_element_instantiation(self):   
        # Check Element can't be instantiated
        self.assertRaises(RuntimeError, mediapackage.Element, self.path_track1)
        
        # Check Track
        self.assertEqual(self.track1.getElementType(), mediapackage.TYPE_TRACK)
        # Check Catalog
        self.assertEqual(self.catalog.getElementType(), mediapackage.TYPE_CATALOG)
        # Check Attachment
        self.assertEqual(self.attach.getElementType(), mediapackage.TYPE_ATTACHMENT)
        # Check Other
        self.assertEqual(self.other.getElementType(), mediapackage.TYPE_OTHER)
        
    def test_element_equality(self):
        track = mediapackage.Track(self.path_track1, 532, "presentation/source")
        attach = mediapackage.Attachment(self.path_attach, "attachment/source")
        catalog = mediapackage.Catalog(self.path_catalog, "catalog/source")
        other = mediapackage.Other(self.path_other, "other/source")
        self.assertFalse(track == self.track2)
        self.assertFalse(track == attach)
        self.assertFalse(attach == catalog)
        self.assertFalse(catalog == other)
        self.assertFalse(other == track)
        self.assertTrue(track == self.track1)
        self.assertTrue(attach == self.attach)
        self.assertTrue(catalog == self.catalog)
        self.assertTrue(other == self.other)
         
    def test_no_elements(self):
        mp = mediapackage.Mediapackage()
        self.assertEqual(len(mp.getElements()), 0)

    def test_add_uris(self):
        mp = mediapackage.Mediapackage()
        mp.add(self.path_track1, mediapackage.TYPE_TRACK, "presentation/source", None, 532)
        self.assertTrue(mp.contains(self.track1))
        mp.add(self.path_track2, mediapackage.TYPE_TRACK, "presenter/source", None, 532)
        self.assertTrue(mp.contains(self.track2))
        mp.add(self.path_catalog, mediapackage.TYPE_CATALOG, "catalog/source")
        self.assertTrue(mp.contains(self.catalog))
        mp.add(self.path_attach, mediapackage.TYPE_ATTACHMENT, "attachment/source")
        self.assertTrue(mp.contains(self.attach))
        mp.add(self.path_other, mediapackage.TYPE_OTHER, "other/source")
        self.assertTrue(mp.contains(self.other))
        self.assertEqual(len(mp.getElements()), 5)
        self.assertEqual(len(mp.getTracks()), 2)
        self.assertEqual(len(mp.getAttachments()), 1)
        self.assertEqual(len(mp.getCatalogs()), 1)
        self.assertEqual(len(mp.getUnclassifiedElements()), 1)

    def test_duration_add_track(self):
        mp = mediapackage.Mediapackage()
        mp.add(self.path_track1, mediapackage.TYPE_TRACK, "presentation/source", None, 532)
        mp.add(self.path_track2, mediapackage.TYPE_TRACK, "presenter/source", None, 1532)
        self.assertEqual(mp.getDuration(), 1532)
        
    def test_add_elements(self):
        mp = mediapackage.Mediapackage()
        mp.add(self.track1)
        self.assertTrue(mp.contains(self.track1))
        self.assertEqual(self.track1.getMediapackage(), mp)
        mp.add(self.track2)
        self.assertTrue(mp.contains(self.track2))
        self.assertEqual(self.track2.getMediapackage(), mp)
        mp.add(self.catalog)
        self.assertTrue(mp.contains(self.catalog))
        self.assertEqual(self.catalog.getMediapackage(), mp)
        mp.add(self.attach)
        self.assertTrue(mp.contains(self.attach))
        self.assertEqual(self.attach.getMediapackage(), mp)
        mp.add(self.other)
        self.assertTrue(mp.contains(self.other))
        self.assertEqual(self.other.getMediapackage(), mp)
        self.assertEqual(len(mp.getElements()), 5)
        self.assertEqual(len(mp.getTracks()), 2)
        self.assertEqual(len(mp.getAttachments()), 1)
        self.assertEqual(len(mp.getCatalogs()), 1)
        self.assertEqual(len(mp.getUnclassifiedElements()), 1)
        
        
    def test_tracks(self):
        mp = mediapackage.Mediapackage()
        file_path = path.join(self.baseDir, 'SCREEN.mpeg')
        mp.add(file_path, mediapackage.TYPE_TRACK, 'presenter/source')
        self.assertEqual(len(mp.getTracks()), 1)


    def test_no_tracks_by_flavour(self):
        mp = mediapackage.Mediapackage()
        file_path = path.join(self.baseDir, 'SCREEN.mpeg')
        mp.add(file_path, mediapackage.TYPE_TRACK, 'presenter/source')
        self.assertEqual(len(mp.getTracks('presentation/source')), 0)


    def test_no_tracks(self):
        mp = mediapackage.Mediapackage()
        file_path = path.join(self.baseDir, 'SCREEN.mpeg')
        mp.add(file_path, mediapackage.TYPE_TRACK, 'presenter/source')
        self.assertEqual(len(mp.getCatalogs()), 0)


    def test_add_tracks(self):
        mp = mediapackage.Mediapackage()
        file_path = path.join(self.baseDir, 'SCREEN.mpeg')
        mp.add(file_path, mediapackage.TYPE_TRACK, 'presenter/source')
        file_path = path.join(self.baseDir, 'CAMERA.mpeg')
        mp.add(file_path, mediapackage.TYPE_TRACK, 'presentation/source')
        file_path = path.join(self.baseDir, 'episode.xml')
        mp.add(file_path, mediapackage.TYPE_CATALOG, 'dublincore/episode')
        self.assertEqual(len(mp.getElements()), 3)


    def test_fromXML(self):        
        xml = path.join(self.baseDir, 'manifest.xml')
        mp = fromXML(xml)
        self.assertEqual(mp.title, "Opening a folder...")
        self.assertEqual(mp.getIdentifier(), "dae91194-2114-481b-8908-8a8962baf8dc")
        self.assertEqual(mp.status, 0)
        self.assertEqual(mp.properties['notes'], u"Nota de Prueba <?php Caracteres ñ I'm raros >")


    def test_mediapackage_size(self):
        xml = path.join(self.baseDir, 'manifest.xml')
        mp = fromXML(xml)
        self.assertEqual(mp.getSize(), 598)


    def test_mediapackage_get_oc_capture_agent_property(self):
        mp = mediapackage.Mediapackage()
        mp.add(self.path_capture_agent_properties, mediapackage.TYPE_ATTACHMENT, identifier='org.opencastproject.capture.agent.properties')

        self.assertEqual(mp.getOCCaptureAgentProperty('capture.device.names'), 'camera,screen,audio')
        self.assertNotEqual(mp.getOCCaptureAgentProperty('capture.device.names.error'), 'camera,screen,audio')
        
        mp2 = mediapackage.Mediapackage()
        self.assertNotEqual(mp2.getOCCaptureAgentProperty('capture.device.names'), 'camera,screen,audio')


        self.assertEqual(mp.getOCCaptureAgentProperties(), 
                         {u'org.opencastproject.workflow.config.trimHold': 'false',
                          u'capture.device.names': 'camera,screen,audio',
                          u'org.opencastproject.workflow.definition': 'full',
                          u'event.series': 'f16b43df-d1d4-4a85-8989-c060b85cea8d',
                          u'event.title': 'Clase 2',
                          u'event.location': 'GC-Etna',
                          u'org.opencastproject.workflow.config.captionHold': 'false'})


    def test_mp_and_operations(self):
        xml = path.join(self.baseDir, 'manifest.xml')
        mp = fromXML(xml)
        self.assertEqual(0, len(mp.operation))


    def test_properties(self):
        mp = mediapackage.Mediapackage()
        mp.title = 'title'
        self.assertEqual(mp.title, 'title')
        self.assertEqual(mp.metadata_episode['title'], 'title')
