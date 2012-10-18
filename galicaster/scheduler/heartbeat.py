# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/scheduler/nightly
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import logging

from datetime import datetime, timedelta
import threading
from threading import Timer
from threading import _Timer

logger = logging.getLogger()

class Heartbeat(object):
    
    def __init__(self, dispatcher, interval_short=10, interval_long=60, nighty_time='00:00'):
        # Raise ValueErrors
        aux = datetime.strptime(nighty_time, '%H:%M')
        self.nighty_hour    = aux.hour
        self.nighty_minute  = aux.minute
        self.interval_short = interval_short
        self.interval_long  = interval_long
        self.dispatcher     = dispatcher 

        self.dispatcher.connect('galicaster-notify-quit', self.do_stop_timers)


    def init_timer(self):
        Timer(self.get_seg_until_next(), self.__notify_timer_daily).start()
        self.__notify_timer_short()
        self.__notify_timer_long()


    def get_seg_until_next(self):
        now = datetime.now()
        tomorrow = (datetime(now.year, now.month, now.day, 
          self.nighty_hour, self.nighty_minute, 0, 0) 
          + timedelta(days=1))
        diff = tomorrow - now
        return diff.seconds + 1


    def do_stop_timers(self, sender=None):
        # NOTE: Stop all _Timers.
        for t in threading.enumerate():
            if isinstance(t, _Timer):
                t.cancel()


    def __notify_timer_daily(self):
        seg = self.get_seg_until_next()
        self.dispatcher.emit('galicaster-notify-nightly')
        logger.debug('galicaster-notify-nightly in %s', seg)
        Timer(seg, self.__notify_timer_daily).start()


    def __notify_timer_short(self):
        self.dispatcher.emit('galicaster-notify-timer-short')
        logger.debug('galicaster-notify-short in %s', self.interval_short)
        Timer(self.interval_short, self.__notify_timer_short).start()


    def __notify_timer_long(self):
        self.dispatcher.emit('galicaster-notify-timer-long')
        logger.debug('galicaster-notify-long in %s', self.interval_long)
        Timer(self.interval_long, self.__notify_timer_long).start()

