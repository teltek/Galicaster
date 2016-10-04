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

from galicaster.utils.i18n import _

import ldap
from gi.repository import Gtk
from galicaster.core.core import PAGES

conf = None
logger = None

def init():
    global conf, logger
    dispatcher = context.get_dispatcher()
    logger = context.get_logger()
    conf = context.get_conf()
    dispatcher.connect('init', show_msg)

def show_msg(element=None):
    buttonDIS = show_buttons(PAGES['DIS'])
    buttonREC = show_buttons(PAGES['REC'])
    buttonMMA = show_buttons(PAGES['MMA'])

    text = {"title" : _("Lock screen"),
            "main" : _("Please insert the password")}

    show = []
    auth_method = conf.get_choice('lockscreen', 'authentication', ['basic', 'ldap'], 'basic')
    quit_button = conf.get_boolean('lockscreen','quit')

    if auth_method == "ldap":
        show = ["username_label","username_entry"]
        text = {"title" : _("Lock screen"),
            "main" : _("LDAP authentication")}
    if quit_button:
        show.append("quitbutton")

    if buttonDIS is not None:
        buttonDIS.connect("clicked",lock,text,show)
    if buttonREC is not None:
        buttonREC.connect("clicked",lock,text,show)
    if buttonMMA is not None:
        buttonMMA.connect("clicked",lock,text,show)

    lock(None,text,show)

def lock(element,text,show):
    message.PopUp(message.LOCKSCREEN, text,
                            context.get_mainwindow(),
                            None, response_action=on_unlock, close_on_response=False,show=show,close_parent=True)
    logger.info("Galicaster locked")

def show_buttons(ui):
    try:
        builder = context.get_mainwindow().nbox.get_nth_page(ui).gui
    except Exception as error:
        logger.debug("The view not exist: "+error)
        return None

    box = builder.get_object("box2")
    button = Gtk.Button()
    hbox = Gtk.Box()
    button.add(hbox)
    label = Gtk.Label("Lockscreen")
    label.set_padding(10,10)
    icon = Gtk.Image().new_from_icon_name("gtk-dialog-authentication",3)
    hbox.pack_start(label,True,True,0)
    hbox.pack_start(icon,True,True,0)
    box.pack_start(button,True,True,0)
    box.reorder_child(button,0)
    box.set_spacing(5)
    box.show_all()
    return button


def on_unlock(*args, **kwargs):
    global conf, logger

    builder = kwargs.get('builder', None)
    popup = kwargs.get('popup', None)

    lentry = builder.get_object("unlockpass")
    userentry = builder.get_object("username_entry")

    auth_method = conf.get_choice('lockscreen', 'authentication', ['basic', 'ldap'], 'basic')

    if  (auth_method == "basic" and conf.get('lockscreen', 'password') == lentry.get_text()) \
        or (auth_method == "ldap" and connect_ldap(userentry.get_text(),lentry.get_text())):
        logger.info("Galicaster unlocked")
        popup.dialog_destroy()

    else:
        lmessage = builder.get_object("lockmessage")
        lmessage.set_text("Wrong username/password")
        lmessage.show()


def connect_ldap(user,password):
    ldapserver = conf.get("lockscreen","ldapserver")
    ldapserverport = conf.get("lockscreen","ldapserverport")
    ldapou_list = conf.get_list("lockscreen","ldapou")
    ldapdc_list = conf.get_list("lockscreen","ldapdc")
    ldapusertype = conf.get_choice("lockscreen","ldapusertype", ["cn", "uid"], "cn")

    ldapOU = ""
    for x in ldapou_list:
        ldapOU = "{},ou={}".format(ldapOU, x)

    ldapDC = ""
    for x in ldapdc_list:
        ldapDC = "{},dc={}".format(ldapDC, x)

    try:
        fullserver = "{}:{}".format(ldapserver,ldapserverport)
        dn = "{}={}{}{}".format(ldapusertype, user, ldapOU, ldapDC)
        logger.debug("Trying to connect to LDAP server with dn: {}".format(dn))
        l = ldap.initialize(fullserver)
        l.protocol_version = ldap.VERSION3
        l.simple_bind_s(dn, password)
        logger.info("Connect to LDAP server success with username: {}".format(user))
    except Exception as error:
        logger.error("Can't connect to to LDAP server {} - {}".format(fullserver,error))
        return False
    return True
