# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/forcedurationrec
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
TODO. 
 - Key en stop_recording
 - Timer solo grabaciones manuales???
 - Comprobar si la grabacion es manual o automatica para empezar o no el Timer 
 - Añadir log
 - Hacer QA
"""
from threading import Timer
from threading import _Timer

from galicaster.core import context

t_stop = None

def init():
    dispatcher = context.get_dispatcher()
    dispatcher.connect("galicaster-notify-quit", do_stop_timers)
    dispatcher.connect('starting-record', create_timer)

    try:
        hours = int(conf.get('forcedurationrec','duration'))
    except ValueError:
        #log or set default value
        pass


def create_timer():
    if isinstance(t_stop, _Timer):
        t_stop.cancel()

    try:
        hours = int(conf.get('forcedurationrec','duration'))
    except ValueError:
        #log or set default value
        pass

    t_stop = Timer(60 * hours, stop_recording) 
    t_stop.start()
    

def stop_recording(sender=None):
    t_stop = None
    dispatcher = context.get_dispatcher()
    #dispatcher.emit("stop-record", key) #TODO Complete key


def do_stop_timers(sender=None):
    if isinstance(t_stop, _Timer):
        t_stop.cancel()
