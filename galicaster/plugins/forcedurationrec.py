# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/forcedurationrec
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
TODO:
 - Timer only in manual recordings
 - Doc
"""
from threading import Timer
from threading import _Timer

from galicaster.core import context


dispatcher = context.get_dispatcher()
conf = context.get_conf()
logger = context.get_logger()
recorder = context.get_recorder()

t_stop = None
max_duration = conf.get_int('forcedurationrec', 'duration', 240)


def init():
    dispatcher.connect("galicaster-notify-quit", do_stop_timers)
    dispatcher.connect('recorder-started', create_timer)
    dispatcher.connect('reload-profile', do_stop_timers)


def create_timer(sender=None, mp_id=None):
    global t_stop
    do_stop_timers()
    t_stop = Timer(60 * max_duration, stop_recording) 
    logger.debug("Init Timer to stop a record in {} minutes".format(max_duration))
    t_stop.start()


def stop_recording(sender=None):
    global t_stop
    t_stop = None
    logger.info("Forceduration plugin stops the recording".format(max_duration))
    recorder.stop()


def do_stop_timers(sender=None):
    global t_stop
    if isinstance(t_stop, _Timer):
        logger.debug("Reset Timer")
        t_stop.cancel()

