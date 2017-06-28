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

count = 0

def get_events_from_string_ical(ical_data, limit=0):
    global count
    # See https://github.com/collective/icalendar#api-change
    f = getattr(Calendar, 'from_ical', getattr(Calendar, 'from_string', None))
    cal = f(ical_data)
    if limit > 0:
        events = cal.walk('vevent')[count:limit+count]
        for event in events:
            if event['DTEND'].dt.replace(tzinfo=None) < datetime.utcnow():
                count += 1
        if count > 0:
            events = cal.walk('vevent')[count:limit+count]
    else:
        events = cal.walk('vevent')
    return events


def get_events_from_file_ical(ical_file, limit=0):
    ical_data = open(ical_file).read()
    return get_events_from_string_ical(ical_data, limit)


def get_deleted_events(old_events, new_events):
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


def get_updated_events(old_events, new_events):
    out = list()
    for old_event in old_events:
        for new_event in new_events:
            append = False
            if old_event['UID'] == new_event['UID']:
                append = is_event_changed(new_event, old_event)
                for attach_enc in new_event['ATTACH']:
                    attach =  base64.b64decode(attach_enc)
                    if not attach_enc.params['X-APPLE-FILENAME'] == 'episode.xml' and not attach_enc.params['X-APPLE-FILENAME'] == 'series.xml':
                        break
                for attach_enc in old_event['ATTACH']:
                    attach1 =  base64.b64decode(attach_enc)
                    if not attach_enc.params['X-APPLE-FILENAME'] == 'episode.xml' and not attach_enc.params['X-APPLE-FILENAME'] == 'series.xml':
                        break

                attach_split = attach.split("\n",2)
                attach = attach_split[0] + attach_split[2]

                attach_split = attach1.split("\n",2)
                attach1 = attach_split[0] + attach_split[2]

                if attach != attach1:
                    append = True

                if append:
                    out.append(new_event)
    return out

def is_event_changed(new_event, old_event):
    if (old_event['DTSTART'].dt.replace(tzinfo=None) != new_event['DTSTART'].dt.replace(tzinfo=None) or
        old_event['DTEND'].dt.replace(tzinfo=None) != new_event['DTEND'].dt.replace(tzinfo=None) or
        old_event['SUMMARY'] != new_event['SUMMARY']):
        append = True
    elif 'RELATED-TO' in new_event and not 'RELATED-TO' in old_event or not 'RELATED-TO' in new_event and 'RELATED-TO' in old_event:
        append = True
    elif 'RELATED-TO' in new_event and 'RELATED-TO' in old_event and old_event['RELATED-TO'] != new_event['RELATED-TO']:
        append = True
    elif 'ORGANIZER' in new_event and not 'ORGANIZER' in old_event or not 'ORGANIZER' in new_event and 'ORGANIZER' in old_event:
        append = True
    elif 'ORGANIZER' in new_event and 'ORGANIZER' in old_event and old_event['ORGANIZER'] != new_event['ORGANIZER']:
        append = True
    else:
        append = False

    return append



def create_mp(repo, event):
    if repo.has_key(event['UID']):
        mp = repo.get(event['UID'])
        if mp.status != mediapackage.SCHEDULED:
            return False
    else:
        mp = mediapackage.Mediapackage()
        mp.status = mediapackage.SCHEDULED
        mp.manual = False
        mp.setIdentifier(event['UID'])
        repo.add(mp)


    mp.setTitle(event['SUMMARY'])
    mp.setDate(event['DTSTART'].dt.replace(tzinfo=None))

    catalog= mp.getCatalogs("dublincore/series")
    if catalog:
        mp.remove(catalog[0])

    if 'identifier' in mp.metadata_series:
        mp.metadata_series["identifier"] = None
        mp.metadata_series['title'] = None
    if "isPartOf" in mp.metadata_episode:
        del mp.metadata_episode['isPartOf']
    if 'creator' in mp.metadata_episode:
        mp.metadata_episode['creator'] = None



    # ca_properties_name = 'org.opencastproject.capture.agent.properties'
    for attach_enc in event['ATTACH']:
        attach =  base64.b64decode(attach_enc)
        if attach_enc.params['X-APPLE-FILENAME'] == 'episode.xml':
            mp.addDublincoreAsString(attach, 'episode.xml')
        elif attach_enc.params['X-APPLE-FILENAME'] == 'series.xml':
            mp.addSeriesDublincoreAsString(attach, 'series.xml')
        else:
            mp.addAttachmentAsString(attach, attach_enc.params['X-APPLE-FILENAME'],
                                     attach_enc.params['X-APPLE-FILENAME'])
    mp.marshalDublincore()
    repo.update(mp)


def handle_ical(ical_data, last_events, repo, scheduler, logger):
    if ical_data:


        try:
            events = get_events_from_string_ical(ical_data, limit=100)
            if last_events:
                delete_events = get_deleted_events(last_events, events)
                update_events = get_updated_events(last_events, events)
        except Exception as exc:
            logger and logger.error('Error processing ical: {0}'.format(exc))
            return

        for event in events:
            if not repo.get(event['UID']):
                logger and logger.info('Creating MP with UID {0} from ical'.format(event['UID']))
                create_mp(repo, event)

        if last_events:
            for event in delete_events:
                logger and logger.info('Deleting MP with UID {0} from ical'.format(event['UID']))
                mp = repo.get(event['UID'])
                if mp and mp.status == mediapackage.SCHEDULED:
                    repo.delete(mp)
                scheduler.remove_timer(mp)

            for event in update_events:
                logger and logger.info('Updating MP with UID {0} from ical'.format(event['UID']))
                create_mp(repo, event)
                mp = repo.get(event['UID'])
                scheduler.update_timer(mp)

        for mp in repo.get_next_mediapackages(5):
            scheduler.create_timer(mp)

        return events
