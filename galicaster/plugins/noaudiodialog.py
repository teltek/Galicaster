# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/noaudiodialog
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""

"""

import gtk
from galicaster.core import context
from galicaster.classui import get_ui_path


no_audio = False
no_audio_dialog = None
focus_is_active = True


def init():
    global focus_is_active

    dispatcher = context.get_dispatcher()
    conf = context.get_conf()

    if conf.get('basic','admin') == 'True':
        focus_is_active = False

    dispatcher.connect('audio-mute', warning_audio)
    dispatcher.connect('audio-recovered', warning_audio_destroy)
    dispatcher.connect('galicaster-status', event_change_mode)


def warning_audio(element=None): # TODO make it generic
    global no_audio
    global no_audio_dialog
    global focus_is_active

    no_audio = True
    if focus_is_active and no_audio_dialog == None:
        gui = gtk.Builder()
        gui.add_from_file(get_ui_path('warning.glade'))
        no_audio_dialog = gui.get_object('dialog')
        no_audio_dialog.set_transient_for(context.get_mainwindow().get_toplevel())
        no_audio_dialog.show() 
    return True


def warning_audio_destroy(element=None):
    global no_audio
    global no_audio_dialog

    no_audio = False
    try:
        assert no_audio_dialog
    except:
        return True           
    no_audio_dialog.destroy()
    no_audio_dialog = None
    return True      



def event_change_mode(orig, old_state, new_state):
    global no_audio
    global no_audio_dialog
    global focus_is_active

    if new_state == 0: 
        focus_is_active = True
        if no_audio:
            warning_audio()

    if old_state == 0:
        focus_is_active = False

        if no_audio:
            no_audio_dialog.destroy()
            no_audio_dialog = None


