# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/cleanstale
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
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
days = None
logger = None

def init():
    global days, logger

    conf = context.get_conf()
    dispatcher = context.get_dispatcher()

    logger = context.get_logger()

    days = None
    try:
        days = int(conf.get('cleanstale', 'maxarchivaldays'))
    except Exception as exc:
        raise Exception("Wrong parameter maxarchivaldays: {}".format(exc))

    if days:
        logger.info("Parameter 'maxarchivaldays' set to {} days".format(days))
        dispatcher.connect('timer-nightly', clear_job)

        oninit = conf.get('cleanstale', 'checkoninit')
        if oninit in ["True", "true"]:
            clear_job(None)
    else:
        raise Exception("Parameter maxarchivaldays not configured")



def clear_job(sender=None):
    global days
    logger.info("Executing clear job ... {} days".format(days))
    repo = context.get_repository()

    mps = repo.get_past_mediapackages(days)

    logger.info("Found {} MP that have more than {} days". format(len(mps), days))
    for mp in mps:
        logger.info("Removing MP {}".format(mp.getIdentifier()))
        repo.delete(mp)
