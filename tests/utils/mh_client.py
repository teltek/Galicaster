# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/utils/mh_client
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


"""
Unit tests for `galicaster.utils` module.

Disble by default. You can enable it to test MatterHorn HTTP Client.
"""
import socket
import pycurl
import json
from xml.dom.minidom import parseString
from unittest import TestCase

from galicaster.utils.mhhttpclient import MHHTTPClient

class TestFunctions(TestCase):

    def no_test_userandaddressinit(self):
        server = 'http://demo.opencastproject.org'
        user = 'matterhorn_system_account';
        password = 'CHANGE_ME';
        hostname = 'rubenruaHost'
        address = '8.8.8.8'
        workflow = 'mini-full'
        workflow_parameters = {'uno': 'uno'}
        workflow_parameters_2 = {'uno': 'uno', 'dos': 'dos'}

        client = MHHTTPClient(server, user, password)
        self.assertEqual(client.hostname, 'galicaster')
        self.assertEqual(client.address, socket.gethostbyname(socket.gethostname()))

        client = MHHTTPClient(server, user, password, hostname)
        self.assertEqual(client.hostname, hostname)
        self.assertEqual(client.address, socket.gethostbyname(socket.gethostname()))

        client = MHHTTPClient(server, user, password, hostname, address)
        self.assertEqual(client.hostname, hostname)
        self.assertEqual(client.address, address)

        client = MHHTTPClient(server, user, password, hostname, address)
        self.assertEqual(client.workflow, 'full')
        self.assertEqual(client.workflow_parameters, {'trimHold': 'true'})

        client = MHHTTPClient(server, user, password, hostname, address, workflow, workflow_parameters)
        self.assertEqual(client.workflow, 'mini-full')
        self.assertEqual(client.workflow_parameters, workflow_parameters)

        client = MHHTTPClient(server, user, password, hostname, address, workflow, workflow_parameters_2)
        self.assertEqual(client.workflow, 'mini-full')
        self.assertEqual(client.workflow_parameters, workflow_parameters_2)



    def no_test_prepare_ingest(self):
        workflow = 'mini-full'
        workflow_parameters = {'uno': 'uno', 'dos': 'dos'}
        client = MHHTTPClient(None, None, None, None, None, workflow, workflow_parameters)
        
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
    def no_test_whoami(self):
        server = 'http://demo.opencastproject.org'
        user = 'matterhorn_system_account'
        password = 'CHANGE_ME'

        client = MHHTTPClient(server, user, password)
        mh_user = client.whoami()

        self.assertEqual(mh_user['username'], 'matterhorn_system_account')


    def no_test_whoami(self):
        server = 'http://demo.opencastproject.org'
        user = 'matterhorn_system_account'
        password = 'CHANGE_ME'

        client = MHHTTPClient(server, user, password)
        mh_user = client.welcome()

        self.assertTrue(True)


    def no_test_series(self):
        server = 'http://demo.opencastproject.org'
        user = 'matterhorn_system_account'
        password = 'CHANGE_ME'

        client = MHHTTPClient(server, user, password)
        series = client.getseries()    

        self.assertTrue(isinstance(series, basestring))
        self.assertTrue(isinstance(json.loads(series), dict))


    def no_test_setstate(self):
        server = 'http://demo.opencastproject.org'
        user = 'matterhorn_system_account'
        password = 'CHANGE_ME'
        client_name = 'rubenrua_pr'
        client_address = '172.20.209.225'
        client_states = [ 'shutting_down', 'capturing', 'uploading', 'unknown', 'idle' ]        

        client = MHHTTPClient(server, user, password)
        client.hostname = client_name
        client.address = client_address
        
        for state in client_states:
            a = client.setstate(state)
            self.assertEqual(a, '{0} set to {1}'.format(client_name, state))


    def no_test_setcapabilities(self):
        server = 'http://demo.opencastproject.org'
        user = 'matterhorn_system_account'
        password = 'CHANGE_ME'
        client_name = 'rubenrua_pr'
        client_address = '172.20.209.225'

        client = MHHTTPClient(server, user, password)
        client.hostname = client_name
        client.address = client_address
        
        out = parseString(client.setconfiguration({}))
        for item  in out.getElementsByTagName('item'):
            if item.getAttribute('key') == 'service.pid':
                self.assertEqual(item.firstChild.firstChild.wholeText, 'galicaster')


    def no_test_limit_init_duration(self):
        server = 'http://10.10.10.10:10'
        user = 'matterhorn_system_account'
        password = 'CHANGE_ME'

        client = MHHTTPClient(server, user, password)

        self.assertRaises(RuntimeError, client.welcome)
