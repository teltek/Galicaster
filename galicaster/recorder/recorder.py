# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/recorder
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

import logging

import gtk
import gst
import os
import sys

from galicaster.core import context

log = logging.getLogger()


class Recorder(object):

    def __init__(self, bins, players={}):
        """
        Initialize the recorder.
        This class is event-based and needs a mainloop to work properly.

        :param bins: a ``list`` of ``dict`` with name, klass, device and file to record
        :param players: a ``dict`` a gtk.DrawingArea list to use as player.
        """
        #FIXME check the values are dict with the next keys: name, klass/type, dev* and filesink.
        if not isinstance(bins, list):
            raise TypeError(
                '%s: need a %r; got a %r: %r' % ('bins', list,
                                                 type(bins), bins) 
                )
        #FIXME check the values are gtk.DrawingArea
        if not isinstance(players, dict):
            raise TypeError(
                '%s: need a %r; got a %r: %r' % ('players', dict, 
                                                 type(players), players)
                )

        self.dispatcher = context.get_dispatcher() 
        self.bins_desc = bins
        self.players = players
        self.restart = False
        self.mute = False
        self.error = False

        self.pipeline_name = "galicaster_recorder"  
        self.pipeline = gst.Pipeline(self.pipeline_name)
        self.bus = self.pipeline.get_bus()
        
        self.bins = dict()
        self.callback = None

        self.bus.add_signal_watch()
        self.bus.enable_sync_message_emission()
        #self.bus.connect('message', self.__debug) # TO DEBUG
        self.bus.connect('message::eos', self.__on_eos)
        self.bus.connect('message::error', self.__on_error)        
        self.bus.connect('message::element', self.__on_message_element)
        self.bus.connect('message::state-changed', self.__on_state_changed)
        self.bus.connect('sync-message::element', self.__on_sync_message)

        for bin in bins:
            self.init_bin (bin)
            
            
    def init_bin(self, bin):
        
        log.info("gst init"+ str(bin))
        name = bin['name']

        try:
            mod_name = 'galicaster.recorder.pipeline.' + bin['device']
            __import__(mod_name)
            mod = sys.modules[mod_name]
            Klass = getattr(mod, "GC" + bin['device'])
        except:
            raise NameError(
                'Invalid track type %s for %s track' % (mod_name, name)
                )

        log.debug("Init bin %s %s", name, mod_name)
        self.bins[name] = Klass(bin)
        self.pipeline.add(self.bins[name])

    def get_status(self):
        return self.pipeline.get_state()

    def get_clock(self):
        return self.pipeline.get_clock()

    def preview(self):
        log.debug("recorder preview")
        if not len(self.bins):
            self.dispatcher.emit("recorder-error","No tracks on profile")
            return False
        else:
            change=self.pipeline.set_state(gst.STATE_PAUSED)
            
            if change == gst.STATE_CHANGE_FAILURE:
                text = None
                random_bin = None
                for key,value in self.bins.iteritems():
                    if not value.getSource():
                        random_bin = value
                        text = "Error on track : "+ key
                    if not random_bin:
                        random_bin = value
                        text = "Error on unknow track"

                src = random_bin
                error = gst.GError(gst.RESOURCE_ERROR,
                                   gst.RESOURCE_ERROR_FAILED, text)
                log.error("recorder bin error "+ str(error) )
                message = gst.message_new_error(
                    src, error, 
                    str(random_bin)+"\nunknown system_error")
                self.bus.post(message)
                #self.dispatcher.emit("recorder-error","Driver error")
                return False
            else:          
                return True

    def stop_preview(self):
        #FIXME send EOS
        self.pipeline.set_state(gst.STATE_NULL)
        self.pipeline.get_state()
        return None

    def record(self):
        if self.pipeline.get_state()[1] == gst.STATE_PLAYING:
            for bin_name, bin in self.bins.iteritems():
                valve = bin.changeValve(False)
            # Get clock

    def stop_record(self):                
        a = gst.structure_from_string('letpass')
        event = gst.event_new_custom(gst.EVENT_EOS, a)
        for bin_name, bin in self.bins.iteritems():
            resultado = bin.send_event_to_src(event)
            #if resultado: 
            #    print "EOS sended to src of: " + bin_name
        return True

    def stop_record_and_restart_preview(self):
        log.debug("Stopping Recording and Restarting Preview")
        a = gst.structure_from_string('letpass')
        event = gst.event_new_custom(gst.EVENT_EOS, a)
        for bin_name, bin in self.bins.iteritems():
            resultado = bin.send_event_to_src(event)
            #if resultado: 
            #    print "EOS sended to src of: " + bin_name
        self.restart = True  # FIXME send user_data on the EOS to force restart
        if self.pipeline.get_state()[1] == gst.STATE_PAUSED: 
            # If paused ensure sending EOS
            self.pipeline.set_state(gst.STATE_PLAYING)
        return True

    def just_restart_preview(self):
        log.debug("Stopping Preview and Restarting")
        self.stop_preview()
        log.debug("EMITTING restart preview")
        self.dispatcher.emit("restart-preview")
        return True

    def pause(self):
        log.debug("recorder paused")
        self.pipeline.set_state(gst.STATE_PAUSED)
        self.pipeline.get_state()
        return True

    def resume(self):
        log.debug("resume paused")
        self.pipeline.set_state(gst.STATE_PLAYING)
        self.pipeline.get_state()
        return None

    def __debug(self, bus, msg):       
        if msg.type != gst.MESSAGE_ELEMENT or msg.structure.get_name() != 'level':
            print "DEBUG ", msg

    def __on_eos(self, bus, msg):
        log.info('eos')
        self.stop_preview()  # FIXME pipeline set to NULL twice (bf and in the function)

        if self.restart:
            self.restart = False
            log.debug("EMITTING restart preview")
            self.dispatcher.emit("restart-preview")

    def __on_error(self, bus, msg):
        error, debug = msg.parse_error()
        error_info = "%s (%s)" % (error, debug)
        log.error(error_info)
        if not debug.count('canguro'):
            self.stop_elements()
            gtk.gdk.threads_enter()
            self.error = error_info
            self.dispatcher.emit("recorder-error", error_info)
            gtk.gdk.threads_leave()
            # return True
    
    def stop_elements(self):        
        iterator = self.pipeline.elements()
        while True:
            try:                
                element = iterator.next()
                element.set_state(gst.STATE_NULL)
                state = element.get_state()
            except StopIteration:
                break           
        self.pipeline.set_state(gst.STATE_NULL)
        self.pipeline.get_state()
        #return True

    def __on_state_changed(self, bus, message):
        old, new, pending = message.parse_state_changed()
        if (isinstance(message.src, gst.Pipeline) and 
            (old, new) == (gst.STATE_READY, gst.STATE_PAUSED) ):
            for bin_name, bin in self.bins.iteritems():
                valve = bin.changeValve(True) 
            self.pipeline.set_state(gst.STATE_PLAYING)

    def __on_sync_message(self, bus, message):
        if message.structure is None:
            return
        if message.structure.get_name() == 'prepare-xwindow-id':
            name = message.src.get_property('name')[5:]
            log.debug("on sync message 'prepare-xwindow-id' %r", name)

            try:
                gtk_player = self.players[name]
                if not isinstance(gtk_player, gtk.DrawingArea):
                    raise TypeError()
                gtk.gdk.threads_enter()
                gtk.gdk.display_get_default().sync()            
                message.src.set_property('force-aspect-ratio', True)
                message.src.set_xwindow_id(gtk_player.window.xid)
                gtk.gdk.threads_leave()

            except KeyError:
                pass
            except TypeError:
                log.error('players[%r]: need a %r; got a %r: %r' % (
                        name, gtk.DrawingArea, type(gtk_player), gtk_player))
        
    def __on_message_element(self, bus, message):
        if message.structure.get_name() == 'level':
            self.__set_vumeter(message)

    def __set_vumeter(self, message):
        struct = message.structure
        if  struct['rms'][0] == float("-inf"):
            valor = "Inf"
        else:            
            valor = struct['rms'][0]
        self.dispatcher.emit("update-rec-vumeter", valor)


    def is_pausable(self):
        return all(bin.is_pausable for bin in self.bins.values())


    def mute_preview(self, value):
        for bin_name, bin in self.bins.iteritems():
            if bin.has_audio:
                bin.mute_preview(value)
