# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/script_button
#
# Copyright (c) 2018, Teltek Video Research <galicaster@teltek.es>

import json

from gi.repository import Gtk

from galicaster.core.core import PAGES
from galicaster.core import context
from galicaster.utils.i18n import _

logger = context.get_logger()
conf = context.get_conf()

def init(**kwargs):
    """
    """
    buttons_conf = conf.get_section('script_button')
    buttons = []
    for name, button_conf in buttons_conf.iteritems():
        button_conf = json.loads(button_conf)
        buttons.append(ScriptButton(button_conf['name'], button_conf['icon'], button_conf['command']))

class ScriptButton:
    def __init__(self, name, icon, command):
        self.name = name
        self.icon = icon
        self.command = command
        dispatcher = context.get_dispatcher()
        dispatcher.connect('init', self.__configure_layout)

    def __configure_layout(self, element=None):
        # Add button
        mw = context.get_mainwindow()
        button = self.__create_button(self.name, self.icon)
        button = mw.insert_element_with_position(button, PAGES['DIS'], "box2", "add", 0)

    def __create_button(self, name, icon):
        logger.info("Creating button {}".format(name))

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
        button.connect("clicked", self.__handler_script_button)

        return button

    def __handler_script_button(self, element=None, element2=None):
        import subprocess
        process = subprocess.Popen(self.command.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
