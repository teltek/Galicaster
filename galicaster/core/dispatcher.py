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
#        'galicaster-init': (GObject.SIGNAL_RUN_FIRST, None,()),
#        'pr': (GObject.SIGNAL_RUN_FIRST, None,(GObject.TYPE_PYOBJECT,)),
#        'upcoming-recording': (GObject.SignalFlags.RUN_LAST, None, () ),
#        'recorder-vumeter': (GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,)),
#        'recorder-error': (GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) ),
#        'recorder-status', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
#        }

    def __init__(self):
        GObject.GObject.__init__(self)

    def add_new_signal(self, name, param=False):
        parameters = (GObject.TYPE_PYOBJECT,) if param else ()
        GObject.signal_new(name, self, GObject.SignalFlags.RUN_LAST, None, parameters)
        
        


#GObject.type_register(Dispatcher)
GObject.signal_new('galicaster-init', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('pr', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
#REC
GObject.signal_new('upcoming-recording', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('starting-record', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('recorder-vumeter', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
GObject.signal_new('recorder-error', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
GObject.signal_new('recorder-status', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
GObject.signal_new('reload-profile', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('start-preview', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('recorder-closed', Dispatcher, GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,) )

#AUDIO
GObject.signal_new('audio-mute', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('audio-recovered', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('enable-no-audio', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('disable-no-audio', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
#PLAYER
GObject.signal_new('update-play-vumeter', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
GObject.signal_new('play-stopped', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('play-list', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )

#MEDIAMANAGER
GObject.signal_new('refresh-row', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
#STATUS
GObject.signal_new('update-play-status', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
GObject.signal_new('update-video', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
#DISTRIBUTION
GObject.signal_new('change-mode', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
GObject.signal_new('galicaster-status', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT) )
GObject.signal_new('galicaster-quit', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('galicaster-notify-quit', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('galicaster-shutdown', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('galicaster-notify-shutdown', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )

#TIMER
GObject.signal_new('galicaster-notify-nightly', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('galicaster-notify-timer-short', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('galicaster-notify-timer-long', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('after-process-ical', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
#NET
GObject.signal_new('net-up', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
GObject.signal_new('net-down', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
#ABOUT
GObject.signal_new('show-about', Dispatcher, GObject.SignalFlags.RUN_LAST, None, () )
#PROVISIONAL
GObject.signal_new('create-mock-mp', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,) )
#WORKER
GObject.signal_new('start-operation', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT,) )
GObject.signal_new('stop-operation', Dispatcher, GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT) )
