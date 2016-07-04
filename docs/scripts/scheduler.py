# -*- coding:utf-8 -*-
from pyhorn import MHClient, client
import datetime
import urllib
import time
import uuid
import base64
import optparse
import sys
import socket
import re

# UTILS
def convert_to_icalendar_format(date):
    return date.strftime("%Y%m%dT%H%M%SZ")

def convert_to_iso_format(date):
    return date.isoformat() + 'Z'

def convert_to_human_format(date):
    return date.strftime("%a %b %m %H:%M%S CEST %Y")

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

# PARSER
parser = optparse.OptionParser(usage="usage: %prog [options]",
                      version="%prog 1.0")
parser.add_option("-s", "--server",dest="server",default="http://localhost:8080",
                  help="Opencast server")
parser.add_option("-u", "--username",dest="username",default="opencast_system_account",
                  help="Opencast digest username")
parser.add_option("-p", "--password",dest="password",default="CHANGE_ME",
                  help="Opencast digest password")
parser.add_option("-c", "--captureagent",dest="ca",default='GCMobile-'+ socket.gethostname(),
                  help="Hostname to schedule recordings")
parser.add_option("-r", "--recordings",type= "int",dest="recordings",default="1",
                  help="Number of recordings",)
parser.add_option("-d", "--duration",type= "int",dest="duration",default="1",
                  help="Duration of each recording",)
parser.add_option("-l", "--lag",type= "int",dest="lag",default="1",
                  help="Lag or delay until first recording",)
parser.add_option("-o","--opencast", dest='opencastMode',help="Whether to send to opencast the calendar or save it locally", default=False)
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

post_template={
        'dublincore'    : '<dublincore xmlns="http://www.opencastproject.org/xsd/1.0/dublincore/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:oc="http://www.opencastproject.org/matterhorn/"><dcterms:title>{title}</dcterms:title><dcterms:creator>iCalendar Opencast</dcterms:creator><dcterms:contributor></dcterms:contributor><dcterms:isPartOf></dcterms:isPartOf><dcterms:subject></dcterms:subject><dcterms:abstract></dcterms:abstract><dcterms:available></dcterms:available><dcterms:coverage></dcterms:coverage><dcterms:created></dcterms:created><dcterms:date></dcterms:date><dcterms:extent></dcterms:extent><dcterms:format></dcterms:format><dcterms:isReferencedBy></dcterms:isReferencedBy><dcterms:isReplacedBy></dcterms:isReplacedBy><dcterms:publisher></dcterms:publisher><dcterms:relation></dcterms:relation><dcterms:replaces></dcterms:replaces><dcterms:rights></dcterms:rights><dcterms:rightsHolder></dcterms:rightsHolder><dcterms:source></dcterms:source><dcterms:type></dcterms:type><dcterms:license>Creative Commons 3.0: Attribution-NonCommercial-NoDerivs</dcterms:license><dcterms:language></dcterms:language><dcterms:description></dcterms:description><dcterms:rights></dcterms:rights><dcterms:identifier></dcterms:identifier><dcterms:temporal>start={start}; end={end}; scheme=W3C-DTF;</dcterms:temporal><dcterms:spatial>{ca}</dcterms:spatial><oc:agentTimeZone></oc:agentTimeZone></dublincore>',
        'agentparameters': ['org.opencastproject.workflow.definition=full',
                            'capture.device.names=defaults',
                            'org.opencastproject.workflow.config.trimHold=false',
                            'org.opencastproject.workflow.config.archiveOp=true',
                            'org.opencastproject.workflow.config.captionHold=false'],
        'wfproperties'   : ['trimHold=false',
                            'archiveOp=true',
                            'captionHold=false']
    }

calendar_template = """
BEGIN:VCALENDAR
PRODID:Opencast Matterhorn Calendar File 0.5
VERSION:2.0
CALSCALE:GREGORIAN
{events}
END:VCALENDAR
"""

event_template = """
BEGIN:VEVENT
DTSTAMP:{timestamp}
DTSTART:{start}
DTEND:{end}
SUMMARY:{title}
UID:{uuid}
ORGANIZER;CN=b:mailto:b@matterhorn.opencast
LOCATION:{ca}
{episode}

{opencast_prop}

END:VEVENT
"""

episode_template = """<?xml version="1.0" encoding="UTF-8"?><dublincore xmlns="http://www.opencastproject.org/xsd/1.0/dublincore/" xmlns:dcterms="http://purl.org/dc/terms/"><dcterms:creator>{creator}</dcterms:creator><dcterms:license>Creative Commons 3.0: Attribution-NonCommercial-NoDerivs</dcterms:license><dcterms:temporal>start={start}; end={end}; scheme=W3C-DTF;</dcterms:temporal><dcterms:title>{title}</dcterms:title><dcterms:spatial>{ca}</dcterms:spatial><dcterms:identifier>{uuid}</dcterms:identifier></dublincore>"""

opencast_prop_template = """#Capture Agent specific data
#{date}
['org.opencastproject.workflow.definition=full', 'capture.device.names\=defaults', 'org.opencastproject.workflow.config.trimHold\=false', 'org.opencastproject.workflow.config.archiveOp\=true', 'org.opencastproject.workflow.config.captionHold\=false']
event.title={title}
event.location={ca}
"""

now = datetime.datetime.utcnow().replace(microsecond=0)
end_date = None
events = ""
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
        start_date = now + datetime.timedelta(minutes=options.lag)
        
    start = start_date.isoformat() + 'Z'
    end_date = start_date + duration
    end = end_date.isoformat() + 'Z'

    print "  Start: {}".format(start)
    print "  End: {}".format(end)
    
    if options.opencastMode:
        print "  Doing POST request..."

        extra_headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

        dictionary = {'title': title,
                      'start': start,
                      'end': end,
                      'ca': options.ca
        }

        post_data = post_template.copy()
        post_data['dublincore'] = post_data['dublincore'].format(**dictionary)
        response = cli.post("recordings/", data=urllib.urlencode(post_data), extra_headers=extra_headers)
        print response



    else:
        print "  Creating calendar event locally..."
        new_uuid = '-'.join(unicode(uuid.uuid4()).split('-')[-2:])
        episode = episode_template.format(**{
            'creator': 'iCalendar auto-generated',
            'start': convert_to_iso_format(start_date),
            'end': convert_to_iso_format(end_date),
            'title': title,
            'ca': options.ca,
            'uuid': new_uuid
            
        })
        
        opencast_prop = opencast_prop_template.format(**{
            'date': convert_to_human_format(now),
            'title': title.replace(":", "\:"),
            'ca' : options.ca
        })

        part_a = 'ATTACH;FMTTYPE=application/xml;VALUE=BINARY;ENCODING=BASE64;X-APPLE-FILEN\n '
        part_b = 'AME=episode.xml:' + base64.b64encode(episode)
        formatted_partb = re.sub("(.{72})", "\\1\n ", part_b, 0, re.DOTALL)
        whole_episode = part_a + formatted_partb
        
        part_a = 'ATTACH;FMTTYPE=application/text;VALUE=BINARY;ENCODING=BASE64;X-APPLE-FILE\n '
        part_b = 'NAME=org.opencastproject.capture.agent.properties:' + base64.b64encode(opencast_prop)
        formatted_opencast_prop = re.sub("(.{72})", "\\1\n ", part_b, 0, re.DOTALL)
        whole_opencast_prop = part_a + formatted_opencast_prop
        
        event = event_template.format(**{
            'timestamp': convert_to_icalendar_format(now),
            'start': convert_to_icalendar_format(start_date),
            'end': convert_to_icalendar_format(end_date),
            'title': title,
            'uuid': new_uuid,
            'ca': options.ca,
            'episode' : whole_episode,
            'opencast_prop': whole_opencast_prop
        })

        events = events + '\n' + event

if not options.opencastMode:
    filename = 'calendar.ical'
    calendar = calendar_template.format(**{'events': events})
    f = open(filename,'w')
    f.write(calendar)
    f.close()
    print "Saved to {}".format(filename)

