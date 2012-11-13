# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/worker
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

from unittest import TestCase
import os
import tempfile
import time
from shutil import rmtree

from galicaster.core import worker
from galicaster.mediapackage import mediapackage
from galicaster.mediapackage.repository import Repository
from galicaster.core.dispatcher import Dispatcher


class TestFunctions(TestCase):

    baseDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'mediapackage')
    path_capture_agent_properties = os.path.join(baseDir, 'org.opencastproject.capture.agent.properties')

    class RepoMock(object):
        def update(self, mp):
            pass

    class MHHTTPClientMock(object):
        def __init__(self):
            self.calls = []

        def ingest(self, mp_file, workflow=None, workflow_instance=None, workflow_parameters=None):
            self.calls.append({'file': mp_file, 
                               'workflow': workflow, 
                               'workflow_instance': workflow_instance, 
                               'workflow_parameters': workflow_parameters})

    class DispatcherMock(object):
        def connect(self, *args):
            pass
        def emit(self, *args):
            pass


    def test_init_parameters(self):
        repo = self.RepoMock()
        client = self.MHHTTPClientMock()
        dispatcher = self.DispatcherMock()
        w = worker.Worker(dispatcher, repo, client)
        self.assertEqual(w.export_path, os.path.expanduser('~'))
        self.assertEqual(w.tmp_path, tempfile.gettempdir())

        #self.assertRaises(OSError, worker.Worker, repo, client, '/a/b/c', None)
        #self.assertRaises(OSError, worker.Worker, repo, client, None, '/a/b/c')

        w = worker.Worker(dispatcher, repo, client, '/tmp/galicaster_tdd/a/b/c', '/tmp/galicaster_tdd/1/2/3')
        self.assertEqual(w.export_path, '/tmp/galicaster_tdd/a/b/c')
        self.assertEqual(w.tmp_path, '/tmp/galicaster_tdd/1/2/3')

        for dir_path in ('/tmp/galicaster_tdd/a/b/c', '/tmp/galicaster_tdd/1/2/3'):
            self.assertTrue(os.path.isdir(dir_path))
            
        rmtree('/tmp/galicaster_tdd')


    def test_manual(self):
        repo = self.RepoMock()
        client = self.MHHTTPClientMock()
        dispatcher = self.DispatcherMock()
        w = worker.Worker(dispatcher, repo, client)

        mp = mediapackage.Mediapackage(uri='/tmp')
        mp.manual = True
        
        w._ingest(mp)
        self.assertEqual(client.calls[0]['workflow'], None)
        self.assertEqual(client.calls[0]['workflow_instance'], None)
        self.assertEqual(client.calls[0]['workflow_parameters'], None)


    def test_no_manual(self):
        repo = self.RepoMock()
        client = self.MHHTTPClientMock()
        dispatcher = self.DispatcherMock()
        w = worker.Worker(dispatcher, repo, client)

        mp = mediapackage.Mediapackage(uri='/tmp')
        mp.properties['workflow_id'] = "1"
        mp.add(self.path_capture_agent_properties, mediapackage.TYPE_ATTACHMENT, identifier='org.opencastproject.capture.agent.properties')
        mp.manual = False
        
        w._ingest(mp)
        self.assertEqual(client.calls[0]['workflow'], 'full')
        self.assertEqual(client.calls[0]['workflow_instance'], '1')
        self.assertEqual(client.calls[0]['workflow_parameters'], {'trimHold': 'false', 'captionHold': 'false'})


    def test_no_manual_only_workflow(self):
        repo = self.RepoMock()
        client = self.MHHTTPClientMock()
        dispatcher = self.DispatcherMock()
        w = worker.Worker(dispatcher, repo, client)

        mp = mediapackage.Mediapackage(uri='/tmp')
        mp.properties['workflow_id'] = "1"
        mp.addAttachmentAsString('org.opencastproject.workflow.definition=mini-full', 
                                 name='org.opencastproject.capture.agent.properties', identifier='org.opencastproject.capture.agent.properties')
        mp.manual = False
        
        w._ingest(mp)
        self.assertEqual(client.calls[0]['workflow'], 'mini-full')
        self.assertEqual(client.calls[0]['workflow_instance'], '1')
        self.assertEqual(client.calls[0]['workflow_parameters'], {})
        

    def test_exec_nightly(self):
        repo = Repository('/tmp/repo_night')
        client = self.MHHTTPClientMock()
        dispatcher = Dispatcher()
        w = worker.Worker(dispatcher, repo, client)

        mp = mediapackage.Mediapackage()
        mp.setOpStatus(worker.INGEST_CODE, mediapackage.OP_NIGHTLY)
        repo.add(mp)

        dispatcher.emit('galicaster-notify-nightly')
        time.sleep(1) # Need time to create zip

        self.assertEqual(len(client.calls), 1)
        self.assertEqual(mp.getOpStatus(worker.INGEST_CODE), mediapackage.OP_DONE)

        rmtree('/tmp/repo_night')
