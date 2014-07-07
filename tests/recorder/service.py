# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/recorder/service
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


"""
Unit tests for `galicaster.recorder.service` module.
"""

from unittest import TestCase
import os
import gtk
import tempfile
import time
from tempfile import mkdtemp
from shutil import rmtree
from datetime import datetime
import gst

from galicaster.core.conf import Conf
from galicaster.core.dispatcher import Dispatcher
from galicaster.core.logger import Logger
from galicaster.mediapackage.repository import Repository
from galicaster.recorder.service import RecorderService
from galicaster.recorder.service import INIT_STATE
from galicaster.recorder.service import PREVIEW_STATE
from galicaster.recorder.service import RECORDING_STATE
from galicaster.recorder.service import PAUSED_STATE
from galicaster.recorder.service import ERROR_STATE
from galicaster.recorder.recorder import Recorder
from galicaster.core import context

from tests import get_resource

gtk.gdk.threads_init()

class TestFunctions(TestCase):

    class WorkerMock(object):
        def ingest(self, mp):
            pass
        def ingest_nightly(self, mp):
            pass


    class RecorderMock(object):
        def __init__(self, bins, players={}):
            self.bins = bins
            self.player = players
            self.dispatcher = context.get_dispatcher()
            self.time = None
        def get_status(self):
            pass
        def get_time(self):
            pass
        def get_recorded_time(self):
            return gst.SECOND
        def preview(self):
            pass
        def preview_and_record(self):
            pass
        def record(self):
            self.time = datetime.now()
        def pause(self):
            pass
        def resume(self):
            pass
        def stop(self, force=False):
            self.time = datetime.now()
            if not force and os.path.isdir(self.bins[0]['path']):
                for bin in self.bins:
                    filename = os.path.join(bin['path'], bin['file'])
                    os.symlink(get_resource('sbs/CAMERA.mp4'), filename)
        def is_pausable(self):
            return True
        def mute_preview(self, value):
            pass
        def set_drawing_areas(self, players):
            self.player = players
        def get_display_areas_info(self):
            return ['sink-1', 'sink-2']
        def get_bins_info(self):
            for bin in self.bins:
                bin['mimetype'] = 'video/avi'
            return self.bins 


    class RecorderErrorMock(RecorderMock):
        def preview(self):
            self.dispatcher.emit("recorder-error", "error test")
            

    def setUp(self):
        self.recorderklass = self.RecorderMock
        #self.recorderklass = Recorder
        self.tmppath = mkdtemp()
        # To reset dispatcher in each tests.
        context.set('dispatcher', None)
        context.delete('dispatcher')


    def tearDown(self):
        rmtree(self.tmppath)


    def test_init(self):
        dispatcher = context.get_dispatcher()
        repo = Repository(self.tmppath)
        worker = self.WorkerMock()
        conf = Conf()
        logger = Logger(None)
        
        recorder_service = RecorderService(dispatcher, repo, worker, conf, logger, self.recorderklass)
        self.assertEqual(recorder_service.state, INIT_STATE)
        self.assertEqual(recorder_service.get_recorded_time(), 0)
        

    def test_preview(self):
        dispatcher = context.get_dispatcher()
        repo = Repository(self.tmppath)
        worker = self.WorkerMock()
        conf = Conf()
        logger = Logger(None)
        
        recorder_service = RecorderService(dispatcher, repo, worker, conf, logger, self.recorderklass)
        self.assertEqual(recorder_service.state, INIT_STATE)
        recorder_service.preview()
        self.assertEqual(recorder_service.state, PREVIEW_STATE)
        self.assertEqual(recorder_service.preview(), False)
        self.assertEqual(recorder_service.stop(), False)
        self.assertEqual(recorder_service.pause(), False)
        self.assertEqual(recorder_service.resume(), False)
        self.sleep()
        recorder_service.stop()
        self.assertEqual(recorder_service.state, PREVIEW_STATE)
        self.assertEqual(len(repo), 0)


    def test_recording(self):
        dispatcher = context.get_dispatcher()
        repo = Repository(self.tmppath)
        worker = self.WorkerMock()
        conf = Conf()
        logger = Logger(None)
        
        recorder_service = RecorderService(dispatcher, repo, worker, conf, logger, self.recorderklass)
        self.assertEqual(recorder_service.state, INIT_STATE)
        recorder_service.preview()
        self.assertEqual(recorder_service.state, PREVIEW_STATE)
        self.sleep()
        recorder_service.record()
        self.assertEqual(recorder_service.state, RECORDING_STATE)
        self.sleep()
        recorder_service.stop()
        self.assertEqual(recorder_service.state, PREVIEW_STATE)
        self.assertEqual(len(repo), 1)


    def test_stop_recoding_on_pause(self):
        dispatcher = context.get_dispatcher()
        repo = Repository(self.tmppath)
        worker = self.WorkerMock()
        conf = Conf()
        logger = Logger(None)
        
        recorder_service = RecorderService(dispatcher, repo, worker, conf, logger, self.recorderklass)
        self.assertEqual(recorder_service.state, INIT_STATE)
        recorder_service.preview()
        self.assertEqual(recorder_service.state, PREVIEW_STATE)
        self.sleep()
        recorder_service.record()
        self.assertEqual(recorder_service.state, RECORDING_STATE)
        self.sleep()
        recorder_service.pause()
        self.assertEqual(recorder_service.state, PAUSED_STATE)
        self.sleep()
        recorder_service.stop()
        self.assertEqual(recorder_service.state, PREVIEW_STATE)
        self.assertEqual(len(repo), 1)


    def test_error(self):
        dispatcher = context.get_dispatcher()
        repo = Repository(self.tmppath)
        worker = self.WorkerMock()
        conf = Conf()
        logger = Logger(None)

        recorder_service = RecorderService(dispatcher, repo, worker, conf, logger, self.RecorderErrorMock)
        self.assertEqual(recorder_service.state, INIT_STATE)
        recorder_service.preview()
        self.sleep()
        self.assertEqual(recorder_service.state, ERROR_STATE)


    def test_external_error(self):
        dispatcher = context.get_dispatcher()
        repo = Repository(self.tmppath)
        worker = self.WorkerMock()
        conf = Conf()
        logger = Logger(None)
        
        recorder_service = RecorderService(dispatcher, repo, worker, conf, logger, self.recorderklass)
        self.assertEqual(recorder_service.state, INIT_STATE)
        recorder_service.preview()
        dispatcher.emit("recorder-error", None)
        self.assertEqual(recorder_service.state, ERROR_STATE)
        

    def test_handle_reload_profile(self):
        dispatcher = context.get_dispatcher()
        repo = Repository(self.tmppath)
        worker = self.WorkerMock()
        conf = Conf()
        logger = Logger(None)
        
        recorder_service = RecorderService(dispatcher, repo, worker, conf, logger, self.recorderklass)
        self.assertEqual(recorder_service.state, INIT_STATE)
        recorder_service.preview()
        old_id = id(recorder_service.recorder)
        dispatcher.emit("reload-profile")
        new_id = id(recorder_service.recorder)
        self.assertEqual(recorder_service.state, PREVIEW_STATE)
        self.assertNotEqual(old_id, new_id)
        self.sleep()
        recorder_service.record()
        old_id = id(recorder_service.recorder)
        self.assertEqual(recorder_service.state, RECORDING_STATE)
        dispatcher.emit("reload-profile")
        new_id = id(recorder_service.recorder)
        self.assertEqual(old_id, new_id)
        self.assertEqual(recorder_service.state, RECORDING_STATE)


    def sleep(self):
        if self.recorderklass == Recorder:
            time.sleep(1.1)
