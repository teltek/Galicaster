# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/core/context
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

from galicaster.mediapackage.repository import Repository
from galicaster.utils.mhhttpclient import MHHTTPClient
from galicaster.core.conf import Conf
from galicaster.core.logger import Logger
from galicaster.core.worker import Worker
from galicaster.core.dispatcher import Dispatcher
from galicaster.core.state import State
from galicaster.classui.mainwindow import GCWindow
from galicaster.scheduler.heartbeat import Heartbeat
from galicaster.scheduler.scheduler import Scheduler

__galicaster_context = {}


def get(service_name):
    """
    Get service by name from the App Context
    """
    return __galicaster_context[service_name]


def has(service_name):
    """
    Has service by name from the App Context
    """
    return service_name in __galicaster_context


def set(service_name, service):
    """
    Set service by name from the App Context
    """
    __galicaster_context[service_name] = service


def delete(service_name):
    """
    Delete service by name from the App Context
    """
    del __galicaster_context[service_name]
    

def get_conf():
    """
    Get the Conf class from the App Context
    """
    if 'conf' not in __galicaster_context:
        __galicaster_context['conf'] = Conf()

    return __galicaster_context['conf']


def get_logger():
    """
    Get the Logger class from the App Context
    """
    if 'logger' not in __galicaster_context:
        conf = get_conf()
        logger = Logger(conf.get('logger', 'path'),
                        conf.get('logger', 'level').upper(),
                        conf.get_boolean('logger', 'rotate'),
                        conf.get_boolean('logger', 'use_syslog'))
        __galicaster_context['logger'] = logger
        conf.logger = logger

    return __galicaster_context['logger']


def get_mhclient():
    """
    Get the Mhclient class from the App Context
    """
    if 'mhclient' not in __galicaster_context:
        conf = get_conf()
        multiple_ingest  = conf.get_boolean('ingest','multiple-ingest') or False
        connect_timeout = conf.get_int('ingest', 'connect_timeout') or 2
        timeout = conf.get_int('ingest', 'timeout') or 2
        if get_conf().get_boolean("ingest", "active"):
            mhclient = MHHTTPClient(conf.get('ingest', 'host'), 
                                    conf.get('ingest', 'username'), 
                                    conf.get('ingest', 'password'), 
                                    conf.hostname, 
                                    conf.get('ingest', 'address'),
                                    multiple_ingest, 
                                    connect_timeout,
                                    timeout,
                                    conf.get('ingest', 'workflow'),
                                    conf.get_dict('ingest', 'workflow-parameters'),
                                    conf.get_dict('ingest', 'ca-parameters'),
                                    get_repository(),
                                    get_logger())
        else:
            mhclient = None
        __galicaster_context['mhclient'] = mhclient

    return __galicaster_context['mhclient']


def get_dispatcher():
    """
    Get the Dispatcher class from the App Context
    """
    if 'dispatcher' not in __galicaster_context:
        __galicaster_context['dispatcher'] = Dispatcher()

    return __galicaster_context['dispatcher']


def get_repository():
    """
    Get the Mediapackage Repository from the App Context
    """
    if 'repository' not in __galicaster_context:
        conf = get_conf()
        template = conf.get('repository','foldertemplate')
        if template is None:
            __galicaster_context['repository'] = Repository(
                conf.get('basic', 'repository'), 
                conf.hostname,
                logger=get_logger())
        else:
            __galicaster_context['repository'] = Repository(
                conf.get('basic', 'repository'), 
                conf.hostname,
                conf.get('repository', 'foldertemplate'),
                get_logger())

    return __galicaster_context['repository']


def get_worker():
    """
    Get Galicaster Worker from the App Context
    """
    legacy = get_conf().get_boolean('ingest', 'legacy') or get_conf().get_boolean('basic', 'legacy')
    if 'worker' not in __galicaster_context:
        __galicaster_context['worker'] = Worker(get_dispatcher(),
                                                get_repository(),
                                                get_logger(),
                                                get_mhclient(),
                                                get_conf().get('basic', 'export'),
                                                get_conf().get('basic', 'tmp'),
                                                not legacy,
                                                get_conf().get('sidebyside', 'layout'),
                                                get_conf().get_list('operations', 'hide'),
                                                get_conf().get_list('operations', 'hide_nightly'))

    return __galicaster_context['worker']


def get_mainwindow():
    """
    Get Galicaster Mainwindow from the App Context
    """
    if 'mainwindow' not in __galicaster_context:
        __galicaster_context['mainwindow'] = GCWindow(get_dispatcher(), 
                                                      get_state(), 
                                                      get_conf().get_size(), 
                                                      get_logger())

    return __galicaster_context['mainwindow']


def get_heartbeat():
    """
    Get Galicaster Heartbeat from the App Context
    """
    # TODO Review
    if 'heartbeat' not in __galicaster_context:
        heartbeat = Heartbeat(get_dispatcher(), 
                      get_conf().get_int('heartbeat', 'short'),
                      get_conf().get_int('heartbeat', 'long'),                      
                      get_conf().get('heartbeat', 'night'),
                      get_logger())
        __galicaster_context['heartbeat'] = heartbeat

    return __galicaster_context['heartbeat']
    

def get_scheduler():
    """
    Get Galicaster Scheduler from the App Context
    """
    if 'scheduler' not in __galicaster_context:
        if get_conf().get_boolean("ingest", "active"):
            sch = Scheduler(get_repository(), get_conf(), get_dispatcher(), 
                            get_mhclient(), get_logger(), get_state())
        else:
            sch = None
        __galicaster_context['scheduler'] = sch

    return __galicaster_context['scheduler']
    

def get_state():
    """
    Get Galicaster State
    """
    if 'state' not in __galicaster_context:
        state = State(get_conf().hostname)
        __galicaster_context['state'] = state

    return __galicaster_context['state']
    
