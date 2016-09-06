# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/scheduler/scheduler
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

import datetime
from gi.repository import GObject

from galicaster.mediapackage import mediapackage

"""
This class manages the timers and its respective signals in order to start and stop scheduled recordings.
"""

class Scheduler(object):

    def __init__(self, repo, conf, disp, logger, recorder):
        """Initializes the scheduler of future recordings.
        The instance of this class is in charge of set all the necessary timers in order to manage scheduled recordings.
        It also manages the update of mediapackages with scheduled recordings and capture agent status.
        Args:
            repo (Repository): the galicaster mediapackage repository. See mediapackage/repository.py.
            conf (Conf): galicaster users and default configuration. See galicaster/core/conf.py.
            disp (Dispatcher): the galicaster event-dispatcher to emit signals. See core/dispatcher.py.
            logger (Logger): the object that prints all the information, warning and error messages. See core/logger.py
            recorder (Recorder)
        Attributes:
            conf (Conf): galicaster users and default configuration given as an argument.
            repo (Repository): the galicaster mediapackage repository given as an argument.
            dispatcher (Dispatcher): the galicaster event-dispatcher to emit signals given by the argument disp.
            logger (Logger): the object that prints all the information, warning and error messages.
            recorder (Recorder)
            start_timers (Dict{str,GObject timeout id}): set of timers with the time remaining for all the scheduled recordings that are going to start in less than 30 minutes.
            mp_rec (str): identifier of the mediapackage that is going to be recorded at the scheduled time.
            last_events (List[Events]): list of calendar Events.
        """

        self.conf       = conf
        self.repo       = repo
        self.dispatcher = disp
        self.logger     = logger
        self.recorder   = recorder

        self.start_timers = dict()
        self.mp_rec = None

        self.dispatcher.connect("timer-long", self._check_next_recording)


    def _check_next_recording(self, origin):
        next_mp = self.repo.get_next_mediapackage()
        if next_mp and not self.start_timers.has_key(next_mp.getIdentifier()):
            self.create_timer(next_mp)


    def create_timer(self, mp):
        """Creates a timer for a future mediapackage recording if there are less than 30 minutes to the scheduled event.
        Args:
            mp (Mediapackage): the mediapackage whose timer is going to be created.
        """
        diff = (mp.getDate() - datetime.datetime.utcnow())
        if diff < datetime.timedelta(minutes=30) and mp.getIdentifier() != self.mp_rec and not self.start_timers.has_key(mp.getIdentifier()):
            self.logger.info('Create timer for MP {}, it starts at {}'.format(mp.getIdentifier(), mp.getStartDateAsString()))
            self.dispatcher.emit('recorder-scheduled-event', mp.getIdentifier())

            timeout_id = GObject.timeout_add_seconds(diff.seconds, self.__start_record, mp.getIdentifier())
            self.start_timers[mp.getIdentifier()] = timeout_id


    def remove_timer(self, mp):
        if mp and self.start_timers.has_key(mp.getIdentifier()):
            GObject.source_remove(self.start_timers[mp.getIdentifier()])
            del self.start_timers[mp.getIdentifier()]


    def update_timer(self, mp):
        if self.start_timers.has_key(mp.getIdentifier()) and mp.status == mediapackage.SCHEDULED:
            GObject.source_remove(self.start_timers[mp.getIdentifier()])
            del self.start_timers[mp.getIdentifier()]
            self.create_timer(mp)


    def __start_record(self, key):
        """Sets the timer for the duration of the scheduled recording that is about to start.
        If any connectivity errors occur, logger prints it properly.
        Args:
            key (str): the new mediapackage identifier.
        """
        mp = self.repo.get(key) # FIXME what if the mp doesnt exist?
        if mp.status == mediapackage.SCHEDULED:

            self.mp_rec = key
            mp = self.repo.get(key)

            self.logger.info('Timeout to start record %s, duration %s ms', mp.getIdentifier(), mp.getDuration())

            GObject.timeout_add_seconds(mp.getDuration()/1000, self.__stop_record, mp.getIdentifier())
            self.recorder.record(mp)

        del self.start_timers[mp.getIdentifier()]


    def __stop_record(self, key):
        """Sets the status of the capture agent when has just finished a scheduled recording.
        If any connectivity errors occur, logger prints it properly.
        Args:
            key (str): the mediapackage identifier.
        """
        self.mp_rec = None
        self.logger.info('Timeout to stop record %s', key)

        mp = self.repo.get(key)
        if mp.status == mediapackage.RECORDING:
            self.recorder.stop()
