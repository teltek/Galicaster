# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/context
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


import os

from galicaster.mediapackage.repository import Repository
from galicaster.utils.conf import Conf
from galicaster.utils.dispatcher import Dispatcher

__galicaster_conf = None
__galicaster_repository = None
__galicaster_dispatcher = None

def get_conf():
    """
    Get the Conf class from the App Context
    """
    global __galicaster_conf

    if not isinstance(__galicaster_conf, Conf):
        __galicaster_conf = Conf()

    return __galicaster_conf


def get_dispatcher():
    """
    Get the Dispatcher class from the App Context
    """
    global __galicaster_dispatcher

    if not isinstance(__galicaster_dispatcher, Dispatcher):
        __galicaster_dispatcher = Dispatcher()

    return __galicaster_dispatcher


def get_repository(use_dispatcher=True):
    """
    Get the Mediapackage Repository from the App Context
    """
    global __galicaster_repository
    if not isinstance(__galicaster_repository, Repository):
        try:
            repository_path = get_conf().get("basic", "repository")
            assert os.path.isdir(repository_path)
        except:
            repository_path = os.path.join(os.getenv('HOME'), "Repository")
            if not os.path.isdir(repository_path):
                os.mkdir(repository_path)

        if use_dispatcher:
            dispatcher = get_dispatcher()
        else:
            dispatcher = None
        __galicaster_repository = Repository(repository_path, dispatcher)

    return __galicaster_repository
