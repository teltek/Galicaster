# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/mediapackage/repository
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
import json
import datetime
from shutil import rmtree, copy
from tempfile import mkdtemp, mkstemp
from unittest import TestCase

from tests import get_resource
from galicaster.mediapackage import repository
from galicaster.mediapackage import mediapackage

class TestFunctions(TestCase):

    baseDir = get_resource('mediapackage')
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

        
    def get_folders_in_repository(self, d):
        folders_list = [os.path.join(d,o) for o in os.listdir(d)
                        if (os.path.isdir(os.path.join(d,o))
                            and not 'attach' in (os.path.join(d,o))
                            and not 'rectemp' in (os.path.join(d,o)))]
        return folders_list
    
        
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
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources')
        repo = repository.Repository(root)
        self.assertEqual(repo.size(), 1)


    def test_big_repository(self):
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources', 'repository')
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
        self.assertEqual(repo.get("dae91194-2114-481b-8908-8a8962baf8dc").status, mediapackage.RECORDED)
        self.assertEqual(repo.get("dae91194-2114-481b-8908-8a8962baf8dd").status, mediapackage.FAILED)
        self.assertEqual(repo.get("dae91194-2114-481b-8908-8a8962baf8de").status, mediapackage.RECORDED)

        self.assertEqual(len(repo.get("dae91194-2114-481b-8908-8a8962baf8da").operation), 0)
        self.assertEqual(len(repo.get("dae91194-2114-481b-8908-8a8962baf8db").operation), 0)
        self.assertEqual(len(repo.get("dae91194-2114-481b-8908-8a8962baf8dc").operation), 1)
        self.assertEqual(len(repo.get("dae91194-2114-481b-8908-8a8962baf8dd").operation), 2)
        self.assertEqual(len(repo.get("dae91194-2114-481b-8908-8a8962baf8de").operation), 3)

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
        self.assertEqual(len(os.listdir(self.tmppath)), 2) #attach and rectemp


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


    def __get_tmp_bin(self, name, values):
        tmp_file = mkstemp(name)[1]
        bin = {'file': os.path.basename(tmp_file), 'path': os.path.dirname(tmp_file)}
        bin.update(values)
        return bin

    def test_add_after_rec_manual(self):
        duration = 134
        repo = repository.Repository(self.tmppath)
        mp = mediapackage.Mediapackage()
        #TODO file extension to mimetype???
        bins = [self.__get_tmp_bin('t.avi', {'device': 'test', 'name': 'name1', 'dev': 'dev1', 'mimetype': 'video/mp4', 'flavor': 'presenter' }),
                self.__get_tmp_bin('t.mp4', {'device': 'test', 'name': 'name2', 'dev': 'dev2', 'mimetype': 'video/mp4', 'flavor': 'presentation' })
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
        bins = [self.__get_tmp_bin('t.avi', {'device': 'test', 'name': 'name1', 'dev': 'dev1', 'mimetype': 'video/mp4', 'flavor': 'presenter' }),
                self.__get_tmp_bin('t.mp4', {'device': 'test', 'name': 'name2', 'dev': 'dev2', 'mimetype': 'video/mp4', 'flavor': 'presentation' })
                ]

        self.assertFalse(mp.manual)        
        repo.add_after_rec(mp, bins, duration)

        self.assertEqual(mp.getDuration(), duration)
        self.assertEqual(len(repo), 1)
        self.assertEqual(len(mp.getTracks()), 1)


    def test_get_next_and_past_mediapackages(self):
        repo = repository.Repository(self.tmppath)
        now = datetime.datetime.utcnow()

        mp = mediapackage.Mediapackage(identifier="1", title='MP#1', date=(now - datetime.timedelta(days=1)))
        repo.add(mp)
        mp = mediapackage.Mediapackage(identifier="2", title='MP#2', date=(now - datetime.timedelta(days=30)))
        repo.add(mp)
        mp = mediapackage.Mediapackage(identifier="3", title='MP#3', date=(now - datetime.timedelta(days=60)))
        repo.add(mp)
        mp_next = mediapackage.Mediapackage(identifier="4", title='MP#4', date=(now + datetime.timedelta(days=1)))
        repo.add(mp_next)
        mp = mediapackage.Mediapackage(identifier="5", title='MP#5', date=(now + datetime.timedelta(days=30)))
        repo.add(mp)

        self.assertEqual(repo.get_next_mediapackage(), mp_next)
        self.assertEqual(len(repo.get_next_mediapackages()), 2)
        self.assertEqual(len(repo.get_past_mediapackages()), 3)
        self.assertEqual(len(repo.get_past_mediapackages(40)), 1)


    def test_repair_inconsistencies(self):
        repo = repository.Repository(self.tmppath)

        mp = mediapackage.Mediapackage()
        mp.status = mediapackage.RECORDED
        mp.setOpStatus("pr0", mediapackage.OP_IDLE)
        mp.setOpStatus("pr1", mediapackage.OP_PENDING)
        mp.setOpStatus("pr2", mediapackage.OP_PROCESSING)
        mp.setOpStatus("pr3", mediapackage.OP_DONE)
        mp.setOpStatus("pr4", mediapackage.OP_FAILED)

        repo.add(mp)
        repo.repair_inconsistencies(mp)
        
        self.assertEqual(mp.status, mediapackage.RECORDED)
        self.assertEqual(mp.getOpStatus("pr0"), mediapackage.OP_IDLE)
        self.assertEqual(mp.getOpStatus("pr1"), mediapackage.OP_FAILED)
        self.assertEqual(mp.getOpStatus("pr2"), mediapackage.OP_FAILED)
        self.assertEqual(mp.getOpStatus("pr3"), mediapackage.OP_DONE)
        self.assertEqual(mp.getOpStatus("pr4"), mediapackage.OP_FAILED)

        
    
    def test_repo_lifecycle(self):
        repo = repository.Repository(self.tmppath)

        mp = mediapackage.Mediapackage()
        mp.title = 'lifecycle test MP'
        self.assertEqual(len(repo), 0)

        repo.add_after_rec(mp, [], 30)
        self.assertEqual(len(repo), 1)
        
        for catalog in mp.getCatalogs():
            self.assertEqual(mp.getURI(), os.path.dirname(catalog.getURI()))
            self.assertTrue(os.path.isfile(catalog.getURI()), 
                            'The catalog path {0} not exists'.format(catalog.getURI()))


    def test_folder_name_template(self):
        repo = repository.Repository(self.tmppath, 'test', 'gc_{hostname}_m{second}')

        mp = mediapackage.Mediapackage()
        repo.add(mp)
        self.assertEqual(mp.getURI(), os.path.join(repo.root, 
          'gc_{hostname}_m{second}'.format(hostname="test", second=mp.getDate().strftime('%S'))))


    def test_folder_name_template_no_alphanumeric(self):
        repo = repository.Repository(self.tmppath, 'test', 'Foo-Bar[!!??]-{hostname}_m{second}')

        mp = mediapackage.Mediapackage()
        repo.add(mp)
        self.assertEqual(mp.getURI(), os.path.join(repo.root, 
          'FooBar{hostname}_m{second}'.format(hostname="test", second=mp.getDate().strftime('%S'))))


    def test_folder_name_template_unique(self):
        repo = repository.Repository(self.tmppath, 'test', 'test')
        
        mp1 = mediapackage.Mediapackage()
        mp2 = mediapackage.Mediapackage()
        mp3 = mediapackage.Mediapackage()

        repo.add(mp1)
        self.assertEqual(mp1.getURI(), os.path.join(repo.root, 'test'))
        repo.add(mp2)
        self.assertEqual(mp2.getURI(), os.path.join(repo.root, 'test_2'))
        repo.add(mp3)
        self.assertEqual(mp3.getURI(), os.path.join(repo.root, 'test_3'))


    def test_save_temprec_on_crash(self):
        repo = repository.Repository(self.tmppath, 'test', 'test')
        
        for file_name in ('CAMERA.avi', 'SCREEN.avi'):
            f = open(repo.get_rectemp_path(file_name), 'w')
            f.write("DATA" * 1000)
            f.close()

        open(repo.get_rectemp_path("None.avi"), 'w').close()
        
        # After crash. Create a new repo
        repo = repository.Repository(self.tmppath, 'test', 'test')
        num_files = num_backup_files = 0
        for name in os.listdir(repo.get_rectemp_path()):
            full_path = os.path.join(repo.get_rectemp_path(), name)
            if os.path.isfile(full_path) and os.path.getsize(full_path):
                num_files += 1
            if os.path.isdir(full_path):
                num_backup_files = len(os.listdir(full_path))

        self.assertEqual(num_files, 0)
        self.assertEqual(num_backup_files, 2)


    def test_recover_recording(self):
        repo_folder = get_resource('repository')
        rectemp_aux = get_resource('utils/temporal_recording')
        rectemp = get_resource('repository/rectemp')

        # Read info.json
        info = {}
        info_filename = os.path.join(rectemp_aux, 'info.json')
        with open(info_filename, 'r') as handle:
            info = json.load(handle)

        # Modify path of tracks
        for indx, track in enumerate(info['tracks']):
            info['tracks'][indx]['path'] = rectemp

        # Copy temporal files
        for temp_file in os.listdir(rectemp_aux):
            full_path = os.path.join(rectemp_aux, temp_file)
            copy(full_path, os.path.join(rectemp, temp_file))

        # Overwrite info.json with new paths
        f = open(os.path.join(rectemp, 'info.json'), 'w')
        f.write(json.dumps(info, indent=4, sort_keys=True))
        f.close()    

        # Get old length
        old_length = len(self.get_folders_in_repository(repo_folder))

        # Create the repository
        from galicaster.core import context
        logger = context.get_logger()
        repo = repository.Repository(repo_folder, '', 'gc_{hostname}_{year}-{month}-{day}T{hour}h{minute}m{second}', logger)

        # Check 1
        self.assertEqual(old_length +1 , len(self.get_folders_in_repository(repo_folder)))

        # Check 2
        mp = repo.get('4ea1049f-c946-4d36-95d4-b8d01223bd73')
        self.assertNotEqual(mp, None)
        mp_info = mp.getAsDict()
        self.assertEqual(mp_info['status'], 4)
        self.assertTrue('Recovered' in mp_info['title'])
        self.assertEqual(len(mp_info['tracks']), 2)
        
        # Clean
        for temp_file in os.listdir(rectemp):
            os.remove(os.path.join(rectemp, temp_file))
        repo.delete(mp)
