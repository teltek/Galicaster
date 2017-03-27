# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/checkspace
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

conf = None
logger = None
repo = None
dispatcher = None
minfreespace = None

def init():
    global conf, logger, repo, dispatcher, minfreespace, freespace
    conf = context.get_conf()
    dispatcher = context.get_dispatcher()
    logger = context.get_logger()
    repo = context.get_repository()

    minfreespace = conf.get_int('checkspace','minfreespace')
    if not minfreespace:
        raise Exception("Parameter minfreespace not configured")

    logger.info("Parameter 'minfreespace' set to {} GB".format(minfreespace))
    dispatcher.connect("recorder-ready", check_space)

def check_space(sender):
    freespace = repo.get_free_space() /(1024*1024*1024)
    if freespace < minfreespace:
        dispatcher.emit("recorder-error", "Low repository space: repo has {} GB free space available". format(freespace))
