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
from galicaster.core.worker import Worker
from galicaster.core.dispatcher import Dispatcher
from galicaster.classui.mainwindow import GCWindow


__galicaster_context = {}


def get(service_name):
    """
    Get service by name from the App Context
    """
    return __galicaster_context[service_name]


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
    

def get_conf(conf_file=None, conf_dist_file=None):
    """
    Get the Conf class from the App Context
    """
    if 'conf' not in __galicaster_context:
        __galicaster_context['conf'] = Conf(conf_file, conf_dist_file)

    return __galicaster_context['conf']


def get_mhclient():
    """
    Get the Mhclient class from the App Context
    """
    if 'mhclient' not in __galicaster_context:
        conf = get_conf()
        __galicaster_context['mhclient'] = MHHTTPClient(conf.get('ingest', 'host'), 
                                                        conf.get('ingest', 'username'), 
                                                        conf.get('ingest', 'password'), 
                                                        conf.get('ingest', 'hostname'), 
                                                        conf.get('ingest', 'address'),
                                                        conf.get('ingest', 'workflow'),
                                                        conf.get('ingest', 'workflow-parameters'))


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
        __galicaster_context['repository'] = Repository(get_conf().get('basic', 'repository'))

    return __galicaster_context['repository']

def get_worker():
    """
    Get Galicaster Worker from the App Context
    """
    if 'worker' not in __galicaster_context:
        __galicaster_context['worker'] = Worker(get_repository(),
                                                get_mhclient(),
                                                get_dispatcher())

    return __galicaster_context['worker']


def get_mainwindow():
    """
    Get Galicaster Mainwindow from the App Context
    """
    if 'mainwindow' not in __galicaster_context:
        __galicaster_context['mainwindow'] = GCWindow(get_dispatcher())

    return __galicaster_context['mainwindow']
