# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/core/dispatcher
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.


"""
Proporciona un sistema global de manejo de eventos a Galicaster. Esta basado en las señales de GObject.
Las señales existentes estan difinidas en este modulo.

To connect to a signal:
dispatcher.connect('signal-name', callback)

To emit a signal:
dispatcher.emit('signal-name', parameters)
"""

from gi.repository import GObject

class Dispatcher(GObject.GObject):
#    __gsignals__ = {
#        'init': (GObject.SIGNAL_RUN_FIRST, None,()),
#        'pr': (GObject.SIGNAL_RUN_FIRST, None,(GObject.TYPE_PYOBJECT,)),
#        'recorder-upcoming-event': (GObject.SignalFlags.RUN_LAST, None, () ),
#        'recorder-vumeter': (GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,)),
#        'recorder-error': (GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) ),
#        'recorder-status', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
#        }

    def __init__(self):
        GObject.GObject.__init__(self)

    def add_new_signal(self, name, *args):
        parameters = ()
        for element in args:
            parameters = parameters + (GObject.TYPE_PYOBJECT,)

        if not self.is_signal(name):
            GObject.signal_new(name, self, GObject.SignalFlags.RUN_LAST, None, parameters)


    def connect_ui(self, detailed_signal, handler, *args):
        def f(*args):
            GObject.idle_add(handler, *args)

        self.connect(detailed_signal, f, *args)


    def is_signal(self, name):
        if name in GObject.signal_list_names(self):
            return True
        return False

#GObject.type_register(Dispatcher)
GObject.signal_new('init', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('pr', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
GObject.signal_new('gc-shown', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
#REC
GObject.signal_new('recorder-upcoming-event', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('recorder-scheduled-event', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
GObject.signal_new('recorder-vumeter', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT,) )
GObject.signal_new('recorder-message-element', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
GObject.signal_new('recorder-error', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
GObject.signal_new('recorder-status', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
GObject.signal_new('action-reload-profile', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('recorder-ready', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('recorder-starting', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('recorder-started', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
GObject.signal_new('recorder-stopped', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )

#AUDIO
GObject.signal_new('audio-mute', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('audio-recovered', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('action-audio-enable-msg', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('action-audio-disable-msg', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
#PLAYER
GObject.signal_new('player-vumeter', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT,) )
GObject.signal_new('player-status', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
GObject.signal_new('play-list', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )

#MEDIAMANAGER
GObject.signal_new('action-mm-refresh-row', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
#DISTRIBUTION
GObject.signal_new('action-view-change', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
GObject.signal_new('view-changed', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT) )
GObject.signal_new('action-quit', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('quit', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('action-shutdown', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('shutdown', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('action-key-press', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT) )
GObject.signal_new('action-key-release', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT) )

#TIMER
GObject.signal_new('timer-nightly', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('timer-short', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('timer-long', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('ical-processed', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
#NET
GObject.signal_new('opencast-status', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
#PROVISIONAL
GObject.signal_new('action-create-mock-mp', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
#WORKER
GObject.signal_new('operation-started', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT,) )
GObject.signal_new('operation-stopped', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT) )
