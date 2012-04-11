# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/ical
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


"""
La libreria icalendar tiene un problema con los adjutnos de tipo:

ATTACH;FMTTYPE=application/xml;VALUE=BINARY;ENCODING=BASE64;X-APPLE-FILEN
 AME=episode.xml:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5k
...
ATTACH;FMTTYPE=application/text;VALUE=BINARY;ENCODING=BASE64;X-APPLE-FILE
 NAME=org.opencastproject.capture.agent.properties:I0NhcHR1cmUgQWdlbnQgc3

La clave de esta estrada es `ATTACH` para ambos y no se puede acceder a los
valores de FMTTYPE, VALUE=BINARY, ENCODING y X-APPLE-FILENAME. Se usa un workarround
para solucionar esto mirando el comienzo del adjunto (si empieza por `<?xml`) y si
tiene `dcterms:temporal` para dif entre serie y episode
"""

from os import path
import base64

import time
from datetime import datetime
from xml.dom import minidom

from icalendar import Calendar
from galicaster.mediapackage import mediapackage

def get_events_from_string_ical(ical_data):
    cal = Calendar.from_string(ical_data)
    return cal.walk('vevent')


def get_events_from_file_ical(ical_file):
    cal = Calendar.from_string(open(ical_file).read())
    return cal.walk('vevent')


def get_delete_events(old_events, new_events):
    out = list()
    for old_event in old_events:
        dtstart = datetime.strptime(str(old_event['DTSTART']), '%Y%m%dT%H%M%SZ')
        now = datetime.utcnow()
        #FIXME in python use filter
        not_e = True
        for new_event in new_events:
            if new_event['UID'] == old_event['UID']:
                not_e = False
        if not_e and dtstart > now:
            out.append(old_event)
    return out


def get_update_events(old_events, new_events):
    out = list()
    for old_event in old_events:
        for new_event in new_events:
            if old_event['UID'] == new_event['UID'] and str(old_event['DTSTART']) != str(new_event['DTSTART']):
                out.append(old_event)
    return out


def create_mp(repo, event):
    if repo.has_by_key(event['UID']):
        mp = repo.get(event['UID'])
        if mp.status != mediapackage.SCHEDULED:
            return False
        rewrite = True
    else:
        mp = repo.get_new_mediapackage(event['UID'], False)
        mp.status = mediapackage.SCHEDULED
        mp.manual = False
        mp.setIdentifier(event['UID'])
        repo.add(mp)
        rewrite = False

    mp.setTitle(event['SUMMARY'])
    mp.setDate(datetime.strptime(str(event['DTSTART']), '%Y%m%dT%H%M%SZ'))
    for attach_enc in event['ATTACH']:
        attach =  base64.b64decode(attach_enc)
        if attach[0:5] == '<?xml': #PARCHE para identificar attach
            if attach.find('dcterms:temporal') != -1:
                mp.addDublincoreAsString(attach, 'episode.xml', rewrite)
            else:
                mp.addSeriesDublincoreAsString(attach, 'series.xml', rewrite)
        else:           
            mp.addAttachmentAsString(attach, 'org.opencastproject.capture.agent.properties', rewrite, 'org.opencastproject.capture.agent.properties')
    mp.marshalDublincore()
    repo.update(mp)






