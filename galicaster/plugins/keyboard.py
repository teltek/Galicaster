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

from galicaster.core import context
import subprocess

from galicaster.utils.systemcalls import write_dconf_settings, execute, is_running

logger = context.get_logger()

def init():
    dispatcher = context.get_dispatcher()

    pid = is_running('onboard')
    if not pid:
        subprocess.Popen(["onboard"]).pid

    dispatcher.connect('init', configure_keyboard)
    dispatcher.connect('quit', unconfigure_keyboard)

def configure_keyboard(dispatcher=None):
    configuration = {
            '/org/onboard/auto-show/enabled'            : 'true',
            '/org/onboard/layout'                       : "'Phone'",
            '/org/onboard/theme'                        : "'Ambiance'",
            '/org/onboard/theme-settings/color-scheme'  : "'/usr/share/onboard/themes/Aubergine.colors'",
            '/org/onboard/window/landscape/dock-expand' : 'false',
            }

    write_dconf_settings(configuration, logger)

def unconfigure_keyboard(dispatcher=None):
    write_dconf_settings({'/org/onboard/use-system-defaults':'true'},logger)
    pid = is_running('onboard')
    if pid:
        execute(['kill', str(pid)])

