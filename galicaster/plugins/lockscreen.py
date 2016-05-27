# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/lockscreen
#
# Copyright (c) 2016, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
"""

from galicaster.classui import message
from galicaster.core import context

from galicaster.utils.systemcalls import write_dconf_settings
from galicaster.utils.i18n import _


def init():
    global conf, logger, bindings, default_bindings
    dispatcher = context.get_dispatcher()
    logger = context.get_logger()
    conf = context.get_conf()    
    dispatcher.connect('init', show_msg)

    bindings = conf.get_json('lockscreen', 'bindings')
    default_bindings = conf.get_json('lockscreen', 'defaultbindings')


def show_msg(element=None):
    global logger, bindings
    logger.info("On init: write dconf bindings")
    write_dconf_settings(bindings, logger, logaserror=False)

    text = {"title" : _("Lock screen"),
            "main" : _("Please insert the password")}

    logger.info("Galicaster locked")
    message.PopUp(message.LOCKSCREEN, text,
                            context.get_mainwindow(),
                            None, response_action=on_unlock, close_on_response=False)


def on_unlock(self, response=None, **kwargs):
    global conf, logger, default_bindings
    
    builder = kwargs.get('builder', None)
    popup = kwargs.get('popup', None)
    
    lentry = builder.get_object("unlockpass")
    if conf.get('lockscreen', 'password') == lentry.get_text():
        logger.info("Galicaster unlocked")
        popup.dialog_destroy()
        write_dconf_settings(default_bindings, logger, logaserror=False)
    else:
        lmessage = builder.get_object("lockmessage")
        lmessage.set_text("Wrong password")
