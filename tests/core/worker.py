# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/core/worker
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.



"""
Unit tests for `galicaster.core.worker` module.
"""

from unittest import TestCase, skip
import os
from os import path
import tempfile
import time
import zipfile
from shutil import rmtree

from tests import get_resource
from galicaster.core import worker
from galicaster.mediapackage import mediapackage
from galicaster.mediapackage.repository import Repository
from galicaster.core.dispatcher import Dispatcher
from galicaster.core.logger import Logger


class TestFunctions(TestCase):

    baseDir = get_resource('mediapackage')
    path_capture_agent_properties = os.path.join(baseDir, 'org.opencastproject.capture.agent.properties')

    class RepoMock(object):
        def update(self, mp):
            pass

    class OCHTTPClientMock(object):
        def __init__(self):
            self.calls = []

        def ingest(self, mp_file, mp=None, workflow=None, workflow_instance=None, workflow_parameters=None):
            self.calls.append({'file': mp_file,
                               'workflow': workflow,
                               'workflow_instance': workflow_instance,
                               'workflow_parameters': workflow_parameters})

    class DispatcherMock(object):
        def connect(self, *args):
            pass
        def emit(self, *args):
            pass


    def setUp(self):
        self.logger_filename = '/tmp/galicaster_test.log'
        self.repo = self.RepoMock()
        self.client = self.OCHTTPClientMock()
        self.dispatcher = self.DispatcherMock()
        self.logger = Logger(self.logger_filename)
        self.worker = worker.Worker(self.dispatcher, self.repo, self.logger, self.client)

        self.repo1 = Repository()
        self.mp = mediapackage.Mediapackage()
        self.repo1.add(self.mp)

    def tearDown(self):
        del self.repo
        del self.client
        del self.dispatcher
        del self.logger
        del self.worker

        self.repo1.delete(self.mp)

    def test_init_parameters(self):
        self.assertEqual(self.worker.export_path, os.path.expanduser('~'))
        self.assertEqual(self.worker.tmp_path, tempfile.gettempdir())

        #self.assertRaises(OSError, worker.Worker, repo, client, '/a/b/c', None)
        #self.assertRaises(OSError, worker.Worker, repo, client, None, '/a/b/c')

        w = worker.Worker(self.dispatcher, self.repo, self.logger, self.client, '/tmp/galicaster_tdd/a/b/c', '/tmp/galicaster_tdd/1/2/3')
        self.assertEqual(w.export_path, '/tmp/galicaster_tdd/a/b/c')
        self.assertEqual(w.tmp_path, '/tmp/galicaster_tdd/1/2/3')

        for dir_path in ('/tmp/galicaster_tdd/a/b/c', '/tmp/galicaster_tdd/1/2/3'):
            self.assertTrue(os.path.isdir(dir_path))

        rmtree('/tmp/galicaster_tdd')


    def test_get_all_job_types(self):
        jtypes = self.worker.get_all_job_types()

        # Even length
        self.assertTrue(len(jtypes)%2 == 0)

        for indx, element in enumerate(jtypes):
            if indx%2 == 0:
                self.assertEqual(jtypes[indx] + ' Nightly', jtypes[indx+1])


    def test_get_ui_job_types(self):
        jtypes = self.worker.get_ui_job_types()
        jtypes_1 = jtypes[0:int(len(jtypes)/2)]
        jtypes_2 = jtypes[int(len(jtypes)/2):]

        # Even length
        self.assertTrue(len(jtypes)%2 == 0)

        for indx, element in enumerate(jtypes_2):
            jtypes_2[indx] = jtypes_2[indx].replace(' Nightly', '')

        self.assertEqual(jtypes_1, jtypes_2)


    def test_get_all_job_types_by_mp(self):
        w = worker.Worker(self.dispatcher, self.repo1, self.logger, self.client)

        daily, nighly =  w.get_all_job_types_by_mp(self.mp)

        for indx, element in enumerate(nighly):
            nighly[indx] = nighly[indx].replace(' Nightly', '')

        self.assertEqual(daily,nighly)

    def test_ui_job_types_by_mp(self):
        w = worker.Worker(self.dispatcher, self.repo1, self.logger, self.client)

        daily, nighly =  w.get_ui_job_types_by_mp(self.mp)

        for indx, element in enumerate(nighly):
            nighly[indx] = nighly[indx].replace(' Nightly', '')

        self.assertEqual(daily,nighly)

    def test_get_job_name(self):
        self.assertEqual(self.worker.get_job_name('ingest'), 'Ingest')

    def test_do_job_by_name(self):
        w = worker.Worker(self.dispatcher, self.repo1, self.logger, self.client)
        self.assertTrue(w.do_job_by_name('ingest', self.mp.getIdentifier()))
        self.assertFalse(w.do_job_by_name('inexistent_op', self.mp.getIdentifier()))

    def test_enqueue_job_by_name(self):
        w = worker.Worker(self.dispatcher, self.repo1, self.logger, self.client)

        self.assertTrue(w.enqueue_job_by_name('ingest', self.mp.getIdentifier()))
        self.assertFalse(w.enqueue_job_by_name('inexistent_op', self.mp.getIdentifier()))
        time.sleep(0.15)

    def test_do_job(self):
        w = worker.Worker(self.dispatcher, self.repo1, self.logger, self.client)

        self.assertTrue(w.do_job('ingest', self.mp))
        self.assertFalse(w.do_job('inexistent_op', self.mp))
        time.sleep(0.15)

    def test_do_job_nightly(self):
        w = worker.Worker(self.dispatcher, self.repo1, self.logger, self.client)

        self.assertTrue(w.do_job_nightly('ingest', self.mp))
        self.assertTrue(w.do_job_nightly('cancelingest', self.mp))
        self.assertFalse(w.do_job_nightly('inexistent_op', self.mp))

    @skip("Test break")
    def test_ingest_manual(self):
        mp = mediapackage.Mediapackage(uri='/tmp')
        mp.manual = True

        self.worker._ingest(mp)
        self.assertEqual(self.client.calls[0]['workflow'], None)
        self.assertEqual(self.client.calls[0]['workflow_instance'], None)
        self.assertEqual(self.client.calls[0]['workflow_parameters'], None)

    @skip("Test break")
    def test_ingest_no_manual(self):
        mp = mediapackage.Mediapackage(identifier='1', uri='/tmp')
        mp.add(self.path_capture_agent_properties, mediapackage.TYPE_ATTACHMENT, identifier='org.opencastproject.capture.agent.properties')
        mp.manual = False

        self.worker._ingest(mp)
        self.assertEqual(self.client.calls[0]['workflow'], 'full')
        self.assertEqual(self.client.calls[0]['workflow_instance'], '1')
        self.assertEqual(self.client.calls[0]['workflow_parameters'], {'trimHold': 'false', 'captionHold': 'false'})

    @skip("Test break")
    def test_ingest_no_manual_only_workflow(self):
        mp = mediapackage.Mediapackage(identifier='1', uri='/tmp')
        mp.addAttachmentAsString('org.opencastproject.workflow.definition=mini-full',
                                 name='org.opencastproject.capture.agent.properties', identifier='org.opencastproject.capture.agent.properties')
        mp.manual = False

        self.worker._ingest(mp)
        self.assertEqual(self.client.calls[0]['workflow'], 'mini-full')
        self.assertEqual(self.client.calls[0]['workflow_instance'], '1')
        self.assertEqual(self.client.calls[0]['workflow_parameters'], {})

    @skip("Test break")
    def test_ingest_nightly(self):
        repo = Repository('/tmp/repo_night')
        dispatcher = Dispatcher()
        logger = Logger(None)
        w = worker.Worker(dispatcher, repo, logger, self.client)

        mp = mediapackage.Mediapackage()
        mp.setOpStatus(worker.INGEST_CODE, mediapackage.OP_NIGHTLY)
        repo.add(mp)

        dispatcher.emit('timer-nightly')
        time.sleep(1) # Need time to create zip
        self.assertEqual(len(self.client.calls), 1)
        self.assertEqual(mp.getOpStatus(worker.INGEST_CODE), mediapackage.OP_DONE)
        rmtree('/tmp/repo_night')

    @skip("Test break")
    def test_ingest_nightly_with_params(self):
        workflow_name = 'GC-fast_workflow'
        workflow_parameters = 'trimHold:true;'
        repo = Repository('/tmp/repo_night')
        dispatcher = Dispatcher()
        logger = Logger(None)
        w = worker.Worker(dispatcher, repo, logger, self.client)

        mp = mediapackage.Mediapackage()
        repo.add(mp)
        w.enqueue_nightly_job_by_name(worker.INGEST_CODE, mp, {'workflow': workflow_name, 'workflow_parameters' : workflow_parameters})

        dispatcher.emit('timer-nightly')
        time.sleep(1) # Need time to create zip
        self.assertEqual(len(self.client.calls), 1)
        self.assertEqual(self.client.calls[0]['workflow'], workflow_name)
        self.assertEqual(self.client.calls[0]['workflow_parameters'], workflow_parameters)
        self.assertEqual(mp.getOpStatus(worker.INGEST_CODE), mediapackage.OP_DONE)
        rmtree('/tmp/repo_night')


    def test_export_to_zip(self):
        w = worker.Worker(self.dispatcher, self.repo1, self.logger, self.client)

        filename = '/tmp/mp.zip'
        w.enqueue_job_by_name('exporttozip', self.mp, {'location': filename})
        time.sleep(0.25)
        self.assertTrue(os.path.exists(filename))

        # Check zip file
        the_zip_file = zipfile.ZipFile(filename)
        ret = the_zip_file.testzip()
        self.assertEqual(ret, None)

    @skip("need special configuration")
    def test_side_by_side(self):
        w = worker.Worker(self.dispatcher, self.repo1, self.logger, self.client)

        baseDir = get_resource('sbs')
        path_track1 = path.join(baseDir, 'SCREEN.mp4')
        path_track2 = path.join(baseDir, 'CAMERA.mp4')
        path_catalog = path.join(baseDir, 'episode.xml')
        path_attach = path.join(baseDir, 'attachment.txt')
        path_capture_agent_properties = path.join(baseDir, 'org.opencastproject.capture.agent.properties')
        path_other = path.join(baseDir, 'manifest.xml')

        track1 = mediapackage.Track(uri = path_track1, duration = 532, flavor = "presentation/source")
        track2 = mediapackage.Track(uri = path_track2, duration = 532, flavor = "presenter/source")
        catalog = mediapackage.Catalog(uri = path_catalog, flavor = "catalog/source")
        attach = mediapackage.Attachment(uri = path_attach, flavor = "attachment/source")
        other = mediapackage.Other(uri = path_other, flavor = "other/source")

        self.mp.add(path_track1, mediapackage.TYPE_TRACK, "presentation/source", "video/mpeg", 532)
        self.mp.add(path_track2, mediapackage.TYPE_TRACK, "presenter/source", "video/mpeg", 532)
        self.mp.add(path_catalog, mediapackage.TYPE_CATALOG, "catalog/source", "text/xml")
        self.mp.add(path_attach, mediapackage.TYPE_ATTACHMENT, "attachment/source", "text/xml")
        self.mp.add(path_other, mediapackage.TYPE_OTHER, "other/source", "text/xml")


        filename = '/tmp/sidebyside.mpeg'
        w.enqueue_job_by_name('sidebyside', self.mp, {'location': filename})
        time.sleep(2)
        self.assertTrue(os.path.exists(filename))
