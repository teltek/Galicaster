# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/scheduler/scheduler
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import logging

import datetime
import tempfile
from threading import Timer
from threading import _Timer

from galicaster.core import context
from galicaster.utils.mhhttpclient import MHHTTPClient
from galicaster.utils import ical
from galicaster.mediapackage import mediapackage

log = logging.getLogger()

class Scheduler():

    #FIXME set timer on Conf
    INTERVAL_INIT_CLIENT = 30
    INTERVAL_PUSH_STATE = 5
    INTERVAL_POLL_ICAL = 10

    def __init__(self):
        """
        """
        self.ca_status = 'idle'

        self.conf = context.get_conf()
        self.repo = context.get_repository() 
        self.worker = context.get_worker()
        self.dispatcher = context.get_dispatcher() 
        self.dispatcher.connect("galicaster-notify-quit", self.do_stop_timers)
        self.__init_client()
        self.t_stop = None

        self.start_timers = dict()
        self.stop_timers = False
        self.mp_rec = None
        #FIXME init last_events with ical from repo.attach
        self.last_events = list()

    
    def __init_client(self):
        log.info('Init matterhorn client')
        server = self.conf.get_section('ingest')

        self.t_state = None
        self.t_ical = None
        self.t_client = None
        self.t_ingest = None

        self.client = context.get_mhclient()

        try:
            self.client.welcome()
        except:
            log.warning('Unable to connect to matterhorn server')
            self.t_client = Timer(self.INTERVAL_INIT_CLIENT, self.__init_client) 
            self.t_client.start()
        else:
            self.__init_timers()
            self.dispatcher.emit("net-up")

    def __init_timers(self):
        self.t_state = Timer(2, self.set_state) 
        self.t_state.start()
        self.t_ical = Timer(2, self.proccess_ical)
        self.t_ical.start()
        self.t_ingest = Timer(self.__get_sec_until_tomorrow(), self.ingest)
        self.t_ingest.start()
        self.t_client = None
        self.t_stop = None


    def __stop_timers(self):
        log.debug('stop timers')
        self.dispatcher.emit("net-down")
        timers = [self.t_state, self.t_ical, self.t_ingest]
        for ti in timers:
            if isinstance(ti, _Timer):
                ti.cancel()
        self.__init_client()


    def set_state(self):
        log.info('Set status %s to server', self.ca_status)
        #log.info('Hostname %s %s', socket.gethostname(), socket.gethostbyname(socket.gethostname()))
        try:
            res = self.client.setstate(self.ca_status)
            res = self.client.setconfiguration(self.conf.get_tracks_in_mh_dict()) 
            self.dispatcher.emit("net-up")
        except:
            log.warning('Problems to connect to matterhorn server ')
            self. __stop_timers()
            return

        if not self.stop_timers:
            self.t_state = Timer(self.INTERVAL_PUSH_STATE, self.set_state)
            self.t_state.start()


    def proccess_ical(self):
        log.info('Proccess ical')

        try:
            ical_data = self.client.ical()
        except:
            log.warning('Problems to connect to matterhorn server ')
            self. __stop_timers()
            return

        try:
            events = ical.get_events_from_string_ical(ical_data)
            delete_events = ical.get_delete_events(self.last_events, events)
            update_events = ical.get_update_events(self.last_events, events)
        except:
            log.error('Error proccessing ical')
            return

        self.repo.save_attach('calendar.ical', ical_data)
        
        for event in events:
            ical.create_mp(self.repo, event)
        
        for event in delete_events:
            mp = self.repo.get(event['UID'])
            if mp.status == mediapackage.SCHEDULED:
                self.repo.delete(mp)
            if self.start_timers.has_key(mp.getIdentifier()):
                self.start_timers[mp.getIdentifier()].cancel()
                del self.start_timers[mp.getIdentifier()]

        for event in update_events:
            mp = self.repo.get(event['UID'])
            if self.start_timers.has_key(mp.getIdentifier()) and mp.status == mediapackage.SCHEDULED:
                self.start_timers[mp.getIdentifier()].cancel()
                del self.start_timers[mp.getIdentifier()]
                self.__create_new_timer(mp)                

        for mp in self.repo.get_next_mediapackages():
            self.__create_new_timer(mp)
                
        self.last_events = events
        if not self.stop_timers:
            self.t_ical = Timer(self.INTERVAL_POLL_ICAL, self.proccess_ical)
            self.t_ical.start()


    def __create_new_timer(self, mp):
        diff = (mp.getDate() - datetime.datetime.utcnow())
        if diff < datetime.timedelta(minutes=30) and mp.getIdentifier() != self.mp_rec and not self.start_timers.has_key(mp.getIdentifier()): 
            ti = Timer(diff.seconds, self.start_record, [mp.getIdentifier()]) 
            self.start_timers[mp.getIdentifier()] = ti
            ti.start()


    def start_record(self, key):
        mp = self.repo.get(key) # FIXME what if the mp doesnt exist?
        if mp.status == mediapackage.SCHEDULED:
            
            self.ca_status = 'capturing'
            self.mp_rec = key
            
            mp = self.repo.get(key)      
            
            log.info('Start record %s, duration %s ms', mp.getIdentifier(), mp.getDuration())

            self.t_stop = Timer(mp.getDuration()/1000, self.stop_record, [mp.getIdentifier()])
            self.t_stop.start()
            self.dispatcher.emit("start-record", mp.getIdentifier())
            try:
                res = self.client.setrecordingstate(key, "capturing")
            except:
                log.warning('Problems to connect to matterhorn server ')
                self. __stop_timers()

        del self.start_timers[mp.getIdentifier()]


    def stop_record(self, key):
        self.ca_status = 'idle'
        self.mp_rec = None
        log.info('Stop record %s', key)

        mp = self.repo.get(key)
        if mp.status == mediapackage.RECORDING:
            self.dispatcher.emit("stop-record", key)
            try:
                res = self.client.setrecordingstate(key, "capture_finished")
            except:
                log.warning('Problems to connect to matterhorn server ')
                self. __stop_timers()
            
        self.t_stop = None


    def __get_sec_until_tomorrow(self):
        now = datetime.datetime.utcnow()
        tomorrow = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1)
        #tomorrow = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute) + datetime.timedelta(minutes=1)
        diff = tomorrow - now
        return diff.seconds


    def ingest(self):
        mps = self.repo.list_by_status(mediapackage.PENDING)
        for mp in mps:
            self.worker.ingest(mp)

        if not self.stop_timers:
            self.t_ingest = Timer(self.__get_sec_until_tomorrow(), self.ingest)
            self.t_ingest.start()


    def clean(self):
        pass


    def do_stop_timers(self, sender=None):
        self.stop_timers = True

        timers = [self.t_client, self.t_state, self.t_ical, self.t_stop, self.t_ingest]
        for ti in timers:
            if isinstance(ti, _Timer):
                ti.cancel()
        for ti in self.start_timers.values():
            if isinstance(ti, _Timer):
                ti.cancel()



