# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/opencast/client
#
# Copyright (c) 2016, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import re
import json
import socket
#IDEA use cStringIO to improve performance
from StringIO import StringIO
import pycurl
from collections import OrderedDict
import urlparse
import urllib

try:
    from galicaster import __version__ as version
except:
    version = ""

INIT_ENDPOINT = '/info/me.json'
ME_ENDPOINT = '/info/me.json'
SETRECORDINGSTATE_ENDPOINT = '/capture-admin/recordings/{id}'
SETSTATE_ENDPOINT = '/capture-admin/agents/{hostname}'
SETCONF_ENDPOINT = '/capture-admin/agents/{hostname}/configuration'
INGEST_ENDPOINT = '/ingest/addZippedMediaPackage'
ICAL_ENDPOINT = '/recordings/calendars'
SERIES_ENDPOINT = '/series/series.json'
SERVICE_REGISTRY_ENDPOINT = '/services/available.json'
SEARCH_ENDPOINT = '/search/episode.json'
WORKFLOWS_ENDPOINT = '/workflow/definitions.json'

SEARCH_SERVICE_TYPE = 'org.opencastproject.search'
INGEST_SERVICE_TYPE = 'org.opencastproject.ingest'


class OCHTTPClient(object):
    
    def __init__(self, server, user, password, hostname='galicaster', address=None, multiple_ingest=False, 
                 connect_timeout=2, timeout=2, workflow='full', workflow_parameters={'trimHold':'true'}, 
                 ca_parameters={}, polling_short=10, polling_long=60, repo=None, logger=None):
        """
        Arguments:

        server -- Opencast server URL.
        user -- Account used to operate the Opencast REST endpoints service.
        password -- Password for the account  used to operate the Opencast REST endpoints service.
        hostname -- Capture agent hostname, optional galicaster by default.
        address -- Capture agent IP address, optional socket.gethostbyname(socket.gethostname()) by default.
        multiple_ingest -- Use an ingest node, optional False by default.
        connect_timeout -- Connection timeout for curl in seconds.
        timeout -- Total timeout for curl in seconds .
        workflow -- Name of the workflow used to ingest the recordings., optional `full` by default.
        workflow_parameters -- Dict of parameters used to ingest, opcional {'trimHold':'true'} by default.
        ca_parameters -- Dict of parameters used as configuration, optional empty by default.
        logger -- Logger service.
        repo -- Repository service.
        """
        self.server = server
        self.user = user
        self.password = password
        self.hostname = hostname

        if address:
            self.address = address
        else:
            try:
                self.address = socket.gethostbyname(socket.gethostname())
            except Exception as exc:
                logger and logger.error('Problem on obtaining the IP of "{}", forced to "127.0.0.1". Exception: {}'.format(socket.gethostname(),exc))
                self.address = '127.0.0.1'

        self.multiple_ingest = multiple_ingest
        self.connect_timeout = connect_timeout
        self.timeout = timeout
        self.workflow = workflow
        self.logger = logger
        self.repo = repo
        self.workflow_parameters = workflow_parameters
        self.workflow_names = []
        self.ca_parameters = ca_parameters
        self.search_server = None
        self.polling_schedule = polling_long
        self.polling_state = polling_short
        # FIXME should be long? https://github.com/teltek/Galicaster/issues/114
        self.polling_caps = polling_short
        self.polling_config = polling_long        
        self.response = {'Status-Code': '', 'Content-Type': '', 'ETag': ''}
        self.ical_etag = -1



    def __call(self, method, endpoint, path_params={}, query_params={}, postfield={}, urlencode=True, server=None, timeout=True, headers={}):

        theServer = server or self.server
        c = pycurl.Curl()
        b = StringIO()

        url = list(urlparse.urlparse(theServer, 'http'))
        url[2] = urlparse.urljoin(url[2], endpoint.format(**path_params))
        url[4] = urllib.urlencode(query_params)
        c.setopt(pycurl.URL, urlparse.urlunparse(url))

        c.setopt(pycurl.FOLLOWLOCATION, False)
        c.setopt(pycurl.CONNECTTIMEOUT, self.connect_timeout)
        if timeout: 
            c.setopt(pycurl.TIMEOUT, self.timeout)
        c.setopt(pycurl.NOSIGNAL, 1)
        c.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_DIGEST)
        c.setopt(pycurl.USERPWD, self.user + ':' + self.password)
        sendheaders = ['X-Requested-Auth: Digest', 'X-Matterhorn-Opencast-Authorization: true']
        if headers:
            for h, v in headers.iteritems():
                sendheaders.append('{}: {}'.format(h, v))
            # implies we might be interested in passing the response headers
            c.setopt(pycurl.HEADERFUNCTION, self.scanforetag)
        c.setopt(pycurl.HTTPHEADER, sendheaders)
        c.setopt(pycurl.USERAGENT, 'Galicaster' + version)
        c.setopt(pycurl.SSL_VERIFYPEER, False) # equivalent to curl's --insecure
       
        if (method == 'POST'):
            if urlencode:
                c.setopt(pycurl.POST, 1) 
                c.setopt(pycurl.POSTFIELDS, urllib.urlencode(postfield))
            else:
                c.setopt(pycurl.HTTPPOST, postfield)
        c.setopt(pycurl.WRITEFUNCTION, b.write)

        #c.setopt(pycurl.VERBOSE, True) ##TO DEBUG
        try:
            c.perform()
        except Exception as exc:
            raise RuntimeError, exc
        
        status_code = c.getinfo(pycurl.HTTP_CODE)
        self.response['Status-Code'] = status_code
        self.response['Content-Type'] = c.getinfo(pycurl.CONTENT_TYPE)
        c.close()
        if status_code != 200 and status_code != 302 and status_code != 304:
            if (status_code > 200) and (status_code < 300):
                self.logger and self.logger.debug("Opencast client ({}) sent a response with status code {}".format(urlparse.urlunparse(url), status_code))
            else:
                title = self.find_between(b.getvalue(), "<title>", "</title>")
                self.logger and self.logger.error('call error in %s, status code {%r}: %s', 
                                                  urlparse.urlunparse(url), status_code, title)
                raise IOError, 'Error in Opencast client'

        return b.getvalue()

    def scanforetag(self, buffer):
        if buffer.startswith('ETag:'):
            etag = buffer[5:]
            self.response['ETag'] = etag.strip()

    def whoami(self):
        return json.loads(self.__call('GET', ME_ENDPOINT))

    def welcome(self):
        return self.__call('GET', INIT_ENDPOINT)


    def ical(self):
        icalendar = self.__call('GET', ICAL_ENDPOINT, query_params={'agentid': self.hostname}, headers={'If-None-Match': self.ical_etag})

        if self.response['Status-Code'] == 304:
            if self.logger:
                self.logger.info("iCal Not modified")
            return None

        self.ical_etag = self.response['ETag']
        if self.logger:
                self.logger.info("iCal modified")
        return icalendar


    def setstate(self, state):
        """
        Los posibles estados son: shutting_down, capturing, uploading, unknown, idle
        """
        self.logger and self.logger.info("Sending state {}".format(state))
        return self.__call('POST', SETSTATE_ENDPOINT, {'hostname': self.hostname},
                           postfield={'address': self.address, 'state': state})


    def setrecordingstate(self, recording_id, state):
        """
        Los posibles estados son: unknown, capturing, capture_finished, capture_error, manifest, 
        manifest_error, manifest_finished, compressing, compressing_error, uploading, upload_finished, upload_error
        """
        return self.__call('POST', SETRECORDINGSTATE_ENDPOINT, {'id': recording_id}, postfield={'state': state})


    def setconfiguration(self, capture_devices):
        client_conf_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                             <!DOCTYPE properties SYSTEM "http://java.sun.com/dtd/properties.dtd">
                             <properties version="1.0">{0}</properties>"""
        client_conf_xml_body = '<entry key="{key}">{value}</entry>'

        client_conf = {
            'service.pid': 'galicaster',
            'capture.confidence.debug': 'false',
            'capture.confidence.enable': 'false',
            'capture.config.remote.polling.interval': self.polling_config,
            'capture.agent.name': self.hostname,
            'capture.agent.state.remote.polling.interval': self.polling_state,
            'capture.agent.capabilities.remote.polling.interval': self.polling_caps,
            'capture.agent.state.remote.endpoint.url': self.server + '/capture-admin/agents',
            'capture.recording.shutdown.timeout': '60',
            'capture.recording.state.remote.endpoint.url': self.server + '/capture-admin/recordings',
            'capture.schedule.event.drop': 'false',
            'capture.schedule.remote.polling.interval': int(self.polling_schedule)/60,
            'capture.schedule.event.buffertime': '1',
            'capture.schedule.remote.endpoint.url': self.server + '/recordings/calendars',
            'capture.schedule.cache.url': '/opt/opencast/storage/cache/schedule.ics',
            'capture.ingest.retry.interval': '300',
            'capture.ingest.retry.limit': '5',
            'capture.ingest.pause.time': '3600',
            'capture.cleaner.interval': '3600',
            'capture.cleaner.maxarchivaldays': '30',
            'capture.cleaner.mindiskspace': '0',
            'capture.error.messagebody': '&quot;Capture agent was not running, and was just started.&quot;',
            'capture.error.subject': '&quot;%hostname capture agent started at %date&quot;',
            'org.opencastproject.server.url': 'http://172.20.209.88:8080',
            'org.opencastproject.capture.core.url': self.server,
            'capture.max.length': '28800'
            }
        
        if self.repo:
            client_conf['capture.cleaner.mindiskspace'] = self.repo.get_free_space()

        client_conf.update(capture_devices)
        client_conf.update(self.ca_parameters)

        xml = ""
        for k, v in client_conf.iteritems():
            xml = xml + client_conf_xml_body.format(key=k, value=v)
        client_conf = client_conf_xml.format(xml)
        return self.__call('POST', SETCONF_ENDPOINT, {'hostname': self.hostname}, postfield={'configuration': client_conf})


    def _prepare_ingest(self, mp_file, workflow=None, workflow_instance=None, workflow_parameters=None):
        "refactor of ingest to unit test"
        postdict = OrderedDict()
        postdict[u'workflowDefinitionId'] = workflow or self.workflow
        if workflow_instance:
            postdict['workflowInstanceId'] = str(workflow_instance)
        if isinstance(workflow_parameters, basestring) and workflow_parameters != '':
            postdict.update(dict(item.split(":") for item in workflow_parameters.split(";")))
        elif isinstance(workflow_parameters, dict) and workflow_parameters:
            postdict.update(workflow_parameters)
        else:
            postdict.update(self.workflow_parameters)
        postdict[u'track'] = (pycurl.FORM_FILE, mp_file)
        return postdict

    def _get_endpoints(self, service_type):
        if self.logger:
            self.logger.debug('Looking up Opencast endpoint for %s', service_type)
        services = self.__call('GET', SERVICE_REGISTRY_ENDPOINT, {}, {'serviceType': service_type})
        services = json.loads(services)
        return services['services']['service']

    def _get_search_server(self):
        if not self.search_server:
            service = self._get_endpoints(SEARCH_SERVICE_TYPE)
            self.search_server = str(service['host'])
        return self.search_server

    def search_by_mp_id(self, mp_id):
        """ Returns search result from opencast """
        search_server = self._get_search_server()
        result = self.__call('GET', SEARCH_ENDPOINT, {}, {'id': mp_id}, {}, True, search_server, True)
        search_result = json.loads(result)
        return search_result['search-results']


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
        
        try:
            adminIP = socket.gethostbyname(adminHost);
            hostIP  = socket.gethostbyname(host)
            if (adminIP != hostIP):
                return True
            else:
                if adminHost != host:
                    self.logger and self.logger.debug("Shared IP address ({}) between {} and {}, it will be used {}".format(adminIP, adminHost, host, server['host']))
                    return True
        except Exception as exc:
            self.logger and self.logger.error("Problem on verifying the ingest server {} (on getting the IP of adminHost={} and host={}), exception {}".format(server['host'], adminHost, host, exc))
        return False


    def get_ingest_server(self):
        """ get the ingest server information from the admin node: 
        if there are more than one ingest servers the first from the list will be used
        as they are returned in order of their load, if there is only one returned this 
        will be the admin node, so we can use the information we already have """ 
        all_servers = self._get_endpoints(INGEST_SERVICE_TYPE)
        if type(all_servers) is list:
            for serv in all_servers:
                if self.verify_ingest_server(serv):
                    return str(serv['host']) # Returns less loaded served
        if self.verify_ingest_server(all_servers):
            return str(all_servers['host']) # There's only one server
        return None # it will use the admin server
 
    def ingest(self, mp_file, mp_id, workflow=None, workflow_instance=None, workflow_parameters=None):
        postdict = self._prepare_ingest(mp_file, workflow, workflow_instance, workflow_parameters)
        server = self.server if not self.multiple_ingest else self.get_ingest_server()
        if self.logger:
            self.logger.info( 'Ingesting MP {} to Server {}'.format(mp_id, server) ) 
        return self.__call('POST', INGEST_ENDPOINT, {}, {}, postdict.items(), False, server, False)


    def getseries(self, **query):
        """ Get series according to the page count and offset provided"""

        return self.__call('GET', SERIES_ENDPOINT, query_params = query)
        

    def get_workflows(self, server=None):
        """ Get workflow names """
        theServer = server or self.server
        validworkflows = ["schedule", "schedule-ng"]
        workflows = []

        if self.logger:
            self.logger.info( 'Getting workflow names for {}'.format(theServer) ) 

        # Get Workflow definitions
        definitions = self.__call('GET', WORKFLOWS_ENDPOINT)

        # Convert to JSON
        if definitions:
            definitions = json.loads(definitions)

            for d in definitions["definitions"]["definition"]:
                if d["tags"]:
                    if "tag" in d["tags"]:
                        if any(x in validworkflows for x in d["tags"]["tag"]):
                            workflows.append({"id"    : d["id"],
                                              "title" : d["title"]})
                    
        return workflows


    def find_between(self, s, first, last):
        try:
            start = s.index(first) + len(first)
            end = s.index(last, start)
            return s[start:end]
        except:
            return ""
