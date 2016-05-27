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

import sys
import gi
gi.require_version('Atspi', '2.0')
gi.require_version('Wnck', '3.0')
from gi.repository import Atspi, Wnck

from dogtail.tree import *
from dogtail.utils import run
from sys import exit
import time
from galicaster.utils.systemcalls import is_running, execute

galicaster = None

def start_galicaster():
    
    global galicaster

    pid = is_running('run_galicaster')
    if pid:
        execute(['kill',str(pid)])
    run('python run_galicaster.py')
    galicaster =  root.application('run_galicaster.py')

def rec(recorder_time=5, repeating_times=1):
    
    # DIST
    dist_rec = __get_by_name('distrib_recorder_button')

    # RECORDER
    recorder_rec = __get_by_name('recorder_rec_button')
    recorder_back = __get_by_name('recorder_back_button')
    recorder_stop = __get_by_name('recorder_stop_button')

    count = 0
    try:
        count = count + 1
        dist_rec.click()
        recorder_rec.click()

        time.sleep(recorder_time)

        recorder_stop.click()
        accept_click = __get_by_name('stop_dialog_ok_button')
        accept_click.click()
        time.sleep(5)

        recorder_back.click()
        print "Recorder nº {} done".format(count)

        #TODO: Check MP information 
    except Exception as exc:
        print "Functional test error: {}".format(exc)
        exit(-1)    

def quit():
    
    #DIST
    dist_quit = __get_by_name('distrib_quit_button')

    dist_quit.click()
    accept_click = __get_by_name('quit_dialog_ok_button')
    accept_click.click()

def __get_by_name(accessible_name):

    global galicaster

    return galicaster.findChild(predicate.IsNamed(accessible_name))
