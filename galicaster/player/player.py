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
#   pipestr = ( ' filesrc location=video1 ! decodebin name=audio ! queue ! xvimagesink name=play1 '
#               ' filesrc location=video2 ! decodebin ! queue ! xvimagesink name=play2 '
#               ' audio. ! queue ! level name=VUMETER message=true interval=interval ! autoaudiosink name=play3 ')
#
#

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")

from gi.repository import Gtk, Gst, Gdk, GObject
from gi.repository import GdkX11 # noqa: ignore=F401
# Needed for window.get_xid(), xvimagesink.set_window_handle(), respectively:

import os

from galicaster.core import context
from galicaster.utils.gstreamer import WeakMethod
from galicaster.utils.mediainfo import get_duration

logger = context.get_logger()

GST_TIMEOUT= Gst.SECOND*10

INIT    = 0
READY   = 1
PLAYING = 2
PAUSED  = 3
STOPPED = 4
ERRORED = 5

class Player(object):
    def __init__(self, files, players={}):
        """
        Initialize the player
        This class is event-based and needs a mainloop to work properly.

        :param files: a ``dict`` a file name list to play
        :param players: a ``dict`` a Gtk.DrawingArea list to use as player
        """
        # FIXME comprobar que existen los files sino excepcion
        if not isinstance(files, dict):
            raise TypeError(
                '%s: need a %r; got a %r: %r' % ('files', dict, type(files), files)
            )
        # FIXME check the values are Gtk.DrawingArea
        if not isinstance(players, dict):
            raise TypeError(
                '%s: need a %r; got a %r: %r' % ('players', dict, type(players), players)
            )

        self.dispatcher = context.get_dispatcher()
        self.files = files
        self.players = players
        self.duration = 0
        self.has_audio = False
        self.error = None
        self.pipeline_complete = False
        self.pipeline = None
        self.audio_sink = None

        self.__get_duration_and_run()

    def create_pipeline(self):
        self.pipeline = Gst.Pipeline.new("galicaster_player")
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
            src = Gst.ElementFactory.make('filesrc', 'src-' + name)
            src.set_property('location', location)
            dec = Gst.ElementFactory.make('decodebin', 'decode-' + name)

            # Connect handler for 'pad-added' signal
            dec.connect('pad-added', WeakMethod(self, '_on_new_decoded_pad'))

            # Link elements
            self.pipeline.add(src)
            self.pipeline.add(dec)
            src.link(dec)

        self.error = None
        return None

    def get_status(self, timeout=GST_TIMEOUT):
        """
        Get the player status
        """
        status = self.pipeline.get_state(timeout)

        if status[0] == Gst.StateChangeReturn.ASYNC:
            logger.error('Timeout getting recorder status, current status: {}'.format(status))

        return status


    def is_playing(self):
        """
        Get True if is playing else False
        """
        return (self.get_status()[1] == Gst.State.PLAYING)

    def get_time(self):
        """
        Get the player current time.
        """
        try:
            clock = self.pipeline.get_clock()
            if clock:
                return clock.get_time()
        except Exception:
            # logger.debug("Exception trying to get current time: {}".format(exc))
            pass

        return 0

    def play(self):
        """
        Start to play
        """
        logger.debug("player playing")
        if not self.pipeline_complete:
            self.pipeline.set_state(Gst.State.PAUSED)
            self.pipeline_complete = True
        else:
            self.dispatcher.emit("player-status", PLAYING)
            self.pipeline.set_state(Gst.State.PLAYING)
        return None

    def pause(self):
        """
        Pause the player
        """
        logger.debug("player paused")
        self.pipeline.set_state(Gst.State.PAUSED)
        self.dispatcher.emit("player-status", PAUSED)
        self.get_status()

    def stop(self):
        """
        Stop the player

        Pause the reproduction and seek to begin
        """
        logger.debug("player stoped")
        self.pipeline.set_state(Gst.State.PAUSED)
        self.seek(0)
        self.dispatcher.emit("player-status", STOPPED)
        self.get_status()
        return None

    def quit(self):
        """
        Close the pipeline
        """
        logger.debug("player deleted")
        self.pipeline.set_state(Gst.State.NULL)
        self.dispatcher.emit("player-status", STOPPED)
        self.get_status()
        return None

    def seek(self, pos, recover_state=False):
        """
        Seek the player

        param: pos time in nanoseconds
        """
        result = self.pipeline.seek(1.0,
                                    Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
                                    # REVIEW sure about ACCURATE
                                    Gst.SeekType.SET, pos,
                                    Gst.SeekType.NONE, -1)
        if recover_state and self.get_status()[1] == Gst.State.PAUSED:
            self.pipeline.set_state(Gst.State.PLAYING)
            self.dispatcher.emit("player-status", PLAYING)
        return result

    def get_duration(self):
        return self.duration

    def get_position(self, format=Gst.Format.TIME):
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
        if (isinstance(message.src, Gst.Pipeline) and
                    (old, new) == (Gst.State.READY, Gst.State.PAUSED)):
            self.pipeline.set_state(Gst.State.PLAYING)

    def _on_new_decoded_pad(self, element, pad):
        name = pad.query_caps(None).to_string()
        element_name = element.get_name()[7:]
        logger.debug('new decoded pad: %r in %r', name, element_name)
        sink = None

        if self.error:
            logger.debug('There is an error, so ingoring decoded pad: %r in %r', name, element_name)
            return None

        if name.startswith('audio/'):
            # if element_name == 'presenter' or len(self.files) == 1:
            if not self.has_audio:
                self.has_audio = True
                self.audio_sink = Gst.ElementFactory.make('autoaudiosink', 'audio')
                vumeter = Gst.ElementFactory.make('level', 'level')
                vumeter.set_property('message', True)
                vumeter.set_property('interval', 100000000)  # 100 ms
                self.pipeline.add(self.audio_sink)
                self.pipeline.add(vumeter)
                pad.link(vumeter.get_static_pad('sink'))
                vumeter.link(self.audio_sink)
                vumeter.set_state(Gst.State.PAUSED)
                assert self.audio_sink.set_state(Gst.State.PAUSED)

        elif name.startswith('video/'):
            vconvert = Gst.ElementFactory.make('videoconvert', 'vconvert-' + element_name)
            self.pipeline.add(vconvert)

            sink = Gst.ElementFactory.make('xvimagesink', 'sink-' + element_name)
            sink.set_property('force-aspect-ratio', True)
            self.pipeline.add(sink)

            pad.link(vconvert.get_static_pad('sink'))
            vconvert.link(sink)
            vconvert.set_state(Gst.State.PAUSED)

            assert sink.set_state(Gst.State.PAUSED)

        return sink

    def _on_eos(self, bus, msg):
        logger.info('Player EOS')
        self.stop()
        self.dispatcher.emit("player-status", STOPPED)

    def _on_error(self, bus, msg):
        self.error = msg.parse_error()[1]
        logger.error(self.error)
        self.dispatcher.emit("player-status", ERRORED)
        self.quit()

    def _prepare_window_handler(self, gtk_player, message):
        Gdk.Display.get_default().sync()
        message.src.set_window_handle(gtk_player.get_property('window').get_xid())
        message.src.set_property('force-aspect-ratio', True)

    def _on_sync_message(self, bus, message):
        if message.get_structure() is None:
            return
        if message.get_structure().get_name() == 'prepare-window-handle':
            name = message.src.get_property('name')[5:]

            logger.debug("on sync message 'prepare-window-handle' %r", name)

            try:
                gtk_player = self.players[name]
                if not isinstance(gtk_player, Gtk.DrawingArea):
                    raise TypeError()
                GObject.idle_add(self._prepare_window_handler, gtk_player, message)

            except TypeError:
                pass
                logger.error('players[%r]: need a %r; got a %r: %r' % (
                    name, Gtk.DrawingArea, type(gtk_player), gtk_player))
            except KeyError:
                pass

    def _on_message_element(self, bus, message):
        if message.get_structure().get_name() == 'level':
            self.__set_vumeter(message)

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

        self.dispatcher.emit("player-vumeter", valor, valor2, stereo)

    def __discover(self, filepath):
        self.duration = 0
        try:
            self.duration = get_duration(filepath)
            logger.info("Duration ON_DISCOVERED: " + str(self.duration))
        except Exception as exc:
            logger.debug("Error trying to get duration of {}: {}".format(filepath, exc))

        self.create_pipeline()
        return True

    def __get_duration_and_run(self):
        # choose lighter file
        size = location = None
        for key, value in self.files.iteritems():
            new = os.path.getsize(value)
            if not size or new > size:
                location = value
        return self.__discover(location)
