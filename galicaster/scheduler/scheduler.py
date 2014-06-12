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

import datetime
import gobject
from os import path
from threading import Timer, _Timer

from galicaster.utils import ical
from galicaster.mediapackage import mediapackage


class Scheduler(object):

    def __init__(self, repo, conf, disp, mhclient, logger, state):
        """
        Arguments:
        repo -- the galicaster mediapackage repository
        conf -- galicaster configuration
        disp -- the galicaster event-dispatcher to emit signals
        mhclient -- matterhorn HTTP client
        state -- galicaster state
        """
        self.ca_status = 'idle'

        self.conf       = conf
        self.repo       = repo
        self.dispatcher = disp
        self.client     = mhclient
        self.logger     = logger
        self.state      = state

        self.dispatcher.connect('galicaster-notify-timer-short', self.do_timers_short)
        self.dispatcher.connect('galicaster-notify-timer-long',  self.do_timers_long)

        self.t_stop = None

        self.start_timers = dict()
        self.mp_rec = None
        self.last_events = self.init_last_events()
        self.net = False


    def init_last_events(self):
        ical_path = self.repo.get_attach_path('calendar.ical')
        if path.isfile(ical_path):
            return ical.get_events_from_file_ical(ical_path)
        else:
            return list()


    def do_timers_short(self, sender):
        if self.net:
            self.set_state()
        else:
            self.init_client()


    def do_timers_long(self, sender):
        if self.net:
            self.proccess_ical()
            self.emit('after-process-ical')
        for mp in self.repo.get_next_mediapackages():
            self.create_new_timer(mp)

    
    def init_client(self):
        self.logger.info('Init matterhorn client')

        try:
            self.client.welcome()
        except:
            self.logger.warning('Unable to connect to matterhorn server')
            self.net = False
            self.emit('net-down')
        else:
            self.net = True
            self.emit('net-up')



    def set_state(self):
        if self.state.is_error:
            self.ca_status = 'unknown' #See AgentState.java
        elif self.state.is_recording:
            self.ca_status = 'capturing'
        else:
            self.ca_status = 'idle'
        self.logger.info('Set status %s to server', self.ca_status)
        try:
            self.client.setstate(self.ca_status)
            self.client.setconfiguration(self.conf.get_tracks_in_mh_dict()) 
            self.net = True
            self.emit('net-up')
        except:
            self.logger.warning('Problems to connect to matterhorn server ')
            self.net = False
            self.emit('net-down')
            return


    def proccess_ical(self):
        self.logger.info('Proccess ical')
        try:
            ical_data = self.client.ical()
        except:
            self.logger.warning('Problems to connect to matterhorn server ')
            self.net = False
            self.emit('net-down')
            return

        try:
            events = ical.get_events_from_string_ical(ical_data)
            delete_events = ical.get_delete_events(self.last_events, events)
            update_events = ical.get_update_events(self.last_events, events)
        except:
            self.logger.error('Error proccessing ical')
            return

        self.repo.save_attach('calendar.ical', ical_data)
        
        for event in events:
            self.logger.info('Creating MP with UID {0} from ical'.format(event['UID']))
            ical.create_mp(self.repo, event)
        
        for event in delete_events:
            self.logger.info('Deleting MP with UID {0} from ical'.format(event['UID']))
            mp = self.repo.get(event['UID'])
            if mp.status == mediapackage.SCHEDULED:
                self.repo.delete(mp)
            if self.start_timers.has_key(mp.getIdentifier()):
                self.start_timers[mp.getIdentifier()].cancel()
                del self.start_timers[mp.getIdentifier()]

        for event in update_events:
            self.logger.info('Updating MP with UID {0} from ical'.format(event['UID']))
            mp = self.repo.get(event['UID'])
            if self.start_timers.has_key(mp.getIdentifier()) and mp.status == mediapackage.SCHEDULED:
                self.start_timers[mp.getIdentifier()].cancel()
                del self.start_timers[mp.getIdentifier()]
                self.create_new_timer(mp)
                
        self.last_events = events


    def create_new_timer(self, mp):
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
            
            self.logger.info('Start record %s, duration %s ms', mp.getIdentifier(), mp.getDuration())

            self.t_stop = Timer(mp.getDuration()/1000, self.stop_record, [mp.getIdentifier()])
            self.t_stop.start()
            self.emit('start-record', mp.getIdentifier())

            try:
                self.client.setrecordingstate(key, 'capturing')
            except:
                self.logger.warning('Problems to connect to matterhorn server ')


        del self.start_timers[mp.getIdentifier()]


    def stop_record(self, key):
        self.ca_status = 'idle'
        self.mp_rec = None
        self.logger.info('Stop record %s', key)

        mp = self.repo.get(key)
        if mp.status == mediapackage.RECORDING:
            self.emit('stop-record', key)
            try:
                self.client.setrecordingstate(key, 'capture_finished')
            except:
                self.logger.warning('Problems to connect to matterhorn server ')
                self.net = False
                self.emit('net-down')
            
        self.t_stop = None


    def emit(self, *args, **kwargs):
        # self.dispatcher.emit(*args, **kwargs)
        #Allow only the main thread to touch the GUI
        gobject.idle_add(self.dispatcher.emit, *args, **kwargs)
        
