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
    conf = context.get_conf()
    dispatcher = context.get_dispatcher()
    dispatcher.connect('galicaster-notify-nightly', clear_job)

    try:
        days = int(conf.get('cleanstale', 'maxarchivaldays'))
    except ValueError:
        #log or set default value
        pass


def clear_job(sender=None):
    conf = context.get_conf()
    repo = context.get_repository()

    try:
        days = int(conf.get('cleanstale', 'maxarchivaldays'))
    except ValueError:
        #log
        return

    mps = repo.get_past_mediapackages(days)
    for mp in mps:
        #log
        repo.delete(mp)
    

