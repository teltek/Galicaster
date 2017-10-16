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
import re
from gi.repository import Gtk
from galicaster.core.core import PAGES_LOADED

conf = None
logger = None

def init():
    global conf, logger
    dispatcher = context.get_dispatcher()
    logger = context.get_logger()
    conf = context.get_conf()
    dispatcher.connect('init', show_msg)
    dispatcher.connect('record-finished', show_msg)

def show_msg(element=None, *args):
    text = {"title" : _("Lock screen"),
            "main" : _("Please insert the password")}

    show = []
    auth_method = conf.get_choice('lockscreen', 'authentication', ['basic', 'ldap'], 'basic')
    quit_button = conf.get_boolean('lockscreen','enable_quit_button')

    if auth_method == "ldap":
        show = ["username_label","username_entry"]
        text = {"title" : _("Lock screen"),
            "main" : _("LDAP authentication")}
    if quit_button:
        show.append("quitbutton")

    if not args:
        for page in PAGES_LOADED:
            button = show_buttons(page)
            if button is not None:
                button.connect("clicked", lock, text, show)

        #FIXME Change behaviour of stop dialog, to avoid shaded lockscreen
        recorderui =  context.get_mainwindow().nbox.get_nth_page(0)
        recorderui.close_before_response_action = True

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
        logger.error("View has not been loaded. Page id: {}, exception: {}".format(ui, str(error)))
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
    global conf, logger, builder

    builder = kwargs.get('builder', None)
    popup = kwargs.get('popup', None)

    lentry = builder.get_object("unlockpass")
    userentry = builder.get_object("username_entry")

    auth_method = conf.get_choice('lockscreen', 'authentication', ['basic', 'ldap'], 'basic')

    if  (auth_method == "basic" and conf.get('lockscreen', 'password') == lentry.get_text()) \
        or (auth_method == "ldap" and connect_ldap(userentry.get_text(),lentry.get_text())):
        logger.info("Galicaster unlocked")
        popup.dialog_destroy()

    elif auth_method == "basic":
        set_error_text("Wrong password")

def set_error_text(error_text):
    lmessage = builder.get_object("lockmessage")
    lmessage.set_text(error_text)
    lmessage.show()


def connect_ldap(user,password):
    ldapserver = conf.get("lockscreen","ldapserver")
    ldapserverport = conf.get("lockscreen","ldapserverport")
    ldapusertype = conf.get("lockscreen","ldapusertype", "cn")
    ldap_advanced_bind = conf.get_boolean("lockscreen", "ldap_advanced_bind")

    if ldap_advanced_bind:
        bind_dn = conf.get("lockscreen","search_dn")
        bind_password = conf.get("lockscreen","search_password")
        search_filter = conf.get("lockscreen","filter")
        base_dn = conf.get("lockscreen","base_dn")
        memberof = conf.get("lockscreen", "group")

    else:
        ldapou_list = conf.get_list("lockscreen","ldapou")
        ldapdc_list = conf.get_list("lockscreen","ldapdc")
        ldapOU = ""
        for x in ldapou_list:
            ldapOU = "{},ou={}".format(ldapOU, x)
        ldapDC = ""
        for x in ldapdc_list:
            ldapDC = "{},dc={}".format(ldapDC, x)
        bind_dn = "{}={}{}{}".format(ldapusertype, user, ldapOU, ldapDC)
        bind_password = password


    try:
        fullserver = "{}:{}".format(ldapserver,ldapserverport)
        logger.debug("Trying to connect to LDAP server with dn: {}".format(bind_dn))
        l = ldap.initialize(fullserver)
        l.protocol_version = ldap.VERSION3
        l.simple_bind_s(bind_dn, bind_password)

        if ldap_advanced_bind:
            if not search_filter == "":
                mappings = {'user' : user}
                search_filter = re.sub(r'{\w+}', '', search_filter.format(**mappings))
            else:
                search_filter = "(&({}={})(memberof={}))".format(ldapusertype, user, memberof)
            logger.debug("Searching in LDAP server with filter: {}".format(search_filter))
            result = l.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter, [])

            if not result:
                logger.warning("User {} not found".format(user))
                set_error_text("User not found")
                return False

            dn = result[0][0]
            l.simple_bind_s(dn, password)
        logger.info("Connect to LDAP server success with username: {}".format(user))

    except ldap.LDAPError as error:
        if type(error) == ldap.INVALID_CREDENTIALS:
            logger.warning("Can't connect to to LDAP server {} - {}".format(fullserver,error))
        else:
            logger.error("Can't connect to to LDAP server {} - {}".format(fullserver,error))
        set_error_text(error[0]["desc"])
        return False

    finally:
        l.unbind()

    return True
