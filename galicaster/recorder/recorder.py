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

import gtk
import gst
import sys

from galicaster.core import context
from galicaster.utils.gstreamer import WeakMethod

logger = context.get_logger()


class Recorder(object):

    def __init__(self, bins, players={}):
        """
        Initialize the recorder.
        This class is event-based and needs a mainloop to work properly.

        :param bins: ``list`` of ``dict`` with bin name, device, path, and optional parameters.
        :param players: (optional) ```gtk.DrawingArea``` ```list``` to use as player.
        """
        if not isinstance(bins, list) or len(bins) == 0:
            raise TypeError(
                '{}: need a {}; got a {}: {}'.format('bins', list,
                                                     type(bins), bins))

        if not isinstance(players, dict):
            raise TypeError(
                '{}: need a {}; got a {}: {}'.format('players', dict,
                                                     type(players), players))

        self.dispatcher = context.get_dispatcher() 
        self.players = players
        self.restart = False
        self.mute = False
        self.error = False
        self.is_recording = False
        self.__start_record_time = 0
        self.__duration = 0

        self.pipeline = gst.Pipeline("galicaster_recorder")
        self.bus = self.pipeline.get_bus()

        self.bins = dict()
        self.callback = None

        self.bus.add_signal_watch()
        self.bus.enable_sync_message_emission()
        #self.bus.connect('message', WeakMethod(self, '_debug')) # TO DEBUG
        self.bus.connect('message::error', WeakMethod(self, '_on_error'))        
        self.bus.connect('message::element', WeakMethod(self, '_on_message_element'))
        self.bus.connect('sync-message::element', WeakMethod(self, '_on_sync_message'))

        for bin in bins:
            name = bin['name']

            try:
                mod_name = 'galicaster.recorder.bins.' + bin['device']
                __import__(mod_name)
                mod = sys.modules[mod_name]
                Klass = getattr(mod, "GC" + bin['device'])
            except:
                message = 'Invalid track type "{}" for "{}" track'.format(bin.get('device'), name)
                logger.error(message)
                raise NameError(message)

            logger.debug("Init bin {} {}".format(name, mod_name))
            self.bins[name] = Klass(bin)
            self.pipeline.add(self.bins[name])


    def get_status(self):
        return self.pipeline.get_state()


    def get_time(self):
        return self.pipeline.get_clock().get_time()


    def get_recorded_time(self):
        if self.pipeline.get_state()[1] == gst.STATE_NULL:
            return self.__duration
        return self.__query_position() - self.__start_record_time


    def __query_position(self):
        try:
            duration = self.pipeline.query_position(gst.FORMAT_TIME)[0]
        except:
            duration = 0
        return duration


    def preview(self):
        logger.debug("recorder preview")
        self.__start(gst.STATE_PAUSED)
        for bin in self.bins.values():
            bin.changeValve(True) 
        self.__start(gst.STATE_PLAYING)


    def preview_and_record(self):
        logger.debug("recorder preview and record")
        self.__start(gst.STATE_PLAYING)
        self.__start_record_time = self.__query_position() #TODO
        self.is_recording = True


    def __start(self, new_state=gst.STATE_PAUSED):
        change = self.pipeline.set_state(new_state)
            
        if change == gst.STATE_CHANGE_FAILURE:
            text = None
            random_bin = None
            for key, value in self.bins.iteritems():
                if not value.getSource():
                    random_bin = value
                    text = "Error on track : "+ key
                if not random_bin:
                    random_bin = value
                    text = "Error on unknow track"

            src = random_bin
            error = gst.GError(gst.RESOURCE_ERROR, gst.RESOURCE_ERROR_FAILED, text)
                
            message = gst.message_new_error(
                src, error, 
                str(random_bin)+"\nunknown system_error")
            self.bus.post(message)
            #self.dispatcher.emit("recorder-error","Driver error")
            return False
        while True:
            message = self.bus.timed_pop_filtered(gst.CLOCK_TIME_NONE, gst.MESSAGE_STATE_CHANGED)
            old, new, pending = message.parse_state_changed()
            if (message.src == self.pipeline and new == new_state):
                break
        return True


    def record(self):
        if self.pipeline.get_state()[1] == gst.STATE_PLAYING:
            for bin in self.bins.values():
                bin.changeValve(False)
        self.__start_record_time = self.__query_position()
        self.is_recording = True


    def pause(self):
        logger.debug("recorder paused")
        self.pipeline.set_state(gst.STATE_PAUSED)
        self.pipeline.get_state()
        return True


    def resume(self):
        logger.debug("resume paused")
        self.pipeline.set_state(gst.STATE_PLAYING)
        self.pipeline.get_state()
        return None


    def stop(self):
        if self.is_recording:
            self.is_recording == False
            self.__duration = self.__query_position() - self.__start_record_time
            a = gst.structure_from_string('letpass')
            event = gst.event_new_custom(gst.EVENT_EOS, a)
            for bin_name, bin in self.bins.iteritems():
                bin.send_event_to_src(event)
            self.bus.timed_pop_filtered(gst.CLOCK_TIME_NONE, gst.MESSAGE_EOS)
        self.pipeline.set_state(gst.STATE_NULL)


    def _debug(self, bus, msg):       
        if msg.type != gst.MESSAGE_ELEMENT or msg.structure.get_name() != 'level':
            print "DEBUG ", msg


    def _on_error(self, bus, msg):
        error, debug = msg.parse_error()
        error_info = "{} ({})".format(error, debug)
        logger.error(error_info)
        if not debug.count('canguro') and not self.error:
            self.stop_elements()
            gtk.gdk.threads_enter()
            self.error = error_info
            self.dispatcher.emit("recorder-error", error_info)
            gtk.gdk.threads_leave()
            # return True
    

    def _on_sync_message(self, bus, message):
        if message.structure is None:
            return
        if message.structure.get_name() == 'prepare-xwindow-id':
            name = message.src.get_property('name')
            logger.debug("on sync message 'prepare-xwindow-id' %r", name)

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
                logger.error('players[{}]: need a {}; got a {}: {}'.format(
                        name, gtk.DrawingArea, type(gtk_player), gtk_player))
        

    def _on_message_element(self, bus, message):
        if message.structure.get_name() == 'level':
            self.__set_vumeter(message)


    def __set_vumeter(self, message):
        struct = message.structure
        if  struct['rms'][0] == float("-inf"):
            valor = "Inf"
        else:            
            valor = struct['rms'][0]
        self.dispatcher.emit("recorder-vumeter", valor)


    def is_pausable(self):
        return all(bin.is_pausable for bin in self.bins.values())


    def mute_preview(self, value):
        for bin_name, bin in self.bins.iteritems():
            if bin.has_audio:
                bin.mute_preview(value)
                

    def set_drawing_areas(self, players):
        self.players = players        


    def get_display_areas_info(self):
        display_areas_info = []
        for bin_name, bin in self.bins.iteritems():
            display_areas_info.extend(bin.get_display_areas_info())
        return display_areas_info


    def get_bins_info(self):
        bins_info = []
        for bin_name, bin in self.bins.iteritems():
            bins_info.extend(bin.get_bins_info())
        return bins_info
        

            
