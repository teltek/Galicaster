# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/repository
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.



"""
Unit tests for `galicaster.repository` module.
"""
import os
from shutil import rmtree
from tempfile import mkdtemp, mkstemp
from unittest import TestCase

from galicaster.mediapackage import repository
from galicaster.mediapackage import mediapackage
from galicaster.utils.mhhttpclient import MHHTTPClient

class TestFunctions(TestCase):

    baseDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'mediapackage')
    path_track1 = os.path.join(baseDir, 'SCREEN.mpeg')
    path_track2 = os.path.join(baseDir, 'CAMERA.mpeg')
    path_catalog = os.path.join(baseDir, 'episode.xml') 
    path_attach = os.path.join(baseDir, 'attachment.txt')
    path_other = os.path.join(baseDir, 'manifest.xml')

    def setUp(self):
        self.track1 = mediapackage.Track(uri = self.path_track1, duration = 532, 
                                         flavor = "presentation/source", mimetype = "video/mpeg")
        self.track2 = mediapackage.Track(uri = self.path_track2, duration = 532, 
                                         flavor = "presenter/source", mimetype = "video/mpeg")
        self.catalog = mediapackage.Catalog(uri = self.path_catalog, flavor = "catalog/source", 
                                            mimetype = "text/xml")
        self.tmppath = mkdtemp()

    def tearDown(self):
        rmtree(self.tmppath)


    def test_create_repository(self):
        repo = repository.Repository()
        self.assertTrue(repo.root, os.path.expanduser('~/Repository'))
        self.assertTrue(repo.get_attach_path(), os.path.expanduser('~/Repository/attach'))
        root = '/tmp'
        repo = repository.Repository(root)
        self.assertTrue(os.path.isdir('/tmp/attach/'))
        root = '/tmp/AAA'
        repo = repository.Repository(root)
        self.assertTrue(os.path.isdir('/tmp/AAA/attach/'))
        

    def test_repository(self):
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')
        repo = repository.Repository(root)
        self.assertEqual(repo.size(), 1)


    def test_big_repository(self):
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'repository')
        repo = repository.Repository(root)
        self.assertEqual(len(repo), 5)
        self.assertEqual(len(repo.list_by_status(mediapackage.FAILED)), 1)

        for (key, mp) in repo.items():
            self.assertTrue(mp.getDuration() >= 0)

        self.assertEqual(repo["dae91194-2114-481b-8908-8a8962baf8da"].getIdentifier(), 
                         "dae91194-2114-481b-8908-8a8962baf8da")

        self.assertFalse(repo.get("dae91194-2114-481b-8908-8a8962baf8da").manual)
        self.assertTrue(repo.get("dae91194-2114-481b-8908-8a8962baf8db").manual)
        self.assertFalse(repo.get("dae91194-2114-481b-8908-8a8962baf8dd").manual)
        self.assertTrue(repo.get("dae91194-2114-481b-8908-8a8962baf8de").manual)

        self.assertEqual(repo.get("dae91194-2114-481b-8908-8a8962baf8da").status, mediapackage.SCHEDULED)
        self.assertEqual(repo.get("dae91194-2114-481b-8908-8a8962baf8db").status, mediapackage.RECORDING)
        self.assertEqual(repo.get("dae91194-2114-481b-8908-8a8962baf8dc").status, mediapackage.PENDING)
        self.assertEqual(repo.get("dae91194-2114-481b-8908-8a8962baf8dd").status, mediapackage.FAILED)
        self.assertEqual(repo.get("dae91194-2114-481b-8908-8a8962baf8de").status, mediapackage.RECORDED)

        mp_duration = repo.get("dae91194-2114-481b-8908-8a8962baf8da").getDuration()
        self.assertEqual(mp_duration, 2106)
        track_duration = repo.get("dae91194-2114-481b-8908-8a8962baf8da").getTrack("track-1").getDuration()
        self.assertEqual(track_duration, 2160)
        

    def test_add(self):
        repo = repository.Repository(self.tmppath)

        mp = mediapackage.Mediapackage()
        mp.add(self.track1)
        mp.add(self.track2)
        mp.add(self.catalog)

        repo.add(mp)
        self.assertRaises(KeyError, repo.add, mp)
        self.assertEqual(repo.size(), 1)


    def test_update(self):
        repo = repository.Repository(self.tmppath)

        mp = mediapackage.Mediapackage()
        mp.add(self.track1)
        mp.add(self.track2)
        mp.add(self.catalog)
        mp.metadata_episode["title"] = "Title"

        self.assertRaises(KeyError, repo.update, mp)

        repo.add(mp)
        self.assertEqual(repo.size(), 1)

        mp.metadata_episode["title"] = "new Title"

        repo.update(mp)
        self.assertEqual(repo.size(), 1)


    def test_delete(self):
        repo = repository.Repository(self.tmppath)

        mp = mediapackage.Mediapackage()
        mp.add(self.track1)
        mp.add(self.track2)
        mp.add(self.catalog)
        mp.metadata_episode["title"] = "Title"

        repo.add(mp)
        self.assertEqual(repo.size(), 1)

        repo.delete(mp)
        self.assertEqual(repo.size(), 0)
        self.assertEqual(len(os.listdir(self.tmppath)), 1) #attach


    def test_bad_delete(self):
        repo = repository.Repository(self.tmppath)

        mp = mediapackage.Mediapackage()
        mp.add(self.track1)
        mp.add(self.track2)
        mp.add(self.catalog)
        mp.metadata_episode["title"] = "Title"

        self.assertRaises(KeyError, repo.delete, mp)


    def test_bad_add_and_update(self):
        pass


    def test_add_after_rec_manual(self):
        duration = 134
        repo = repository.Repository(self.tmppath)
        mp = mediapackage.Mediapackage()
        #TODO file extension to mimetype???
        bins = [{'name': 'name1', 'dev': 'dev1', 'file' : mkstemp('t.avi')[1], 'klass': 'klass1', 'options': {'flavor': 'presenter' }},
                {'name': 'name2', 'dev': 'dev2', 'file' : mkstemp('t.mp4')[1], 'klass': 'klass2', 'options': {'flavor': 'presentation' }}
                ]

        self.assertTrue(mp.manual)        
        repo.add_after_rec(mp, bins, duration)

        self.assertEqual(mp.getDuration(), duration)
        self.assertEqual(len(repo), 1)
        self.assertEqual(len(mp.getTracks()), len(bins))


    def test_add_after_rec_no_manual(self):
        duration = 134
        repo = repository.Repository(self.tmppath)
        mp = mediapackage.Mediapackage()
        repo.add(mp)
        mp.addAttachmentAsString('capture.device.names=name1,name3', name='org.opencastproject.capture.agent.properties', identifier='org.opencastproject.capture.agent.properties')

        mp.manual = False
        #TODO file extension to mimetype???
        bins = [{'name': 'name1', 'dev': 'dev1', 'file' : mkstemp('t.avi')[1], 'klass': 'klass1', 'options': {'flavor': 'presenter' }},
                {'name': 'name2', 'dev': 'dev2', 'file' : mkstemp('t.mp4')[1], 'klass': 'klass2', 'options': {'flavor': 'presentation' }}
                ]

        self.assertFalse(mp.manual)        
        repo.add_after_rec(mp, bins, duration)

        self.assertEqual(mp.getDuration(), duration)
        self.assertEqual(len(repo), 1)
        self.assertEqual(len(mp.getTracks()), 1)
