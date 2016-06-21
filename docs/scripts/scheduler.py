# -*- coding:utf-8 -*-
from pyhorn import MHClient, client
import random
import string
import datetime
import urllib
import time

client._session.verify = False

url = 'http://localhost:8080'
username = 'opencast_system_account';
password = 'CHANGE_ME';

# CONFIG PARAMS
ca = "GCMobile"
time_until_rec = datetime.timedelta(minutes=1) 
duration = datetime.timedelta(seconds=90)

cli = MHClient(url, username, password)

data3={
        'dublincore'    : '<dublincore xmlns="http://www.opencastproject.org/xsd/1.0/dublincore/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:oc="http://www.opencastproject.org/matterhorn/"><dcterms:title>{}</dcterms:title><dcterms:creator>b</dcterms:creator><dcterms:contributor></dcterms:contributor><dcterms:isPartOf></dcterms:isPartOf><dcterms:subject></dcterms:subject><dcterms:abstract></dcterms:abstract><dcterms:available></dcterms:available><dcterms:coverage></dcterms:coverage><dcterms:created></dcterms:created><dcterms:date></dcterms:date><dcterms:extent></dcterms:extent><dcterms:format></dcterms:format><dcterms:isReferencedBy></dcterms:isReferencedBy><dcterms:isReplacedBy></dcterms:isReplacedBy><dcterms:publisher></dcterms:publisher><dcterms:relation></dcterms:relation><dcterms:replaces></dcterms:replaces><dcterms:rights></dcterms:rights><dcterms:rightsHolder></dcterms:rightsHolder><dcterms:source></dcterms:source><dcterms:type></dcterms:type><dcterms:license>Creative Commons 3.0: Attribution-NonCommercial-NoDerivs</dcterms:license><dcterms:language></dcterms:language><dcterms:description></dcterms:description><dcterms:rights></dcterms:rights><dcterms:identifier></dcterms:identifier><dcterms:temporal>start={}; end={}; scheme=W3C-DTF;</dcterms:temporal><dcterms:spatial>{}</dcterms:spatial><oc:agentTimeZone></oc:agentTimeZone></dublincore>',
        'agentparameters': ['org.opencastproject.workflow.definition=full',
                            'capture.device.names=defaults',
                            'org.opencastproject.workflow.config.trimHold=false',
                            'org.opencastproject.workflow.config.archiveOp=true',
                            'org.opencastproject.workflow.config.captionHold=false'],
        'wfproperties'   : ['trimHold=false',
                            'archiveOp=true',
                            'captionHold=false']
    }

print "creating random title..."
random_string = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(3))
title = 'test' + random_string
print title

extra_headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

print "creating start and end time..."
now = datetime.datetime.utcnow().replace(microsecond=0)
start = (now + time_until_rec).isoformat() + 'Z'
print "Start: {}".format(start)
end = (now + duration).isoformat() + 'Z'
print "End: {}".format(end)

data3['dublincore'] = data3['dublincore'].format(title,start,end,ca)

print "Doing POST request..."
response = cli.post("recordings/", data=urllib.urlencode(data3), extra_headers=extra_headers)
print response
