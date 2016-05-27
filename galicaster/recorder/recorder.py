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


import sys

from gi.repository import Gtk, Gst, Gdk
Gst.init(None)

from galicaster.core import context
from galicaster.utils.gstreamer import WeakMethod

logger = context.get_logger()

GST_TIMEOUT= Gst.SECOND*10

class Recorder(object):

    def __init__(self, bins, players={}):
        """
        Initialize the recorder.

        :param bins: ``list`` of ``dict`` with bin name, device, path, and optional parameters.
        :param players: (optional) ```Gtk.DrawingArea``` ```list``` to use as player.
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
        self.__start_record_time = -1
        self.__pause_timestamp = 0
        self.__paused_time = 0
        self.__valves_status = False
        self.__duration = 0

        self.pipeline = Gst.Pipeline.new("galicaster_recorder")
        self.bus = self.pipeline.get_bus()

        self.bins = dict()
        self.callback = None

        self.bus.add_signal_watch()
        self.bus.enable_sync_message_emission()
#        self.bus.connect('message', WeakMethod(self, '_debug')) # TO DEBUG
        self.bus.connect('message::error', WeakMethod(self, '_on_error'))        
        self.bus.connect('message::element', WeakMethod(self, '_on_message_element'))


        try:            
            for bin in bins:
                name = bin['name']
                
                mod_name = 'galicaster.recorder.bins.' + bin['device']
                __import__(mod_name)
                mod = sys.modules[mod_name]
                Klass = getattr(mod, "GC" + bin['device'])
                
                logger.debug("Init bin {} {}".format(name, mod_name))
                self.bins[name] = Klass(bin)
                self.pipeline.add(self.bins[name])
                
        except Exception as exc:
            logger.info("Removing loaded bins due to an error...")
            for bin_name in self.bins:
                self.pipeline.remove(self.bins[bin_name])
            self.bins.clear()
            
            self.error = str(exc)
            name = name if 'name' in locals() else 'Unknown'
            message = 'Invalid track type "{}" for "{}" track: {}'.format(bin.get('device'), name, exc)
            raise NameError(message)



    def get_status(self, timeout=GST_TIMEOUT):        
        status = self.pipeline.get_state(timeout)        

        if status[0] == Gst.StateChangeReturn.ASYNC:
            self.__emit_error('Timeout getting recorder status, current status: {}'.format(status), '', stop=False)
        
        return status

    def get_time(self):
        return self.pipeline.get_clock().get_time()


    def get_recorded_time(self):
        """Get recorded time in usec"""
        if self.__start_record_time == -1:
            return 0

        status = self.get_status()[1]
        
        if status == Gst.State.NULL:
            return self.__duration
        elif status == Gst.State.PAUSED:
            return self.__query_position() - self.__start_record_time - self.__paused_time - (self.__query_position() - self.__pause_timestamp)

        return self.__query_position() - self.__start_record_time - self.__paused_time


    def __query_position(self):
        try:
            succes, duration = self.pipeline.query_position(Gst.Format.TIME)
        except:
            duration = 0
        return duration


    def preview(self):
        logger.debug("recorder preview")
        self.__set_state(Gst.State.PAUSED)
        for bin in self.bins.values():
            bin.changeValve(True)
        self.__valves_status = True
        self.__set_state(Gst.State.PLAYING)


    def preview_and_record(self):
        logger.debug("recorder preview and record")
        self.__set_state(Gst.State.PLAYING)
        self.__start_record_time = self.__query_position()
        self.is_recording = True


    def __set_state(self, new_state=Gst.State.PAUSED):
        change = self.pipeline.set_state(new_state)
            
        if change == Gst.StateChangeReturn.FAILURE:
            # text = None
            random_bin = None
            for key, value in self.bins.iteritems():
                if not value.getSource():
                    random_bin = value
                    # text = "Error on track : "+ key
                if not random_bin:
                    random_bin = value
                    # text = "Error on unknow track"

            src = random_bin
            # error = Gst.StreamError(Gst.ResourceError.FAILED)
            # error = Glib.GError(Gst.ResourceError, Gst.ResourceError.FAILED, text)

            a = Gst.Structure.new_from_string('letpass')
            message = Gst.Message.new_custom(Gst.MessageType.ERROR,src, a)   
            # message = Gst.Message.new_error(src, error, str(random_bin)+"\nunknown system_error")
            self.bus.post(message)
            self.dispatcher.emit("recorder-error","Driver error")
            return False

        self.get_status()
        return True


    def record(self):
        if self.get_status()[1] == Gst.State.PLAYING:
            for bin in self.bins.values():
                bin.changeValve(False)
            self.__valves_status = False
        
        self.__start_record_time = self.__query_position()
        self.is_recording = True


    def pause(self):
        logger.debug("recorder paused")
        self.__set_state(Gst.State.PAUSED)
        return True


    # doesn't pause pipeline, just stops recording
    def pause_recording(self):
        if self.is_recording:
            logger.debug("recording paused (warning: this doesn't pause pipeline, just stops recording)")
            self.__pause_timestamp = self.__query_position()
            for bin in self.bins.values():
                bin.changeValve(True)                
            self.__valves_status = True


    def resume(self):
        logger.debug("recorder resumed")
        self.__set_state(Gst.State.PLAYING)
        return True


    def resume_recording(self):
        logger.debug("recording resumed")
        for bin in self.bins.values():
            bin.changeValve(False)
        self.__valves_status = False

        self.__paused_time = self.__paused_time + (self.__query_position() - self.__pause_timestamp)
        self.__set_state(Gst.State.PLAYING)
        return True


    def stop(self, force=False):
        if self.get_status()[1] == Gst.State.PAUSED:
            logger.debug("Resume recorder before stopping")
            self.resume()

        if self.is_recording and not force:
            if self.__valves_status == True:
                self.resume_recording()
                
            logger.debug("Stopping recorder, sending EOS event to sources")
                
            self.is_recording = False
            self.__duration = self.__query_position() - self.__start_record_time - self.__paused_time
            a = Gst.Structure.new_from_string('letpass')
            event = Gst.Event.new_custom(Gst.EventType.EOS, a)
            for bin_name, bin in self.bins.iteritems():
                bin.send_event_to_src(event)

            msg = self.bus.timed_pop_filtered(GST_TIMEOUT, Gst.MessageType.EOS)            
            if not msg:
                self.__emit_error('Timeout trying to receive EOS message', '', stop=False)
            else:
                logger.debug('EOS message successfully received')

        self.pipeline.set_state(Gst.State.NULL)


    def _debug(self, bus, msg):       
        if msg.type != Gst.MessageType.ELEMENT or msg.get_structure().get_name() != 'level':
            print "DEBUG ", msg


    def _on_error(self, bus, msg):
        error, debug = msg.parse_error()
        error_info = "{} ({})".format(error, debug)
        return self.__emit_error(error_info, debug)

    
    def __emit_error(self, error_info, debug, stop=True):
        if not self.error:
            logger.error(error_info)
            if not debug or (debug and not debug.count('canguro')):
                if stop:
                    self.stop(True)
                self.error = error_info
                self.dispatcher.emit("recorder-error", error_info)
                # return True
        

    def _on_sync_message(self, bus, message):
        if message.get_structure() is None:
            return
        if message.get_structure().get_name() == 'prepare-window-handle':
            name = message.src.get_property('name')
            logger.debug("on sync message 'prepare-window-handle' %r", name)

            # Workaround for autovideosink (it name contains the sink that is being used)
            sep_autovideosink = "-actual-sink"
            if sep_autovideosink in name:
                name = name.split(sep_autovideosink, 1)[0]
            
            try:
                gtk_player = self.players[name]
                if not isinstance(gtk_player, Gtk.DrawingArea):
                    raise TypeError()
                Gdk.threads_enter()
                Gdk.Display.get_default().sync()            
                message.src.set_property('force-aspect-ratio', True)
#                message.src.set_xwindow_id(gtk_player.get_property(window).get_xid())
                message.src.set_window_handle(gtk_player.get_property('window').get_xid())
                Gdk.threads_leave()
                
                # Disconnect from on_sync_message (From now on it's not needed)
                del self.players[name]
                if not self.players:
                    #self.bus.disable_sync_message_emission()
                    self.bus.handler_disconnect(self.__sync_handle)
                
            except KeyError:
                pass
            except TypeError:
                logger.error('players[{}]: need a {}; got a {}: {}'.format(
                        name, Gtk.DrawingArea, type(gtk_player), gtk_player))
        

    def _on_message_element(self, bus, message):
        if message.get_structure().get_name() == 'level':
            self.__set_vumeter(message)
        else:
            self.dispatcher.emit("recorder-message-element", message.get_structure())


    def __set_vumeter(self, message):
        struct = message.get_structure()
        rms_values = struct.get_value('rms')
        stereo = True

        if float(rms_values[0]) == float("-inf"):
            valor = "Inf"
        else:            
            valor = float(rms_values[0])

        if len(rms_values) > 1:
            if float(rms_values[1]) == float("-inf"):
                valor2 = "Inf"
            else:            
                valor2 = float(rms_values[1])
        else:
            stereo = False
            valor2 = valor

        self.dispatcher.emit("recorder-vumeter", valor, valor2, stereo)


    def is_pausable(self):
        return all(bin.is_pausable for bin in self.bins.values())


    def mute_preview(self, value):
        for bin_name, bin in self.bins.iteritems():
            if bin.has_audio:
                bin.mute_preview(value)
                

    def set_drawing_areas(self, players):
        self.players = players        
        if self.players:
            self.__sync_handle = self.bus.connect('sync-message::element', WeakMethod(self, '_on_sync_message'))


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

