# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/lowaudio
#
# Copyright (c) 2016, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

"""

"""

from galicaster.core import context
import threading

timer = False
dispatcher = None
logger = None
timeout = None
t = None

def init():
    global dispatcher, logger, timeout
    logger = context.get_logger()
    dispatcher = context.get_dispatcher()
    conf = context.get_conf()
    threshold = conf.get('lowaudio','lowaudio_threshold')
    timeout = conf.get_float('lowaudio','timeout')
    if not threshold or not timeout:
        raise Exception("Failed to load plugin lowaudio, no parameters set in configuration file")
    dispatcher.add_new_signal("low-audio")
    dispatcher.add_new_signal("low-audio-recovered")
    dispatcher.connect('low-audio', low_audio)
    dispatcher.connect('low-audio-recovered', low_audio_recovered)


def low_audio(element=None):
    global timer, t
    if not timer:
        t = threading.Timer(timeout, emit_error)
        t.start()
        logger.debug(("Timer set to {}").format(timeout))
        timer = True

def emit_error():
    global timer
    dispatcher.emit("recorder-error", "Low volume")
    timer = False

def low_audio_recovered(element=None):
    global timer
    t.cancel()
    timer = False
    logger.debug("Audio recovered, removed timer")
