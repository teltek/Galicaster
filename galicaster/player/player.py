# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/player/player
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.
#
#   pipestr = ( ' filesrc location=video1 ! decodebin2 name=audio ! queue ! xvimagesink name=play1 '
#               ' filesrc location=video2 ! decodebin2 ! queue ! xvimagesink name=play2 ' 
#               ' audio. ! queue ! level name=VUMETER message=true interval=interval ! autoaudiosink name=play3 ')
#
#


import gtk
import gst
import os
from gst.pbutils import Discoverer

from galicaster.core import context
from galicaster.utils.gstreamer import WeakMethod

logger = context.get_logger()

class Player(object):

    def __init__(self, files, players = {}):
        """
        Initialize the player
        This class is event-based and needs a mainloop to work properly.

        :param files: a ``dict`` a file name list to play
        :param players: a ``dict`` a gtk.DrawingArea list to use as player
        """
        #FIXME comprobar que existen los files sino excepcion
        if not isinstance(files, dict):
            raise TypeError(
                '%s: need a %r; got a %r: %r' % ('files', dict, type(files), files)
            )
        #FIXME check the values are gtk.DrawingArea
        if not isinstance(players, dict):
            raise TypeError(
                '%s: need a %r; got a %r: %r' % ('players', dict, type(players), players)
            )

        self.dispatcher = context.get_dispatcher() 
        self.files = files
        self.players = players
        self.duration = 0
        self.has_audio = False
        self.pipeline_complete = False
        self.audio_sink = None

        self.__get_duration_and_run()


    def create_pipeline(self):
        self.pipeline = gst.Pipeline("galicaster_player")
        bus = self.pipeline.get_bus()

        # Create bus and connect several handlers
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect('message::eos', WeakMethod(self, '_on_eos'))
        bus.connect('message::error', WeakMethod(self, '_on_error'))
        bus.connect('message::element', WeakMethod(self, '_on_message_element'))
        bus.connect('message::state-changed', WeakMethod(self, '_on_state_changed'))
        bus.connect('sync-message::element', WeakMethod(self, '_on_sync_message'))

        # Create elements
        for name, location in self.files.iteritems():
            logger.info('playing %r', location)
            src = gst.element_factory_make('filesrc', 'src-' + name)
            src.set_property('location', location)
            dec = gst.element_factory_make('decodebin2', 'decode-' + name)
            
            # Connect handler for 'new-decoded-pad' signal
            dec.connect('new-decoded-pad', WeakMethod(self, '_on_new_decoded_pad'))
            
            # Link elements
            self.pipeline.add(src, dec)
            src.link(dec)

        return None


    def get_status(self):
        """
        Get the player status
        """
        return self.pipeline.get_state()


    def is_playing(self):
        """
        Get True if is playing else False
        """
        return (self.pipeline.get_state()[1] == gst.STATE_PLAYING)


    def get_time(self):
        """
        Get the player current time.
        """
        return self.pipeline.get_clock().get_time()


    def play(self):
        """
        Start to play
        """
        logger.debug("player playing")
        if not self.pipeline_complete:
            self.pipeline.set_state(gst.STATE_PAUSED)
            self.pipeline_complete = True
        else:
            self.pipeline.set_state(gst.STATE_PLAYING)
        return None


    def pause(self):
        """
        Pause the player
        """
        logger.debug("player paused")
        self.pipeline.set_state(gst.STATE_PAUSED)
        self.pipeline.get_state()


    def stop(self):
        """
        Stop the player

        Pause the reproduction and seek to begin
        """
        logger.debug("player stoped")
        self.pipeline.set_state(gst.STATE_PAUSED)
        self.seek(0) 
        self.pipeline.get_state()
        return None


    def quit(self):
        """
        Close the pipeline
        """
        logger.debug("player deleted")
        self.pipeline.set_state(gst.STATE_NULL)
        self.pipeline.get_state()
        return None


    def seek(self, pos, recover_state=False):
        """
        Seek the player

        param: pos time in nanoseconds
        """
        result = self.pipeline.seek(1.0, 
            gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_ACCURATE, # REVIEW sure about ACCURATE
            gst.SEEK_TYPE_SET, pos, 
            gst.SEEK_TYPE_NONE, -1) 
        if recover_state and self.pipeline.get_state()[1] == gst.STATE_PAUSED:
            self.pipeline.set_state(gst.STATE_PLAYING)
        return result


    def get_duration(self):       
        return self.duration


    def get_position(self, format=gst.FORMAT_TIME):
        return self.pipeline.query_position(format)


    def get_volume(self):
        if self.audio_sink == None:
            return 100
        return self.audio_sink.get_property('volume')


    def set_volume(self, volume):
        if self.audio_sink != None:
            self.audio_sink.set_property('volume', volume)
	
    def _on_state_changed(self, bus, message):
        old, new, pending = message.parse_state_changed()
        if (isinstance(message.src, gst.Pipeline) and 
            (old, new) == (gst.STATE_READY, gst.STATE_PAUSED) ):
            self.pipeline.set_state(gst.STATE_PLAYING)

    def _on_new_decoded_pad(self, element, pad, last):         
        name = pad.get_caps()[0].get_name()
        element_name = element.get_name()[7:]
        logger.debug('new decoded pad: %r in %r', name, element_name)
        sink = None

        if name.startswith('audio/'):
            #if element_name == 'presenter' or len(self.files) == 1:
            if not self.has_audio:
                self.has_audio = True
                self.audio_sink = gst.element_factory_make('autoaudiosink', 'audio')
                vumeter = gst.element_factory_make('level', 'level') 
                vumeter.set_property('message', True)
                vumeter.set_property('interval', 100000000) # 100 ms
                self.pipeline.add(self.audio_sink, vumeter)
                pad.link(vumeter.get_pad('sink'))
                vumeter.link(self.audio_sink)
                vumeter.set_state(gst.STATE_PAUSED)
                assert self.audio_sink.set_state(gst.STATE_PAUSED)
                
        elif name.startswith('video/'):
            sink = gst.element_factory_make('xvimagesink', 'sink-' + element_name) 
            sink.set_property('force-aspect-ratio', True)
            self.pipeline.add(sink)
            pad.link(sink.get_pad('sink'))
            assert sink.set_state(gst.STATE_PAUSED)
            
        return sink


    def _on_eos(self, bus, msg):
        logger.info('Player EOS')
        self.stop()
        self.dispatcher.emit("play-stopped")


    def _on_error(self, bus, msg):
        error = msg.parse_error()[1]
        logger.error(error)
        self.stop()


    def _on_sync_message(self, bus, message):
        if message.structure is None:
            return
        if message.structure.get_name() == 'prepare-xwindow-id':
            name = message.src.get_property('name')[5:]

            logger.debug("on sync message 'prepare-xwindow-id' %r", name)

            try:
                gtk_player = self.players[name]
                if not isinstance(gtk_player, gtk.DrawingArea):
                    raise TypeError()
                gtk.gdk.threads_enter()
                gtk.gdk.display_get_default().sync()
                message.src.set_xwindow_id(gtk_player.window.xid)
                message.src.set_property('force-aspect-ratio', True)
                gtk.gdk.threads_leave()

            except TypeError:
                logger.error('players[%r]: need a %r; got a %r: %r' % (
                        name, gtk.DrawingArea, type(gtk_player), gtk_player))
            except KeyError:
                pass


    def _on_message_element(self, bus, message):
        if message.structure.get_name() == 'level':
            self.__set_vumeter(message)


    def __set_vumeter(self, message):
        struct = message.structure
        
        if  struct['rms'][0] == float("-inf"):
            valor = "Inf"
        else:            
            valor = struct['rms'][0]
        self.dispatcher.emit("update-play-vumeter", valor)


    def __discover(self,filepath):
        discoverer = Discoverer(1*gst.SECOND)
        info = discoverer.discover_uri('file://'+filepath)
        self.duration = info.get_duration() / 1000000000
        logger.info("Duration ON_DISCOVERED: " + str(self.duration))        
        self.create_pipeline()
        return True


    def __get_duration_and_run(self):
        # choose lighter file
        size = location = None
        for key,value in self.files.iteritems():
            new = os.path.getsize(value)
            if not size or new > size:
                location = value
        return self.__discover(location)
