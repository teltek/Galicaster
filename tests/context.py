# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/context
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
        self.assertEqual(type(context.get_mhclient()), galicaster.utils.mhhttpclient.MHHTTPClient)


    def test_get_mhclient_with_config(self):
        context.delete('mhclient') # Context init in other test
        host = "http://servertest.www.es"
        conf = context.get_conf()
        original_host = conf.get('ingest', 'host')
        conf.set('ingest', 'host', host)
        client = context.get_mhclient()
        self.assertNotEqual(original_host, client.server)
        self.assertEqual(host, client.server)

        context.delete('mhclient') # Context init in other test
        hostname = 'foobar'
        conf.set('ingest', 'hostname', hostname)
        client = context.get_mhclient()
        self.assertEqual(hostname, client.hostname)

        context.delete('mhclient') # Context init in other test
        conf.remove_option('ingest', 'hostname')
        client = context.get_mhclient()
        self.assertEqual('GC-' + socket.gethostname(), client.hostname)

        context.delete('conf') # To other test
        context.delete('mhclient') # To other test


        
    




