# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/service
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-o
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

from datetime import datetime
import gst
from galicaster.mediapackage import mediapackage
from galicaster.recorder import Recorder
from galicaster.utils.i18n import _

class State(object):
    def __init__(self, name): self.name = name
    def __str__(self): return self.name

INIT_STATE = State('init')
PREVIEW_STATE = State('preview')
RECORDING_STATE = State('recording')
PAUSED_STATE = State('paused')
ERROR_STATE = State('error')

class RecorderService(object):
    def __init__(self, dispatcher, repo, worker, conf, logger, recorderklass=Recorder):
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
        
        self.state = INIT_STATE

        self.current_mediapackage = None
        self.recorder = None
        self.__recorderklass = recorderklass
        self.__create_drawing_areas_func = None


    def set_create_drawing_areas_func(self, func):
        self.__create_drawing_areas_func = func


    def preview(self):
        current_profile = self.conf.get_current_profile()
        bins = current_profile.tracks
        for objectbin in bins:
            objectbin['path'] = self.repo.get_rectemp_path()

        self.recorder = self.__recorderklass(bins)
        if self.__create_drawing_areas_func:
            info = self.recorder.get_display_areas_info()
            #TODO
            #if self.swap:
            #    info.reverse()
            areas = self.__create_drawing_areas_func(info)
            self.recorder.set_drawing_areas(areas)
        self.recorder.preview()
        self.state = PREVIEW_STATE


    def record(self):
        #TODO if is recording
        self.recorder and self.recorder.record()
        self.current_mediapackage = self.__new_mediapackage(to_record=True)
        self.state = RECORDING_STATE


    def stop(self, force=False):
        if self.state == PAUSED_STATE:
            self.resume()

        self.recorder and self.recorder.stop(force)

        if self.state == RECORDING_STATE:
            close_duration = self.recorder.get_recorded_time() / gst.MSECOND
            self.current_mediapackage.status = mediapackage.RECORDED
            self.repo.add_after_rec(self.current_mediapackage, self.recorder.get_bins_info(),
                                    close_duration, self.current_mediapackage.manual)

            code = 'manual' if self.current_mediapackage.manual else 'scheduled'
            if self.conf.get_lower('ingest', code) == 'immediately':
                self.worker.ingest(self.current_mediapackage)
            elif self.conf.get_lower('ingest', code) == 'nightly':
                self.worker.ingest_nightly(self.current_mediapackage)

            self.state = PREVIEW_STATE
            return True
        return False


    def pause(self):
        if self.state == RECORDING_STATE:
            self.recorder.pause()
            self.state = PAUSED_STATE
            return True
        return False


    def resume(self):
        if self.state == PAUSED_STATE:
            self.recorder.resume()
            self.state = RECORDING_STATE
            return True
        return False


    def mute_preview(self, value):
        self.recorder and self.recorder.mute_preview(value)


    def get_recorded_time(self):
        return self.recorder.mute_preview(value) if self.recorder else 0


    def __new_mediapackage(self, to_record=False):
        now = datetime.now().replace(microsecond=0)
        title = _("Recording started at {0}").format(now.isoformat())
        mp = mediapackage.Mediapackage(title=title)
        mp.properties['origin'] = self.conf.hostname
        if to_record:
            mp.status=mediapackage.RECORDING
            now = datetime.utcnow().replace(microsecond=0)
            mp.setDate(now)
        return mp
