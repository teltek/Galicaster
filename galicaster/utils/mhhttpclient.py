# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/mhhttpclient
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import re
import json
import urllib
import socket
#IDEA use cStringIO to improve performance
from StringIO import StringIO
import pycurl
from collections import OrderedDict

INIT_ENDPOINT = '/welcome.html'
ME_ENDPOINT = '/info/me.json'
SETRECORDINGSTATE_ENDPOINT = '/capture-admin/recordings/{id}'
SETSTATE_ENDPOINT = '/capture-admin/agents/{hostname}'
SETCONF_ENDPOINT = '/capture-admin/agents/{hostname}/configuration'
INGEST_ENDPOINT = '/ingest/addZippedMediaPackage'
ICAL_ENDPOINT = '/recordings/calendars?agentid={hostname}'
SERIES_ENDPOINT = '/series/series.json?count={count}' 
SERVICE_REGISTRY_ENDPOINT = '/services/available.json?serviceType={serviceType}'



class MHHTTPClient(object):
    
    def __init__(self, server, user, password, hostname='galicaster', address=None, multiple_ingest=False, 
                 workflow='full', workflow_parameters={'trimHold':'true'}, logger=None):
        """
        Arguments:

        server -- Matterhorn server URL.
        user -- Account used to operate the Matterhorn REST endpoints service.
        password -- Password for the account  used to operate the Matterhorn REST endpoints service.
        hostname -- Capture agent hostname, optional galicaster by default.
        address -- Capture agent IP address, optional socket.gethostbyname(socket.gethostname()) by default.
        workflow -- Name of the workflow used to ingest the recordings., optional `full` by default.
        workflow_parameters -- string (k1=v1;k2=v2) or dict of parameters used to ingest, opcional {'trimHold':'true'} by default.
        """
        self.server = server
        self.user = user
        self.password = password
        self.hostname = hostname
        self.address = address or socket.gethostbyname(socket.gethostname())
        self.multiple_ingest = multiple_ingest
        self.workflow = workflow
        self.logger = logger
        if isinstance(workflow_parameters, basestring):
            self.workflow_parameters = dict(item.split(":") for item in workflow_parameters.split(";"))
        else:
            self.workflow_parameters = workflow_parameters


    def __call(self, method, endpoint, params={}, postfield={}, urlencode=True, server=None, timeout=True):

        theServer = server or self.server
        c = pycurl.Curl()
        b = StringIO()
        c.setopt(pycurl.URL, theServer + endpoint.format(**params))
        c.setopt(pycurl.FOLLOWLOCATION, False)
        c.setopt(pycurl.CONNECTTIMEOUT, 2)
        if timeout: 
            c.setopt(pycurl.TIMEOUT, 2)
        c.setopt(pycurl.NOSIGNAL, 1)
        c.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_DIGEST)
        c.setopt(pycurl.USERPWD, self.user + ':' + self.password)
        c.setopt(pycurl.HTTPHEADER, ['X-Requested-Auth: Digest'])
        c.setopt(pycurl.USERAGENT, 'Galicaster')
        if (method == 'POST'):
            if urlencode:
                c.setopt(pycurl.POST, 1) 
                c.setopt(pycurl.POSTFIELDS, urllib.urlencode(postfield))
            else:
                c.setopt(pycurl.HTTPPOST, postfield)
        c.setopt(pycurl.WRITEFUNCTION, b.write)
        #c.setopt(pycurl.VERBOSE, True)
        try:
            c.perform()
        except:
            raise RuntimeError, 'connect timed out!'
        status_code = c.getinfo(pycurl.HTTP_CODE)
        c.close() 
        if status_code != 200:
            if self.logger:
                self.logger.error('call error in %s, status code {%r}', 
                                  theServer + endpoint.format(**params), status_code)
            raise IOError, 'Error in Matterhorn client'
        return b.getvalue()


    def whoami(self):
        return json.loads(self.__call('GET', ME_ENDPOINT))

    def welcome(self):
        return self.__call('GET', INIT_ENDPOINT)


    def ical(self):
        return self.__call('GET', ICAL_ENDPOINT, {'hostname': self.hostname})


    def setstate(self, state):
        """
        Los posibles estados son: shutting_down, capturing, uploading, unknown, idle
        """
        return self.__call('POST', SETSTATE_ENDPOINT, {'hostname': self.hostname}, 
                           {'address': self.address, 'state': state})


    def setrecordingstate(self, recording_id, state):
        """
        Los posibles estados son: unknown, capturing, capture_finished, capture_error, manifest, 
        manifest_error, manifest_finished, compressing, compressing_error, uploading, upload_finished, upload_error
        """
        return self.__call('POST', SETRECORDINGSTATE_ENDPOINT, {'id': recording_id}, {'state': state})


    def setconfiguration(self, capture_devices):
        client_conf_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                             <!DOCTYPE properties SYSTEM "http://java.sun.com/dtd/properties.dtd">
                             <properties version="1.0">{0}</properties>"""
        client_conf_xml_body = '<entry key="{key}">{value}</entry>'

        client_conf = {
            'service.pid': 'galicaster',
            'capture.confidence.debug': 'false',
            'capture.confidence.enable': 'false',            
            'capture.config.remote.polling.interval': '600',
            'capture.agent.name': self.hostname,
            'capture.agent.state.remote.polling.interval': '10',
            'capture.agent.capabilities.remote.polling.interval': '10',
            'capture.agent.state.remote.endpoint.url': self.server + '/capture-admin/agents',
            'capture.recording.shutdown.timeout': '60',
            'capture.recording.state.remote.endpoint.url': self.server + '/capture-admin/recordings',
            'capture.schedule.event.drop': 'false',
            'capture.schedule.remote.polling.interval': '1',
            'capture.schedule.event.buffertime': '1',
            'capture.schedule.remote.endpoint.url': self.server + '/recordings/calendars',
            'capture.schedule.cache.url': '/opt/matterhorn/storage/cache/schedule.ics',
            'capture.ingest.retry.interval': '300',
            'capture.ingest.retry.limit': '5',
            'capture.ingest.pause.time': '3600',
            'capture.cleaner.interval': '3600',
            'capture.cleaner.maxarchivaldays': '30',
            'capture.cleaner.mindiskspace': '536870912',
            'capture.error.messagebody': '&quot;Capture agent was not running, and was just started.&quot;',
            'capture.error.subject': '&quot;%hostname capture agent started at %date&quot;',
            'org.opencastproject.server.url': 'http://172.20.209.88:8080',
            'org.opencastproject.capture.core.url': self.server,
            'capture.max.length': '28800'
            }
        
        client_conf.update(capture_devices)

        xml = ""
        for k, v in client_conf.iteritems():
            xml = xml + client_conf_xml_body.format(key=k, value=v)
        client_conf = client_conf_xml.format(xml)

        return self.__call('POST', SETCONF_ENDPOINT, {'hostname': self.hostname}, {'configuration': client_conf})


    def _prepare_ingest(self, mp_file, workflow=None, workflow_instance=None, workflow_parameters=None):
        "refactor of ingest to unit test"
        postdict = OrderedDict()
        postdict[u'workflowDefinitionId'] = workflow or self.workflow
        if workflow_instance:
            postdict['workflowInstanceId'] = str(workflow_instance)
        if isinstance(workflow_parameters, basestring):
            postdict.update(dict(item.split(":") for item in workflow_parameters.split(";")))
        elif isinstance(workflow_parameters, dict) and workflow_parameters:
            postdict.update(workflow_parameters)
        else:
            postdict.update(self.workflow_parameters)
        postdict[u'track'] = (pycurl.FORM_FILE, mp_file)
        return postdict

    def verify_ingest_server(self, server):
        """ if we have multiple ingest servers the get_ingest_server should never 
        return the admin node to ingest to, This is verified by the IP address so 
        we can meke sure that it doesn't come up through a DNS alias, If all ingest 
        services are offline the ingest will still fall back to the server provided 
        to Galicaster as then None will be returned by get_ingest_server  """   
    
        p = '(?:http.*://)?(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*'
        m = re.search(p,server['host'])
        host=m.group('host')
        m = re.search(p,self.server)
        adminHost=m.group('host')
        if (not server['online']):
            return False
        if (server['maintenance']):
            return False
        adminIP = socket.gethostbyname(adminHost);
        hostIP = socket.gethostbyname(host)
        if (adminIP != hostIP):
            return True
        return False


    def get_ingest_server(self):
        """ get the ingest server information from the admin node: 
        if there are more than one ingest servers the first from the list will be used
        as they are returned in order of their load, if there is only one returned this 
        will be the admin node, so we can use the information we already have """ 
        servers = self.__call('GET', SERVICE_REGISTRY_ENDPOINT, {'serviceType':'org.opencastproject.ingest'}, {}, 
                              True, None, True)
        servers_avail = json.loads(servers)
        all_servers = servers_avail['services']['service']
        if type(all_servers) is list:
            for serv in all_servers:
                if self.verify_ingest_server(serv):
                    return str(serv['host']) # Returns less loaded served
        if self.verify_ingest_server(all_servers):
            return str(all_servers['host']) # There's only one server
        return None # it will use the admin server
 
    def ingest(self, mp_file, workflow=None, workflow_instance=None, workflow_parameters=None):
        postdict = self._prepare_ingest(mp_file, workflow, workflow_instance, workflow_parameters)
        server = self.server if not self.multiple_ingest else self.get_ingest_server()
        self.logger.info( 'Ingesting to Server {0}'.format(server) ) 
        return self.__call('POST', INGEST_ENDPOINT, {}, postdict.items(), False, server, False)


    def getseries(self):
        """ Get all series upto 100"""
        # TODO No limit, to get all
        return self.__call('GET', SERIES_ENDPOINT, {'count': 100})
        
