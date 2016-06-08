# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/core/context
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

# Stress test: repeatedly:
#  1.- Go to recorder section.
#  2.- Start to record.
#  3.- Stop the recording.
#  4.- Go back to main menu.
#
# First, enable accessibility support in your GNOME session with:
#  gsettings set org.gnome.desktop.interface toolkit-accessibility true

from dogtail.utils import run

import sys
from sys import exit
import time
from galicaster.utils.systemcalls import is_running, execute

galicaster = None
# FIXME: imported libreries as global variables to avoid Travis importing errors
root = None
predicate = None

def start_galicaster():

    global galicaster
    global root, predicate

    import gi
    gi.require_version('Atspi', '2.0')
    gi.require_version('Wnck', '3.0')
    from dogtail.tree import root, predicate

    pid = is_running('run_galicaster')
    if pid:
        execute(['kill',str(pid)])
    run('python run_galicaster.py')
    galicaster = root.application('run_galicaster.py')

def rec(recorder_time=5, repeating_times=1):
    
    count = 0
    try:
        count = count + 1
        go_to_recorder()
        start_recording()

        time.sleep(recorder_time)

        stop_recording()
        time.sleep(5)

        go_to_distrib()
        print "Recorder nº {} done".format(count)

        #TODO: Check MP information 
    except Exception as exc:
        print "Functional test error: {}".format(exc)
        exit(-1)    

def go_to_recorder():
    #TODO: Check where we are
    __get_by_name('distrib_recorder_button').click()

def go_to_distrib():
    #TODO: Check where we are
    __get_by_name('recorder_back_button').click()

def start_recording():
    #TODO: Check where we are
    __get_by_name('recorder_rec_button').click()

def stop_recording():
    #TODO: Check where we are
    __get_by_name('recorder_stop_button').click()
    __get_by_name('stop_dialog_ok_button').click()

def pause_recording():
    __get_by_name('recorder_pause_button').click()

def rewind_recording():
    __get_by_name('paused_dialog_ok_button').click()

def quit():
    #TODO: Check where we are
    __get_by_name('distrib_quit_button').click()
    __get_by_name('quit_dialog_ok_button').click()

def __get_by_name(accessible_name):

    global galicaster

    return galicaster.findChild(predicate.IsNamed(accessible_name))



