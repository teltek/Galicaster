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


def init():
    global days, logger

    conf = context.get_conf()
    dispatcher = context.get_dispatcher()
    dispatcher.connect('galicaster-notify-nightly', clear_job)

    logger = context.get_logger()

    days = None
    try:
        days = int(conf.get('cleanstale', 'maxarchivaldays'))
        if days:
            logger.info("Parameter 'maxarchivaldays' set to {} days".format(days))

        oninit = conf.get('cleanstale', 'checkoninit')
        if oninit in ["True", "true"]:
            clear_job(None)

    except Exception as exc:
        logger.error("Could not read the config parameters: {}".format(exc))



def clear_job(sender=None):
    logger.info("Executing clear job ...")
    conf = context.get_conf()
    repo = context.get_repository()

    mps = repo.get_past_mediapackages(days)

    logger.info("Found {} MP that have more than {} days". format(len(mps), days))
    for mp in mps:
        logger.info("Removing MP {}".format(mp.getIdentifier()))
        repo.delete(mp)
    

