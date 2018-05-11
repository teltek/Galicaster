# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/script_button
#
# Copyright (c) 2018, Teltek Video Research <galicaster@teltek.es>

from gi.repository import Gtk

from galicaster.core.core import PAGES
from galicaster.core import context
from galicaster.utils.i18n import _

logger = context.get_logger()
conf = context.get_conf()

def init(**kwargs):
    """
    """
    dispatcher = context.get_dispatcher()

    dispatcher.connect('init', configure_layout)

def configure_layout(element=None):
    # Add network button
    mw = context.get_mainwindow()
    name = conf.get('script_button', 'name', "Script")
    icon = conf.get('script_button', 'icon', "gtk-properties")
    network_button = __create_network_button(name, icon)
    network_button = mw.insert_element_with_position(network_button,PAGES['DIS'],"box2", "add", 0)

def __create_network_button(name, icon):
    logger.info("Creating network button")

    button = Gtk.Button()
    hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    button.add(hbox)

    icon = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.DIALOG)
    l1 = Gtk.Label(_(name))
    l1.get_style_context().add_class('label_medium')
    l1.set_margin_start(10)
    l1.set_margin_end(10)

    hbox.pack_end(icon,True,True,0)
    hbox.pack_end(l1,False,False,0)
    button.connect("clicked", handler_script_button)

    return button

def handler_script_button(element=None, element2=None):
    import subprocess
    bashCommand = conf.get('script_button', 'command')
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
