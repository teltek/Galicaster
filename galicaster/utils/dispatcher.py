# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/galicaster/utils/dispatcher
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


import gobject

class Dispatcher(gobject.GObject):
    def __init__(self):
        gobject.GObject.__gobject_init__(self)


gobject.type_register(Dispatcher)
gobject.signal_new("pr", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
#REC
gobject.signal_new("start-record", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
gobject.signal_new("stop-record", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
gobject.signal_new("restart-preview", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
gobject.signal_new("update-rec-vumeter", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
#AUDIO
gobject.signal_new("audio-mute", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
gobject.signal_new("audio-recovered", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
#PLAYER
gobject.signal_new("update-play-vumeter", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
gobject.signal_new("play-stopped", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
gobject.signal_new("play-list", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
#MEDIAMANAGER
gobject.signal_new("refresh-row", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
#STATUS
gobject.signal_new("update-play-status", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
gobject.signal_new("update-rec-status", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
gobject.signal_new("update-video", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
gobject.signal_new("start-before", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
#DISTRIBUTION
gobject.signal_new("change-mode", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,) )
gobject.signal_new("galicaster-status", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT) )
gobject.signal_new("galicaster-quit", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
#NET
gobject.signal_new("net-up", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
gobject.signal_new("net-down", Dispatcher, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, () )
