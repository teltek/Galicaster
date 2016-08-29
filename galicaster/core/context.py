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


__galicaster_context = {}

"""
This module initializes:
    Conf: parser of the user's configuration. See core/conf.py
    Logger: in charge of printing warnings, errors and information messages. See core/logger.py
    Dispatcher: contains all the signals that communicates different parts of Galicaster app. See core/dispatcher.py
    Repository: contains and manages all the mediapackages. See mediapackage/repository.py
    Worker: in charge of processing long mediapackage operations. See core/worker.py
    OCClient (Opencast's client): communicates with Opencast. See opencast/client.py
    Mainwindow: the UI. See classui/mainwindow.py
    Heartbeat: in charge of emitting signals in long and short periods of time. See scheduler/heartbeat.py
    Scheduler: manages scheduled recordings. See scheduler/scheduler.py
    State: state of Galicaster. See core/state.py
"""

def get(service_name):
    """Gets service by name from the App Context.
    Returns:
        Obj: the service of the given name.
    """
    return __galicaster_context[service_name]


def has(service_name):
    """Checks if the service of the given service name is in the App Context.
    Args:
        service_name (str): the name of the service whose belonging to context is going to be checked.
    """
    return service_name in __galicaster_context


def set(service_name, service):
    """Sets service by name in the App Context.
    Args:
        service_name (str): the name of the service that is going to be set.
        service (Obj): the service that is going to be set.
    """
    __galicaster_context[service_name] = service


def delete(service_name):
    """Deletes service by name from the App Context.
    Args:
        service_name (str): the name of the service that is going to be deleted.
    """
    del __galicaster_context[service_name]


def get_conf():
    """Creates if necessary and retrieves the Conf class from the App Context.
    Returns:
        Conf: the conf instantiation in galicaster context.
    """
    from galicaster.core.conf import Conf

    if 'conf' not in __galicaster_context:
        __galicaster_context['conf'] = Conf()
        __galicaster_context['conf'].reload()

    return __galicaster_context['conf']


def get_logger():
    """Creates if necessary and retrieves the Logger class from the App Context.
    Returns:
        Logger: the logger in galicaster app.
    """
    from galicaster.core.logger import Logger

    if 'logger' not in __galicaster_context:
        conf = get_conf()
        logger = Logger(conf.get('logger', 'path'),
                        conf.get_choice_uppercase('logger', 'level', ['CRITICAL', 'ERROR', 'WARN', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'], 'DEBUG'),
                        conf.get_boolean('logger', 'rotate'),
                        conf.get_boolean('logger', 'use_syslog'))
        __galicaster_context['logger'] = logger
        conf.logger = logger

    return __galicaster_context['logger']


def get_occlient():
    """Creates if necessary and retrieves the OCclient class from the App Context.
    Returns:
        OCHTTPClient: the opencast client of galicaster context.
    """
    from galicaster.opencast.client import OCHTTPClient

    if 'occlient' not in __galicaster_context:
        conf = get_conf()
        multiple_ingest  = conf.get_boolean('ingest','multiple-ingest') or False
        connect_timeout = conf.get_int('ingest', 'connect_timeout') or 2
        timeout = conf.get_int('ingest', 'timeout') or 2
        if get_conf().get_boolean("ingest", "active"):
            occlient = OCHTTPClient(conf.get('ingest', 'host'),
                                    conf.get('ingest', 'username'),
                                    conf.get('ingest', 'password'),
                                    conf.get_hostname(),
                                    conf.get('ingest', 'address'),
                                    multiple_ingest,
                                    connect_timeout,
                                    timeout,
                                    conf.get('ingest', 'workflow'),
                                    conf.get_dict('ingest', 'workflow-parameters'),
                                    conf.get_dict('ingest', 'ca-parameters'),
                                    conf.get('heartbeat', 'short'),
                                    conf.get('heartbeat', 'long'),
                                    get_repository(),
                                    get_logger())
        else:
            occlient = None
        __galicaster_context['occlient'] = occlient

    return __galicaster_context['occlient']


def get_ocservice():
    """Creates if necessary and retrieves the Ocservice class from the App Context.
    Returns:
        OCService: the opencast service of galicaster context.
    """
    from galicaster.opencast.service import OCService

    if 'ocservice' not in __galicaster_context:
        conf = get_conf()
        if conf.get_boolean("ingest", "active"):
            ocservice = OCService(get_repository(),
                                  get_occlient(),
                                  get_scheduler(),
                                  get_conf(),
                                  get_dispatcher(),
                                  get_logger(),
                                  get_recorder())
        else:
            ocservice = None
        __galicaster_context['ocservice'] = ocservice

    return __galicaster_context['ocservice']


def get_dispatcher():
    """Creates if necessary and retrieves the Dispatcher class from the App Context.
    Returns:
      Dispatcher: the dispatcher instance in galicaster context.
    """
    from galicaster.core.dispatcher import Dispatcher

    if 'dispatcher' not in __galicaster_context:
        __galicaster_context['dispatcher'] = Dispatcher()

    return __galicaster_context['dispatcher']


def get_repository():
    """Creates if necessary and retrieves the Mediapackage Repository from the App Context.
    Returns:
        Mediapackage: mediapackage instance in galicaster context.
    """
    from galicaster.mediapackage.repository import Repository

    if 'repository' not in __galicaster_context:
        conf = get_conf()
        template = conf.get('repository','foldertemplate')
        __galicaster_context['repository'] = Repository(
            conf.get('basic', 'repository'),
            conf.get_hostname(),
            template,
            get_logger())

    return __galicaster_context['repository']


def get_worker():
    """Creates if necessary and retrieves the Galicaster Worker from the App Context.
    Returns:
        Worker: the worker instance in galicaster context.
    """
    from galicaster.core.worker import Worker

    legacy = get_conf().get_boolean('ingest', 'legacy') or get_conf().get_boolean('basic', 'legacy')
    if 'worker' not in __galicaster_context:
        __galicaster_context['worker'] = Worker(get_dispatcher(),
                                                get_repository(),
                                                get_logger(),
                                                get_occlient(),
                                                get_conf().get('basic', 'export'),
                                                get_conf().get('basic', 'tmp'),
                                                not legacy,
                                                get_conf().get('sidebyside', 'layout'),
                                                get_conf().get_list('operations', 'hide'),
                                                get_conf().get_list('operations', 'hide_nightly'))

    return __galicaster_context['worker']


def get_mainwindow():
    """Creates if necessary and retrieves Galicaster Mainwindow from the App Context.
    Returns:
        GCWindow: the galicaster main window instance in galicaster context.
    """
    from galicaster.classui.mainwindow import GCWindow

    if 'mainwindow' not in __galicaster_context:
        __galicaster_context['mainwindow'] = GCWindow(get_dispatcher(),
                                                      get_conf().get_size(),
                                                      get_logger())

    return __galicaster_context['mainwindow']


def get_heartbeat():
    """Creates if necessary and retrieves Galicaster Heartbeat from the App Context.
    Returns:
        Heartbeat: the heartbeat instance in galicaster context.
    """
    from galicaster.scheduler.heartbeat import Heartbeat

    # TODO Review
    if 'heartbeat' not in __galicaster_context:
        heartbeat = Heartbeat(get_dispatcher(),
                      get_conf().get_int('heartbeat', 'short', 10),
                      get_conf().get_int('heartbeat', 'long', 60),
                      get_conf().get_hour('heartbeat', 'night', '00:00'),
                      get_logger())
        __galicaster_context['heartbeat'] = heartbeat

    return __galicaster_context['heartbeat']


def get_scheduler():
    """Creates if necessary and retrieves Galicaster Scheduler from the App Context.
    Returns:
        Scheduler: the scheduler instance in galicaster context.
    """
    from galicaster.scheduler.scheduler import Scheduler

    if 'scheduler' not in __galicaster_context:
        sch = Scheduler(get_repository(), get_conf(), get_dispatcher(),
                        get_logger(), get_recorder())
        __galicaster_context['scheduler'] = sch

    return __galicaster_context['scheduler']


def get_recorder():
    """Creates if necessary and retrives Galicaster Recorder from the App Context.
    Returns:
        Recorder: the recorder instance in galicaster context.
    """
    from galicaster.recorder.service import RecorderService

    if 'recorder' not in __galicaster_context:
        recorder = RecorderService(get_dispatcher(),
                                   get_repository(),
                                   get_worker(),
                                   get_conf(),
                                   get_logger(),
                                   get_conf().get_boolean('recorder','autorecover', False))
        __galicaster_context['recorder'] = recorder

    return __galicaster_context['recorder']
