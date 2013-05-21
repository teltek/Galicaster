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

import gobject

class Dispatcher(gobject.GObject):
    def __init__(self):
        gobject.GObject.__gobject_init__(self)

    def add_new_signal(self, name, param=False):
        parameters = (gobject.TYPE_PYOBJECT,) if param else ()
        gobject.signal_new(name, self, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, parameters)
        
        


gobject.type_register(Dispatcher)
gobject.signal_new('galicaster-init', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
gobject.signal_new('pr', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
#REC
gobject.signal_new('upcoming-recording', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
gobject.signal_new('start-record', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) ) #FIXME define where and wich signals emit on scheduled/manual record
gobject.signal_new('starting-record', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
gobject.signal_new('stop-record', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
gobject.signal_new('restart-preview', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
gobject.signal_new('update-rec-vumeter', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
# NEW ON 1.2
gobject.signal_new('recorder-error', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
gobject.signal_new('reload-profile', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
gobject.signal_new('start-preview', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )

#AUDIO
gobject.signal_new('audio-mute', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
gobject.signal_new('audio-recovered', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
#PLAYER
gobject.signal_new('update-play-vumeter', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
gobject.signal_new('play-stopped', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
gobject.signal_new('play-list', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )

#MEDIAMANAGER
gobject.signal_new('refresh-row', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
#STATUS
gobject.signal_new('update-play-status', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
gobject.signal_new('update-rec-status', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
gobject.signal_new('update-video', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
gobject.signal_new('start-before', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
gobject.signal_new('update-pipeline-status', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT,) )

#DISTRIBUTION
gobject.signal_new('change-mode', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
gobject.signal_new('galicaster-status', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT) )
gobject.signal_new('galicaster-quit', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
gobject.signal_new('galicaster-notify-quit', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
gobject.signal_new('galicaster-shutdown', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
gobject.signal_new('galicaster-notify-shutdown', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )

#TIMER
gobject.signal_new('galicaster-notify-nightly', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
gobject.signal_new('galicaster-notify-timer-short', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
gobject.signal_new('galicaster-notify-timer-long', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
gobject.signal_new('after-process-ical', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
#NET
gobject.signal_new('net-up', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
gobject.signal_new('net-down', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
#ABOUT
gobject.signal_new('show-about', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
#PROVISIONAL
gobject.signal_new('create-mock-mp', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
#WORKER
gobject.signal_new('start-operation', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT,) )
gobject.signal_new('stop-operation', Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT) )
