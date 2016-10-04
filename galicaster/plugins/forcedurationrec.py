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
 - Create a timer only for manual recordings
 - Doc
"""
from gi.repository import GObject

from galicaster.core import context


dispatcher = context.get_dispatcher()
conf = context.get_conf()
logger = context.get_logger()
recorder = context.get_recorder()

timeout_id = None
max_duration = conf.get_int('forcedurationrec', 'duration', 240)


def init():
    dispatcher.connect('recorder-started', create_timer)
    dispatcher.connect('action-reload-profile', do_stop_timers)


def create_timer(sender=None, mp_id=None):
    global timeout_id
    do_stop_timers()
    logger.debug("Init a timer to stop a record in {} minutes".format(max_duration))
    timeout_id = GObject.timeout_add_seconds(60 * max_duration, stop_recording)


def stop_recording(sender=None):
    global timeout_id
    timeout_id = None
    logger.info("Forceduration plugin stops the recording".format(max_duration))
    recorder.stop()


def do_stop_timers(sender=None):
    global timeout_id
    if timeout_id:
        GObject.source_remove(timeout_id)
