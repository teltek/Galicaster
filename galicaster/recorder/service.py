# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/service
#
# Copyright (c) 2014, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-o
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

"""
TODO:
 - Scheduled recordings
 - profile.execute (see recorderui configure_profile)
 - Add connect:
   * start-record
   * stop-record
   * start-before
 - Add doc
"""

from datetime import datetime
from galicaster.mediapackage import mediapackage
from galicaster.recorder import Recorder
from galicaster.utils.i18n import _
from galicaster.utils.gstreamer import WeakMethod


class Status(object):
    def __init__(self, name): self.name = name
    def __str__(self): return self.name
    def __repr__(self): return self.name

INIT_STATUS = Status('init')
PREVIEW_STATUS = Status('preview')
RECORDING_STATUS = Status('recording')
PAUSED_STATUS = Status('paused')
ERROR_STATUS = Status('error')


class RecorderService(object):
    def __init__(self, dispatcher, repo, worker, conf, logger, autorecover=False, recorderklass=Recorder):
        """
        Initialize the recorder service.

        :param dispacher service.
        :param repo service.
        :param worker service.
        :param conf service.
        :param logger service.
        :param recorderklass (only to test) 
        """        
        self.repo = repo
        self.dispatcher = dispatcher
        self.worker = worker
        self.logger = logger
        self.conf = conf
        self.overlap = conf.get_permission("overlap")
        self.mute = True
        
        self.__set_status(INIT_STATUS)

        self.current_mediapackage = None
        self.error_msg = None
        self.recorder = None
        self.__recorderklass = recorderklass
        self.__create_drawing_areas_func = None
        self.__handle_recover_id = None
        self.autorecover = autorecover

        self.logger.debug("Autorecover mode: {}".format(self.autorecover))
        
        self.dispatcher.connect("init", WeakMethod(self, '_handle_init'))
        self.dispatcher.connect("action-reload-profile", WeakMethod(self, '_handle_reload_profile'))
        self.dispatcher.connect("recorder-error", WeakMethod(self, '_handle_error'))
        


    def set_create_drawing_areas_func(self, func):
        self.__create_drawing_areas_func = func


    def preview(self):
        if self.status not in (INIT_STATUS, ERROR_STATUS):
            return False
        
        try:
            self.logger.info("Starting recording service in the preview status")
            self.__prepare()
            self.recorder.preview()
            self.__set_status(PREVIEW_STATUS)
            return True

        except Exception as exc:
            self.dispatcher.emit("recorder-error", str(exc))

        return False


    def __prepare(self):
        current_profile = self.conf.get_current_profile()
        self.logger.debug("Using {} profile".format(current_profile.name))
        bins = current_profile.tracks
        for objectbin in bins:
            objectbin['path'] = self.repo.get_rectemp_path()

        
        self.recorder = self.__recorderklass(bins)
        self.dispatcher.emit("recorder-ready")

        self.mute_preview(self.mute)
        if self.__create_drawing_areas_func:
            info = self.recorder.get_display_areas_info()
            areas = self.__create_drawing_areas_func(info)
            self.recorder.set_drawing_areas(areas)
            

    def record(self, mp=None):
        self.dispatcher.emit("recorder-starting")

        self.logger.info("Recording (current status: {})".format(self.status))
        if self.status in (INIT_STATUS, ERROR_STATUS):
            self.logger.warning("Cancel recording: status error (in {})".format(self.status))
            return False
        if self.status != PREVIEW_STATUS and not self.overlap:
            self.logger.info("Cancel recording: it is already recording and not allow overlap")
            return False

        if self.status == PAUSED_STATUS:
            self.resume()

        if self.status == RECORDING_STATUS:
            self.recorder.stop()
            self.__close_mp()
            try:
                self.__prepare()
                self.recorder.preview_and_record()
            except Exception as exc:
                self.dispatcher.emit("recorder-error", str(exc))
                return False
        else:
            self.recorder and self.recorder.record()
            
        if not self.current_mediapackage:
            self.current_mediapackage = mp or self.create_mp()
            
        self.current_mediapackage.status = mediapackage.RECORDING
        now = datetime.utcnow().replace(microsecond=0)
        self.current_mediapackage.setDate(now)
        self.__set_status(RECORDING_STATUS)
        self.dispatcher.emit("recorder-started", self.current_mediapackage.getIdentifier())

        # Save current tmp data
        self.repo.save_current_mp_data(self.current_mediapackage, self.recorder.get_bins_info())

        return True


    def stop(self, force=False):
        self.logger.info("Stopping the capture")
        if self.status == PAUSED_STATUS:
            self.resume()
        if self.status != RECORDING_STATUS:
            self.logger.warning("Cancel stop: status error (is {})".format(self.status))
            return False

        self.recorder.stop(force)
        self.__close_mp()
        self.__set_status(INIT_STATUS)
        self.preview()
        return True


    def __close_mp(self):
        close_duration = self.recorder.get_recorded_time() / 1000000
        self.current_mediapackage.status = mediapackage.RECORDED
        self.logger.info("Adding new mediapackage ({}) to the repository".format(
                self.current_mediapackage.getIdentifier()))
        self.repo.add_after_rec(self.current_mediapackage, self.recorder.get_bins_info(),
                                close_duration, self.current_mediapackage.manual)

        # FIXME
        mp_mod_Uri = self.current_mediapackage.getURI()
        self.dispatcher.emit("recorder-stopped", mp_mod_Uri)
        
        code = 'manual' if self.current_mediapackage.manual else 'scheduled'
        if self.conf.get_lower('ingest', code) == 'immediately':
            self.worker.ingest(self.current_mediapackage)
        elif self.conf.get_lower('ingest', code) == 'nightly':
            self.worker.ingest_nightly(self.current_mediapackage)
        self.current_mediapackage = None


    def pause(self):
        self.logger.info("Pausing recorder")

        if self.status == RECORDING_STATUS:
            # Recorder mode (pausetype: pipeline (default value) or recording)
            if self.conf.get_choice('recorder', 'pausetype', ['pipeline', 'recording'] , 'pipeline') == 'pipeline':
                self.recorder.pause()
            else:
                self.recorder.pause_recording()
        
            self.__set_status(PAUSED_STATUS)
            return True
        self.logger.warning("Cancel pause: status error (in {})".format(self.status))
        return False


    def resume(self):
        self.logger.info("Resuming recorder")
        if self.status == PAUSED_STATUS:
            # Recorder mode (pausetype: pipeline (default value) or recording)
            if self.conf.get_choice('recorder', 'pausetype', ['pipeline', 'recording'] , 'pipeline') == 'pipeline':
                self.recorder.resume()
            else:
                self.recorder.resume_recording()
            
            self.__set_status(RECORDING_STATUS)
            return True
        self.logger.warning("Cancel resume: status error (in {})".format(self.status))
        return False


    def mute_preview(self, value):
        """Proxy function to mute preview"""
        self.mute = value
        self.recorder and self.recorder.mute_preview(value)


    def is_pausable(self):
        """Proxy function to know if actual recorder is pausable"""
        return self.recorder.is_pausable() if self.recorder else False


    def is_recording(self):
        """Helper function to check if status is RECORDING_STATUS or PAUSED_STATUS"""
        return self.status == RECORDING_STATUS or self.status == PAUSED_STATUS


    def is_error(self):
        """Helper function to check if status is ERROR_STATUS"""
        return self.status == ERROR_STATUS


    def get_recorded_time(self):
        """Proxy function to get the recorder time"""
        return self.recorder.get_recorded_time() if self.recorder else 0


    def _handle_error(self, origin, error_msg):
        self.logger.error("Handle error ({})". format(error_msg))
        # self.current_mediapackage = None
        if self.recorder:
            self.recorder.stop(True)
        self.error_msg = error_msg
        self.__set_status(ERROR_STATUS)

        if self.autorecover and not self.__handle_recover_id:
            self.repo.save_crash_recordings()
            self.logger.debug("Connecting recover recorder callback")
            self.__handle_recover_id = self.dispatcher.connect("timer-long", 
                                                             WeakMethod(self, '_handle_recover'))


    def _handle_recover(self, origin):
        self.logger.info("Handle recover from error")
        if self.__handle_recover_id and self.preview(): 
            self.error_msg = None
            self.logger.debug("Disconnecting recover recorder callback")
            self.__handle_recover_id = self.dispatcher.disconnect(self.__handle_recover_id)        


    def _handle_init(self, origin):
        self.logger.debug("Init recorder service")
        self.preview()


    def _handle_reload_profile(self, origin):
        if self.status in (PREVIEW_STATUS, ERROR_STATUS):
            self.logger.debug("Resetting recorder after reloading the profile")
            if self.recorder:
                self.recorder.stop(True)
            self.__set_status(INIT_STATUS)
            self.preview()

    def create_mp(self):
        self.current_mediapackage = self.__new_mediapackage()
        return self.current_mediapackage

    def __new_mediapackage(self):
        now = datetime.now().replace(microsecond=0)
        title = _("Recording started at {0}").format(now.isoformat())
        mp = mediapackage.Mediapackage(title=title)
        mp.properties['origin'] = self.conf.get_hostname()
        return mp


    def __set_status(self, status):
        self.status = status
        self.dispatcher.emit('recorder-status', status)


    def __del__(self):
        self.recorder and self.recorder.stop(True)
