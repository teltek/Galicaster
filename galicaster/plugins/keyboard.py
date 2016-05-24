# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/keyboard
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
Plugin that shows a keyboard when a dialog window with input entries is shown
"""

from gi.repository import Gtk, Gdk
from galicaster.core import context
import subprocess
import re

from galicaster.utils.i18n import _

logger = context.get_logger()
pid = None

def init():
    global pid
    dispatcher = context.get_dispatcher()

    pid = is_running('onboard')
    if not pid:
        pid = subprocess.Popen(["onboard"]).pid

    dispatcher.connect('init', configure_keyboard)
    dispatcher.connect('quit', unconfigure_keyboard)

def configure_keyboard(dispatcher=None):
    execute(['gsettings',
        'set',
        'org.onboard.auto-show',
        'hide-on-key-press',
        'false'])

    execute(['gsettings',
        'set',
        'org.onboard.auto-show',
        'enabled',
        'true'])

def unconfigure_keyboard(dispatcher=None):
    execute(['gsettings',
        'set',
        'org.onboard.auto-show',
        'hide-on-key-press',
        'true'])

    execute(['gsettings',
        'set',
        'org.onboard.auto-show',
        'enabled',
        'false'])

    execute(['kill',pid])

def execute(command=[], logaserror=True):
    global logger

    level = 40 if logaserror else 10
    if command:
        try:
            proc = subprocess.check_output(command, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as exc:
            logger.log(level, "CalledProcessError trying to execute {}: {}".format(command, exc))
        except Exception as exc:
            logger.log(level, "Error trying to execute {}: {}".format(command, exc))


def is_running(process):

    s = subprocess.Popen(['ps', 'axw'],stdout=subprocess.PIPE)
    for x in s.stdout:
        if re.search(process, x):
            return x.split(' ')[0]
    return None
