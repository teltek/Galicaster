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


import base64

from datetime import datetime

from icalendar import Calendar
from galicaster.mediapackage import mediapackage

def get_events_from_string_ical(ical_data):
    # See https://github.com/collective/icalendar#api-change
    f = getattr(Calendar, 'from_ical', getattr(Calendar, 'from_string', None))
    cal = f(ical_data)
    return cal.walk('vevent')


def get_events_from_file_ical(ical_file):
    # See https://github.com/collective/icalendar#api-change
    f = getattr(Calendar, 'from_ical', getattr(Calendar, 'from_string', None))
    cal = f(open(ical_file).read())
    return cal.walk('vevent')


def get_delete_events(old_events, new_events):
    out = list()
    for old_event in old_events:
        dtstart = old_event['DTSTART'].dt.replace(tzinfo=None)
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
            if (old_event['UID'] == new_event['UID'] and 
                old_event['DTSTART'].dt.replace(tzinfo=None) != new_event['DTSTART'].dt.replace(tzinfo=None)):
                out.append(old_event)
    return out


def create_mp(repo, event):
    if repo.has_key(event['UID']):
        mp = repo.get(event['UID'])
        if mp.status != mediapackage.SCHEDULED:
            return False
        rewrite = True
    else:
        mp = mediapackage.Mediapackage()
        mp.status = mediapackage.SCHEDULED
        mp.manual = False
        mp.setIdentifier(event['UID'])
        repo.add(mp)
        rewrite = False

    mp.setTitle(event['SUMMARY'])
    mp.setDate(event['DTSTART'].dt.replace(tzinfo=None))
    
    # ca_properties_name = 'org.opencastproject.capture.agent.properties'
    for attach_enc in event['ATTACH']:
        attach =  base64.b64decode(attach_enc)
        if attach_enc.params['X-APPLE-FILENAME'] == 'episode.xml':
            mp.addDublincoreAsString(attach, 'episode.xml', rewrite)
        elif attach_enc.params['X-APPLE-FILENAME'] == 'series.xml':
            mp.addSeriesDublincoreAsString(attach, 'series.xml', rewrite)
        else:
            mp.addAttachmentAsString(attach, attach_enc.params['X-APPLE-FILENAME'], 
                                     rewrite, attach_enc.params['X-APPLE-FILENAME'])
                         
    mp.marshalDublincore()
    repo.update(mp)






