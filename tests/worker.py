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
from os import path

from galicaster.core.worker import Worker
from galicaster.mediapackage import mediapackage


class TestFunctions(TestCase):

    baseDir = path.join(path.dirname(path.abspath(__file__)), 'resources', 'mediapackage')
    path_capture_agent_properties = path.join(baseDir, 'org.opencastproject.capture.agent.properties')

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


    def test_manual(self):
        repo = self.RepoMock()
        client = self.MHHTTPClientMock()
        worker = Worker(repo, client)

        mp = mediapackage.Mediapackage(uri='/tmp')
        mp.manual = True
        
        worker._ingest(mp)
        self.assertEqual(client.calls[0]['workflow'], None)
        self.assertEqual(client.calls[0]['workflow_instance'], None)
        self.assertEqual(client.calls[0]['workflow_parameters'], None)


    def test_no_manual(self):
        repo = self.RepoMock()
        client = self.MHHTTPClientMock()
        worker = Worker(repo, client)

        mp = mediapackage.Mediapackage(identifier='1', uri='/tmp')
        mp.add(self.path_capture_agent_properties, mediapackage.TYPE_ATTACHMENT, identifier='org.opencastproject.capture.agent.properties')
        mp.manual = False
        
        worker._ingest(mp)
        self.assertEqual(client.calls[0]['workflow'], 'full')
        self.assertEqual(client.calls[0]['workflow_instance'], '1')
        self.assertEqual(client.calls[0]['workflow_parameters'], {'trimHold': 'false', 'captionHold': 'false'})


    def test_no_manual_only_workflow(self):
        repo = self.RepoMock()
        client = self.MHHTTPClientMock()
        worker = Worker(repo, client)

        mp = mediapackage.Mediapackage(identifier='1', uri='/tmp')
        mp.addAttachmentAsString('org.opencastproject.workflow.definition=mini-full', 
                                 name='org.opencastproject.capture.agent.properties', identifier='org.opencastproject.capture.agent.properties')
        mp.manual = False
        
        worker._ingest(mp)
        self.assertEqual(client.calls[0]['workflow'], 'mini-full')
        self.assertEqual(client.calls[0]['workflow_instance'], '1')
        self.assertEqual(client.calls[0]['workflow_parameters'], {})
        


        
        

