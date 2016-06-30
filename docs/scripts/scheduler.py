# -*- coding:utf-8 -*-
from pyhorn import MHClient, client
import datetime
import urllib
import time
import optparse
import sys
import socket

parser = optparse.OptionParser(usage="usage: %prog [options]",
                      version="%prog 1.0")
parser.add_option("-s", "--server",
                  dest="server",
                  default="http://localhost:8080",
                  help="Opencast server")
parser.add_option("-u", "--username",
                  dest="username",
                  default="opencast_system_account",
                  help="Opencast digest username")
parser.add_option("-p", "--password",
                  dest="password",
                  default="CHANGE_ME",
                  help="Opencast digest password")
parser.add_option("-c", "--captureagent",
                  dest="ca",
                  default='GCMobile-'+ socket.gethostname(),
                  help="Hostname to schedule recordings")
parser.add_option("-r", "--recordings",
                  type= "int",
                  dest="recordings",
                  default="1",
                  help="Number of recordings",)
parser.add_option("-d", "--duration",
                  type= "int",
                  dest="duration",
                  default="1",
                  help="Duration of each recording",)
parser.add_option("-l", "--lag",
                  type= "int",
                  dest="lag",
                  default="1",
                  help="Lag or delay until first recording",)
(options, args) = parser.parse_args()

print "=========== CURRENT CONFIG ==========="
print " Server:          ", options.server
print " Username:        ", options.username
print " Password:        ", options.password
print " Capture agent:   ", options.ca
print " Num recordings:  ", options.recordings
print " Duration (min):  ", options.duration
print " Lag (min):       ", options.lag
print "======================================\n"

client._session.verify = False
cli = MHClient(options.server, options.username, options.password)

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

now = datetime.datetime.utcnow().replace(microsecond=0)
end_date = None
for x in range(0, options.recordings):
    # TITLE
    print "Creating a new recording"
    tag = (datetime.datetime.now().replace(microsecond=0).isoformat() + 'Z') + ' - Recording: {}'.format(x)
    title = 'test - ' + tag
    print "  Title:", title

    duration = datetime.timedelta(minutes=options.duration)
    if end_date:
        start_date = end_date + datetime.timedelta(minutes=options.lag)
    else:
        start_date = now + datetime.timedelta(options.lag)
        
    end_date = start_date + duration
    start = start_date.isoformat() + 'Z'
    end = end_date.isoformat() + 'Z'
    print "  Start: {}".format(start)
    print "  End: {}".format(end)
    
    print "  Doing POST request..."
    extra_headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
    data3['dublincore'] = data3['dublincore'].format(title,start,end,options.ca)
    response = cli.post("recordings/", data=urllib.urlencode(data3), extra_headers=extra_headers)
    print response
