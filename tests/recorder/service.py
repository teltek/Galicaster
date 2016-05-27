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
from gi.repository import Gtk
import tempfile
import time
from tempfile import mkdtemp
from shutil import rmtree
from datetime import datetime
from gi.repository import Gst

from galicaster.core.conf import Conf
from galicaster.core.dispatcher import Dispatcher
from galicaster.core.logger import Logger
from galicaster.mediapackage import mediapackage
from galicaster.mediapackage.repository import Repository
from galicaster.recorder.service import RecorderService
from galicaster.recorder.service import INIT_STATUS
from galicaster.recorder.service import PREVIEW_STATUS
from galicaster.recorder.service import RECORDING_STATUS
from galicaster.recorder.service import PAUSED_STATUS
from galicaster.recorder.service import ERROR_STATUS
from galicaster.recorder.recorder import Recorder
from galicaster.core import context

from tests import get_resource

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
            return Gst.SECOND
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
        dispatcher, repo, worker, conf, logger = self.__get_dependencies()
        
        recorder_service = RecorderService(dispatcher, repo, worker, conf, logger, self.recorderklass)
        self.assertEqual(recorder_service.status, INIT_STATUS)
        self.assertEqual(recorder_service.get_recorded_time(), 0)
        

    def test_preview(self):
        dispatcher, repo, worker, conf, logger = self.__get_dependencies()
        
        recorder_service = RecorderService(dispatcher, repo, worker, conf, logger, self.recorderklass)
        self.assertEqual(recorder_service.status, INIT_STATUS)
        recorder_service.preview()
        self.assertEqual(recorder_service.status, PREVIEW_STATUS)
        self.assertEqual(recorder_service.preview(), False)
        self.assertEqual(recorder_service.stop(), False)
        self.assertEqual(recorder_service.pause(), False)
        self.assertEqual(recorder_service.resume(), False)
        self.__sleep()
        recorder_service.stop()
        self.assertEqual(recorder_service.status, PREVIEW_STATUS)
        self.assertEqual(len(repo), 0)


    def test_recording(self):
        dispatcher, repo, worker, conf, logger = self.__get_dependencies()
        
        recorder_service = RecorderService(dispatcher, repo, worker, conf, logger, self.recorderklass)
        self.assertEqual(recorder_service.status, INIT_STATUS)
        recorder_service.preview()
        self.assertEqual(recorder_service.status, PREVIEW_STATUS)
        self.assertEqual(recorder_service.current_mediapackage, None)
        self.__sleep()
        recorder_service.record()
        self.assertEqual(recorder_service.status, RECORDING_STATUS)
        self.assertNotEqual(recorder_service.current_mediapackage, None)
        self.__sleep()
        recorder_service.stop()
        self.assertEqual(recorder_service.current_mediapackage, None)
        self.assertEqual(recorder_service.status, PREVIEW_STATUS)
        self.assertEqual(len(repo), 1)


    def test_stop_recoding_on_pause(self):
        dispatcher, repo, worker, conf, logger = self.__get_dependencies()
        
        recorder_service = RecorderService(dispatcher, repo, worker, conf, logger, self.recorderklass)
        self.assertEqual(recorder_service.status, INIT_STATUS)
        recorder_service.preview()
        self.assertEqual(recorder_service.is_recording(), False)
        self.assertEqual(recorder_service.status, PREVIEW_STATUS)
        self.__sleep()
        recorder_service.record()
        self.assertEqual(recorder_service.is_recording(), True)
        self.assertEqual(recorder_service.status, RECORDING_STATUS)
        self.__sleep()
        recorder_service.pause()
        self.assertEqual(recorder_service.is_recording(), True)
        self.assertEqual(recorder_service.status, PAUSED_STATUS)
        self.__sleep()
        recorder_service.stop()
        self.assertEqual(recorder_service.is_recording(), False)
        self.assertEqual(recorder_service.status, PREVIEW_STATUS)
        self.assertEqual(len(repo), 1)


    def test_error_and_recover(self):
        dispatcher, repo, worker, conf, logger = self.__get_dependencies()
        
        recorder_service = RecorderService(dispatcher, repo, worker, conf, logger, self.recorderklass)
        self.assertEqual(recorder_service.status, INIT_STATUS)
        recorder_service.preview()
        self.__sleep()
        recorder_service.record()
        self.assertEqual(recorder_service.error_msg, None)
        self.assertNotEqual(recorder_service.current_mediapackage, None)
        dispatcher.emit("recorder-error", "Test Error")
        self.assertEqual(recorder_service.status, ERROR_STATUS)
        self.assertEqual(recorder_service.is_error(), True)
        self.assertNotEqual(recorder_service.error_msg, None)
        dispatcher.emit("timer-long")
        self.assertEqual(recorder_service.status, PREVIEW_STATUS)
        self.assertEqual(recorder_service.error_msg, None)
        recorder_service.record()
        self.assertEqual(recorder_service.status, RECORDING_STATUS)
        self.assertNotEqual(recorder_service.current_mediapackage, None)
        dispatcher.emit("timer-long")
        self.assertEqual(recorder_service.status, RECORDING_STATUS)
        self.assertNotEqual(recorder_service.current_mediapackage, None)
        

    def test_handle_reload_profile(self):
        dispatcher, repo, worker, conf, logger = self.__get_dependencies()
        
        recorder_service = RecorderService(dispatcher, repo, worker, conf, logger, self.recorderklass)
        self.assertEqual(recorder_service.status, INIT_STATUS)
        recorder_service.preview()
        old_id = id(recorder_service.recorder)
        dispatcher.emit("action-reload-profile")
        new_id = id(recorder_service.recorder)
        self.assertEqual(recorder_service.status, PREVIEW_STATUS)
        self.assertNotEqual(old_id, new_id)
        self.__sleep()
        recorder_service.record()
        old_id = id(recorder_service.recorder)
        self.assertEqual(recorder_service.status, RECORDING_STATUS)
        dispatcher.emit("action-reload-profile")
        new_id = id(recorder_service.recorder)
        self.assertEqual(old_id, new_id)
        self.assertEqual(recorder_service.status, RECORDING_STATUS)


    def test_new_recording_when_recording(self):
        dispatcher, repo, worker, conf, logger = self.__get_dependencies()
        conf.set("allows", "overlap", "True")
        
        recorder_service = RecorderService(dispatcher, repo, worker, conf, logger, self.recorderklass)
        recorder_service.preview()
        self.__sleep()
        recorder_service.record()
        self.__sleep()
        recorder_service.record()
        self.assertEqual(recorder_service.status, RECORDING_STATUS)
        self.assertEqual(len(repo), 1)
        self.__sleep()
        self.assertEqual(recorder_service.status, RECORDING_STATUS)
        recorder_service.stop()
        self.assertEqual(len(repo), 2)


    def test_new_recording_when_recording_not_allow(self):
        dispatcher, repo, worker, conf, logger = self.__get_dependencies()
        
        recorder_service = RecorderService(dispatcher, repo, worker, conf, logger, self.recorderklass)
        recorder_service.preview()
        self.__sleep()
        recorder_service.record()
        self.__sleep()
        recorder_service.record()
        self.assertEqual(recorder_service.status, RECORDING_STATUS)
        self.assertEqual(len(repo), 0)
        self.__sleep()
        self.assertEqual(recorder_service.status, RECORDING_STATUS)
        recorder_service.stop()
        self.assertEqual(len(repo), 1)


    def test_new_recording_when_paused(self):
        dispatcher, repo, worker, conf, logger = self.__get_dependencies()
        conf.set("allows", "overlap", "True")
        
        recorder_service = RecorderService(dispatcher, repo, worker, conf, logger, self.recorderklass)
        recorder_service.preview()
        self.__sleep()
        recorder_service.record()
        self.__sleep()
        recorder_service.pause()
        self.__sleep()
        recorder_service.record()
        self.assertEqual(recorder_service.status, RECORDING_STATUS)
        self.assertEqual(len(repo), 1)
        self.__sleep()
        self.assertEqual(recorder_service.status, RECORDING_STATUS)
        recorder_service.stop()        
        self.assertEqual(len(repo), 2)


    def test_record_scheduled_mp(self):
        dispatcher, repo, worker, conf, logger = self.__get_dependencies()        
        recorder_service = RecorderService(dispatcher, repo, worker, conf, logger, self.recorderklass)

        self.assertEqual(len(repo), 0)
        recorder_service.preview()
        self.assertEqual(recorder_service.current_mediapackage, None)
        self.assertEqual(len(repo), 0)
        self.__sleep()
        recorder_service.record()
        self.assertNotEqual(recorder_service.current_mediapackage, None)
        self.assertEqual(recorder_service.current_mediapackage.status, mediapackage.RECORDING)
        self.assertEqual(len(repo), 0)
        self.__sleep()
        recorder_service.stop()
        self.assertEqual(recorder_service.current_mediapackage, None)
        self.assertEqual(len(repo), 1)

        mp = mediapackage.Mediapackage(title="test")
        repo.add(mp)

        self.assertEqual(len(repo), 2)
        recorder_service.preview()
        self.assertEqual(recorder_service.current_mediapackage, None)
        self.assertEqual(len(repo), 2)
        self.__sleep()
        recorder_service.record(mp)
        self.assertEqual(recorder_service.current_mediapackage, mp)
        self.assertEqual(recorder_service.current_mediapackage.status, mediapackage.RECORDING)
        self.assertEqual(repo[mp.identifier].status, mediapackage.RECORDING)
        self.assertEqual(len(repo), 2)
        self.__sleep()
        recorder_service.stop()
        self.assertEqual(recorder_service.current_mediapackage, None)
        self.assertEqual(len(repo), 2)

        for mp in repo.values():
            self.assertEqual(mp.status, mediapackage.RECORDED)
            



    def __sleep(self):
        if self.recorderklass == Recorder:
            time.sleep(1.1)


    def __get_dependencies(self):
        dispatcher = context.get_dispatcher()
        repo = Repository(self.tmppath)
        worker = self.WorkerMock()
        conf = Conf()
        conf.reload()
        conf.set("allows", "overlap", "False")
        logger = Logger(None)

        return dispatcher, repo, worker, conf, logger
