# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/opencast/client
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


"""
Unit tests for `galicaster.opencast` module.

Disble by default. You can enable it to test MatterHorn HTTP Client.
"""
import os
import socket
import pycurl
import json
from xml.dom.minidom import parseString
from unittest import TestCase
from unittest import skip
from nose.plugins.attrib import attr

from galicaster.opencast.client import OCHTTPClient


@attr('nodefault', 'opencast')
class TestFunctions(TestCase):

    def test_init(self):
        server = 'http://demo.opencastproject.org:8080'
        user = 'opencast_system_account';
        password = 'CHANGE_ME';
        hostname = 'GalicasterTestHost'
        address = '8.8.8.8'
        multiple_ingest = False
        connect_timeout = 2
        timeout = 2
        workflow = 'mini-full'
        workflow_parameters = {'uno': 'uno'}
        workflow_parameters_2 = {'uno': 'uno', 'dos': 'dos'}

        client = OCHTTPClient(server, user, password)
        self.assertEqual(client.hostname, 'galicaster')
        self.assertEqual(client.address, socket.gethostbyname(socket.gethostname()))

        client = OCHTTPClient(server, user, password, hostname)
        self.assertEqual(client.hostname, hostname)
        self.assertEqual(client.address, socket.gethostbyname(socket.gethostname()))

        client = OCHTTPClient(server, user, password, hostname, address)
        self.assertEqual(client.hostname, hostname)
        self.assertEqual(client.address, address)

        client = OCHTTPClient(server, user, password, hostname, address)
        self.assertEqual(client.workflow, 'full')
        self.assertEqual(client.workflow_parameters, {'trimHold': 'true'})

        client = OCHTTPClient(server, user, password, hostname, address, multiple_ingest, connect_timeout, timeout)
        self.assertEqual(client.multiple_ingest, multiple_ingest)
        self.assertEqual(client.connect_timeout, connect_timeout)
        self.assertEqual(client.timeout, timeout)

        client = OCHTTPClient(server, user, password, hostname, address, multiple_ingest, connect_timeout, timeout, workflow, workflow_parameters)
        self.assertEqual(client.workflow, 'mini-full')
        self.assertEqual(client.workflow_parameters, workflow_parameters)

        client = OCHTTPClient(server, user, password, hostname, address, multiple_ingest, connect_timeout, timeout, workflow, workflow_parameters_2)
        self.assertEqual(client.workflow, 'mini-full')
        self.assertEqual(client.workflow_parameters, workflow_parameters_2)



    def test_prepare_ingest(self):
        workflow = 'mini-full'
        workflow_parameters = {'uno': 'uno', 'dos': 'dos'}
        client = OCHTTPClient(None, None, None, None, None, False, 2, 2, workflow, workflow_parameters)
        
        # Default values
        postdict = client._prepare_ingest('file')
        self.assertEqual(postdict, {'workflowDefinitionId': 'mini-full', 'track': (pycurl.FORM_FILE, 'file'),
                                    'uno': 'uno', 'dos': 'dos'})

        # Other workflow
        postdict = client._prepare_ingest('file', 'other-workflow')
        self.assertEqual(postdict, {'workflowDefinitionId': 'other-workflow', 'track': (pycurl.FORM_FILE, 'file'),
                                    'uno': 'uno', 'dos': 'dos'})

        # With workflow_instance
        postdict = client._prepare_ingest('file', 'other-workflow', 342)
        self.assertEqual(postdict, {'workflowDefinitionId': 'other-workflow', 'track': (pycurl.FORM_FILE, 'file'),
                                    'workflowInstanceId': '342', 'uno': 'uno', 'dos': 'dos'})

        # Other workflow_parameters
        postdict = client._prepare_ingest('file', workflow='other-workflow', workflow_parameters={'diezuno': 'diez'})
        self.assertEqual(postdict, {'workflowDefinitionId': 'other-workflow', 'track': (pycurl.FORM_FILE, 'file'),
                                    'diezuno': 'diez'})

        # Other workflow_parameters as string
        postdict = client._prepare_ingest('file', workflow='other-workflow', workflow_parameters='diezdos:8)')
        self.assertEqual(postdict, {'workflowDefinitionId': 'other-workflow', 'track': (pycurl.FORM_FILE, 'file'),
                                    'diezdos': '8)'})

        # All diferent
        postdict = client._prepare_ingest('file', 'other-workflow', 1342, {'param': 'false', 'param2': 'true'})
        self.assertEqual(postdict, {'workflowDefinitionId': 'other-workflow', 'track': (pycurl.FORM_FILE, 'file'),
                                    'workflowInstanceId': '1342', 'param': 'false', 'param2': 'true'})
        
        
    # OC-MH whoami endpoint return anonymous.
    def test_whoami(self):
        server = 'http://demo.opencastproject.org:8080'
        user = 'opencast_system_account'
        password = 'CHANGE_ME'

        client = OCHTTPClient(server, user, password)
        oc_user = client.whoami()

        self.assertEqual(oc_user['username'], 'opencast_system_account')


    def test_whoami(self):
        server = 'http://demo.opencastproject.org:8080'
        user = 'opencast_system_account'
        password = 'CHANGE_ME'

        client = OCHTTPClient(server, user, password)
        oc_user = client.welcome()

        self.assertTrue(True)


    def test_series(self):
        server = 'http://demo.opencastproject.org:8080'
        user = 'opencast_system_account'
        password = 'CHANGE_ME'

        client = OCHTTPClient(server, user, password)
        series = client.getseries()    

        self.assertTrue(isinstance(series, basestring))
        self.assertTrue(isinstance(json.loads(series), dict))

    @skip("check endpoint")
    def test_setstate(self):
        server = 'http://demo.opencastproject.org:8080'
        user = 'opencast_system_account'
        password = 'CHANGE_ME'
        client_name = 'rubenrua_pr'
        client_address = '172.20.209.225'
        client_states = [ 'shutting_down', 'capturing', 'uploading', 'unknown', 'idle' ]        

        client = OCHTTPClient(server, user, password)
        client.hostname = client_name
        client.address = client_address
        
        for state in client_states:
            a = client.setstate(state)
            self.assertEqual(a, '{0} set to {1}'.format(client_name, state))


    @skip("check endpoint")
    def test_setcapabilities(self):
        server = 'http://demo.opencastproject.org:8080'
        user = 'opencast_system_account'
        password = 'CHANGE_ME'
        client_name = 'rubenrua_pr'
        client_address = '172.20.209.225'

        client = OCHTTPClient(server, user, password)
        client.hostname = client_name
        client.address = client_address
        
        out = parseString(client.setconfiguration({}))
        for item  in out.getElementsByTagName('item'):
            if item.getAttribute('key') == 'service.pid':
                self.assertEqual(item.firstChild.firstChild.wholeText, 'galicaster')


    def test_limit_init_duration(self):
        server = 'http://10.10.10.10:10'
        user = 'opencast_system_account'
        password = 'CHANGE_ME'

        client = OCHTTPClient(server, user, password)

        self.assertRaises(RuntimeError, client.welcome)
