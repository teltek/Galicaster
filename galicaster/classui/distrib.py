# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/ui/distribui
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.


from gi.repository import Gtk, GdkPixbuf

from galicaster.core import context
from galicaster.classui import get_ui_path, get_image_path
from galicaster.utils.miscellaneous import get_footer
from galicaster.classui.profile import ProfileUI as ListProfile
from galicaster.utils.resize import relabel
from galicaster.classui import message
from galicaster.classui.strip import StripUI

from galicaster.utils.i18n import _

class DistribUI(Gtk.Box):
    """
    GUI for the Welcoming - Distribution Screen
    """
    __gtype_name__ = 'DistribUI'

    def __init__(self):
        Gtk.Box.__init__(self)
        dbuilder= Gtk.Builder()
        dbuilder.add_from_file(get_ui_path('distrib.glade'))
        self.builder = dbuilder
        self.gui = dbuilder
        dbox = dbuilder.get_object("distbox")
        release = dbuilder.get_object("release_label")
        release.set_label(get_footer())

        recorder = dbuilder.get_object("button1")
        manager = dbuilder.get_object("button2")
        quit_button =  dbuilder.get_object("button3")
        shutdown_button =  dbuilder.get_object("button4")

        profile_button = dbuilder.get_object("profile_button")
        self.selected = dbuilder.get_object("selected_profile")
        self.update_selected_profile()

        strip = StripUI(None)
        strip.resize()
        strip.set_logo()
        dbox.pack_start(strip,False,False,0)
        dbox.reorder_child(strip,0)

        #Connect signals
        dispatcher = context.get_dispatcher()
        dispatcher.connect_ui("action-reload-profile", self.update_selected_profile)
        recorder.connect("clicked", self.emit_signal, "action-view-change", 0)
        manager.connect("clicked", self.emit_signal, "action-view-change", 1)
        quit_button.connect("clicked", self.emit_signal, "action-quit")
        shutdown_button.connect("clicked", self.emit_signal, "action-shutdown")
        profile_button.connect("clicked", self.on_profile_button)

        conf = context.get_conf()
        quit_button.set_visible(conf.get_boolean("basic", "quit"))
        shutdown_button.set_visible(conf.get_boolean("basic", "shutdown"))
        self.pack_start(dbox, True, True, 0)

    def on_profile_button(self, origin):
        parent = self.get_toplevel()
        ListProfile(parent)

    def update_selected_profile(self, button = None):
        profile = context.get_conf().get_current_profile()

        if self.selected.get_text() != profile.name:
            self.selected.set_text(_("Profile: {profileName}").format(profileName = profile.name))

    def emit_signal(origin, button, signal, value=None):
        dispatcher = context.get_dispatcher()
        if value != None:
            dispatcher.emit(signal, value)
        else:
            dispatcher.emit(signal)

    def resize(self):
        size = context.get_mainwindow().get_size()

        anchura = size[0]
        k = anchura / 1920.0

        builder= self.builder

        l1 = builder.get_object("reclabel")
        l2 = builder.get_object("mmlabel")
        l3 = builder.get_object("selected_profile")
        i1 = builder.get_object("recimage")
        i2 = builder.get_object("mmimage")
        b1 = builder.get_object("button1")
        b2 = builder.get_object("button2")
        relabel(l1,k*48,True)
        relabel(l2,k*48,True)
        relabel(l3,k*26,True)
        i1.set_pixel_size(int(k*120))
        i2.set_pixel_size(int(k*120))
        b1.set_property("width-request", int(anchura/3.5) )
        b2.set_property("width-request", int(anchura/3.5) )
        b1.set_property("height-request", int(anchura/3.5) )
        b2.set_property("height-request", int(anchura/3.5) )
