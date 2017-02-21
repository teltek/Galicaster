# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/noaudiodialog
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

"""
Plugin that shows a Dialog when audio is muted or too low.
The dialog is shown in the following circunstances combine: the plugin is active, there is an audio input, the audio level is lower than the threshold, the page has focus and the dialog wasnt blocked or closed
In case the focus is recovered the dialog may be shown again.
The dialog blockade is cancelled when the profile is reloaded or changed and when a recording starts.
"""

from gi.repository import Gtk, Gdk
from gi.repository import Pango
from galicaster.core import context
from galicaster.classui.elements.message_header import Header
from threading import Lock

from galicaster.utils.i18n import _

lock = Lock()

no_audio = False
no_audio_dialog = None
focus_is_active = True
keep_hidden = False
old_keep_hidden = False
was_shown = False

def init():

    global focus_is_active
    global no_audio_dialog

    dispatcher = context.get_dispatcher()
    conf = context.get_conf()
    no_audio_dialog = create_ui()

    focus_is_active = not conf.get_boolean('basic','admin')

    dispatcher.connect('audio-mute', warning_audio_show)
    dispatcher.connect('audio-recovered', warning_audio_hide)
    dispatcher.connect('view-changed', event_change_mode)
    dispatcher.connect('action-reload-profile', clear_data_and_check)
    dispatcher.connect('recorder-starting', deactivate_hidden_and_check)
    dispatcher.connect('recorder-upcoming-event', deactivate_hidden_and_check)
    dispatcher.connect('action-audio-disable-msg', force_hide)
    dispatcher.connect('action-audio-enable-msg', disable_force_hide)

def force_hide(element=None):
    global no_audio_dialog
    global was_shown
    global keep_hidden
    global old_keep_hidden

    with lock:
        was_shown = no_audio_dialog.get_visible()
        old_keep_hidden = keep_hidden
        keep_hidden = True
        __check_dialog()

def disable_force_hide(element=None):
    global keep_hidden
    global old_keep_hidden
    global was_shown

    with lock:
        keep_hidden = old_keep_hidden
        if was_shown:
            __check_dialog()

def __check_dialog():

    global no_audio_dialog
    global keep_hidden
    global focus_is_active
    global no_audio

    if not keep_hidden and no_audio and focus_is_active:
        no_audio_dialog.show()
    else:
        no_audio_dialog.hide()

def activate_hidden(button, dialog):
    """
    Activates Keep Hidden feature and hides dialog
    """
    global keep_hidden
    with lock:
        keep_hidden = True
        __check_dialog()


def deactivate_hidden_and_check(element=None):
    """
    When a signal is recived, deactivate the keep hidden feature and shows dialog if necessary
    """

    global keep_hidden

    with lock:
        keep_hidden = False
        __check_dialog()

    return True


def clear_data_and_check(element=None):

    global no_audio
    no_audio = False
    with lock:
        __check_dialog()

    return True


def warning_audio_show(element=None):
    """
    Called up on a new mute signal, shows the dialog if necessary
    """
    global no_audio

    with lock:
        no_audio = True
        __check_dialog()

    return True


def warning_audio_hide(element=None):
    """
    If the audio dialog is displayed, hides it
    """
    global no_audio

    with lock:
        no_audio = False
        __check_dialog()

    return True


def event_change_mode(orig, old_state, new_state):
    """
    On changing mode, if the new area is right, shows dialog if necessary
    """

    global focus_is_active

    if new_state == 0:
        with lock:
            focus_is_active = True
            __check_dialog()

    if old_state == 0:
        with lock:
            focus_is_active = False
            __check_dialog()


def refuse_focus(signal, data):
    data.grab_focus()


def create_ui():
    """
    Creates the No Audio Dialog interface
    """
    parent =  context.get_mainwindow().get_toplevel()
    ui = Gtk.Dialog("Warning", parent)

    #Properties
    ui.set_type_hint(Gdk.WindowTypeHint.TOOLBAR)
    ui.set_skip_taskbar_hint(True)
    ui.set_modal(False)
    ui.set_accept_focus(False)
    ui.set_destroy_with_parent(True)


    size = parent.get_size()
    ui.set_property('width-request',int(size[0]/3))
    if size[0] < 1300:
        ui.set_property('width-request',int(size[0]/2.3))
    wprop = size[0]/1920.0
    hprop = size[1]/1080.0
    ui.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
    ui.action_area.set_layout(Gtk.ButtonBoxStyle.SPREAD)

    #Buttons
    conf = context.get_conf()
    keep_closed_feature = conf.get_boolean('audio','keep_closed') or False
    if keep_closed_feature:
        keep_button = ui.add_button("Keep Closed",1)
        keep_button.connect("clicked",activate_hidden, ui)
    hide_button = ui.add_button(_("Close"),2)
    hide_button.connect("clicked",lambda l:ui.hide())
    for child in ui.action_area.get_children():
        child.set_property("width-request", int(wprop*170) )
        child.set_property("height-request", int(hprop*70) )
        child.set_can_focus(False)

    #Taskbar with logo
    strip = Header(size=size, title=_("Warning"))
    ui.vbox.pack_start(strip, False, True, 0)
    strip.show()

    #Labels
    label1 = Gtk.Label(label=_("No Audio!!"))
    label2 = Gtk.Label(label=_("Pick up the microphone\nPress the mute button"))
    desc1 = "bold " + str(int(hprop*64))+"px"
    desc2 = "bold " + str(int(hprop*24))+"px"
    font1=Pango.FontDescription(desc1)
    font2=Pango.FontDescription(desc2)
    label1.modify_font(font1)
    label2.modify_font(font2)
    label1.set_alignment(0.5,0.5)
    label2.set_alignment(0.5,0.5)
    # Warning icon
    box = Gtk.HBox(spacing=0) # between image and text
    image = Gtk.Image()
    image.set_from_icon_name(Gtk.STOCK_DIALOG_WARNING, Gtk.IconSize.DIALOG)
    image.set_pixel_size(int(wprop*80))
    box.pack_start(image,True,True,0)
    box.pack_start(label1,True,True,0)
    image.show()
    box.show()
    #ui.vbox.pack_start(box, True, False, int(hprop*5))
    another_box = Gtk.VBox(spacing=int(hprop*20))
    another_box.pack_start(box, True, False, 0)
    another_box.pack_start(label2, True, False, 0)
    another_box.show()
    ui.action_area.set_property('spacing',int(hprop*20))
    ui.vbox.pack_start(another_box, False, False, 10)
    #ui.vbox.pack_start(box, True, False, 0)
    #ui.vbox.pack_start(label2, True, False, 0)
    resize_buttons(ui.action_area,int(wprop*25),True)
    ui.vbox.set_child_packing(ui.action_area, True, True, int(hprop*25), Gtk.PackType.END)

    label1.show()
    label2.show()
    return ui

def resize_buttons(area, fsize, equal = False):
        """Adapts buttons to the dialog size"""
        font = Pango.FontDescription("bold "+str(fsize)+"px")
        for button in area.get_children():
            for element in button.get_children():
                if type(element) == Gtk.Label:
                    element.modify_font(font)
                    if equal:
                        element.set_padding(-1,int(fsize/2.6))
