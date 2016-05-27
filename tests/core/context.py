# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/core/context
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


"""
Unit tests for `galicaster.core.context` module.
"""
import socket
from unittest import TestCase

from galicaster.core import context
import galicaster

class TestFunctions(TestCase):

    def test_twice(self):
        conf1 = context.get_conf()
        conf2 = context.get_conf()
        self.assertEqual(id(conf1), id(conf2))

    def test_getter_setter(self):
        service_name = 'pr'
        service = 'Service'
        other_service = 'Other service'
        self.assertRaises(KeyError, context.get, service_name)
        context.set(service_name, service)
        self.assertEqual(service, context.get(service_name))
        context.set(service_name, other_service)
        self.assertNotEqual(service, context.get(service_name))
        self.assertEqual(other_service, context.get(service_name))
        context.delete(service_name)
        self.assertRaises(KeyError, context.get, service_name)
    
    def test_context(self):
        self.assertNotEqual(type(context.get_conf()), galicaster.core.conf)
        self.assertEqual(type(context.get_conf()), galicaster.core.conf.Conf)
        self.assertEqual(type(context.get_dispatcher()), galicaster.core.dispatcher.Dispatcher)
        self.assertEqual(type(context.get_repository()), galicaster.mediapackage.repository.Repository)


    def test_get_scheduler_and_occlient_none(self):
        conf = context.get_conf()

        conf.set('ingest', 'active', 'False')
        self.assertEqual(context.get_occlient(), None)
        self.assertEqual(context.get_scheduler(), None)

        context.delete('occlient')
        context.delete('scheduler')
        conf.set('ingest', 'active', 'True')
        self.assertEqual(type(context.get_occlient()), galicaster.opencast.client.OCHTTPClient)
        self.assertEqual(type(context.get_scheduler()), galicaster.scheduler.scheduler.Scheduler)


    def test_get_occlient_with_config(self):
        # Context init in other test
        if context.has('occlient'):
            context.delete('occlient') 

        host = "http://servertest.www.es"
        conf = context.get_conf()
        conf.set('ingest', 'active', 'True')
        original_host = conf.get('ingest', 'host')
        conf.set('ingest', 'host', host)
        client = context.get_occlient()
        self.assertNotEqual(original_host, client.server)
        self.assertEqual(host, client.server)

        context.delete('occlient') # Context init in other test
        conf.remove_option('ingest', 'hostname')
        conf.set('ingest' , 'hostname', 'foobar')
        client = context.get_occlient()
        self.assertEqual('foobar', client.hostname)

        context.delete('occlient') # Context init in other test
        conf.set('basic', 'admin', 'False')
        conf.remove_option('ingest', 'hostname')
        conf.hostname = conf.get_hostname()
        client = context.get_occlient()
        self.assertEqual('GC-' + socket.gethostname(), client.hostname)

        context.delete('occlient') # Context init in other test
        conf.set('basic', 'admin', 'True')
        conf.remove_option('ingest', 'hostname')
        conf.hostname = conf.get_hostname()
        client = context.get_occlient()
        self.assertEqual('GCMobile-' + socket.gethostname(), client.hostname)

        context.delete('conf') # To other test
        context.delete('occlient') # To other test


        
    




