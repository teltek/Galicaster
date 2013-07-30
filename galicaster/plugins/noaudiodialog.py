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

import gtk
import pango
from galicaster.core import context
from galicaster.classui import get_ui_path, get_image_path
from galicaster.classui.elements.message_header import Header

no_audio = False
no_audio_dialog = None
focus_is_active = True
keep_hidden = False


def init():
    global focus_is_active

    dispatcher = context.get_dispatcher()
    conf = context.get_conf()

    focus_is_active = not conf.get_boolean('basic','admin')

    dispatcher.connect('audio-mute', warning_audio)
    dispatcher.connect('audio-recovered', warning_audio_destroy)
    dispatcher.connect('galicaster-status', event_change_mode)
    dispatcher.connect('reload-profile', clear_data_and_check)
    dispatcher.connect('restart_preview', deactivate_hidden_and_check)
    dispatcher.connect('starting-record', deactivate_hidden_and_check)
    dispatcher.connect('upcoming-recording', deactivate_hidden_and_check)

def activate_hidden(button, dialog):
    """
    Activates Keep Hidden feature and hides dialog
    """
    global keep_hidden
    keep_hidden = True
    dialog.hide() 

def deactivate_hidden_and_check(element=None):
    """
    When a signal is received, deactivate the keep hidden feature and shows dialog if necessary
    """
    global no_audio
    global no_audio_dialog
    global focus_is_active
    global keep_hidden
    keep_hidden = False

    if focus_is_active and no_audio:
        if no_audio_dialog:
            pass
        else:
            no_audio_dialog = create_ui()
        no_audio_dialog.show() 
    return True

def clear_data_and_check(element=None):
    global no_audio
    no_audio = False
    deactivate_hidden_and_check()
    return True


def warning_audio(element=None):
    """
    Called up on a new mute signal, shows the dialog if necessary
    """
    global no_audio
    global no_audio_dialog
    global focus_is_active
    global keep_hidden
    no_audio = True
    if focus_is_active and not keep_hidden:
        if no_audio_dialog:
            pass
        else:
            no_audio_dialog = create_ui()
        no_audio_dialog.show() 
    return True

def warning_audio_destroy(element=None):
    """
    If the audio dialog is displayed, hides it
    """
    global no_audio
    global no_audio_dialog
    no_audio = False
    try:
        assert no_audio_dialog
    except:
        return True           
    no_audio_dialog.hide()
    return True      

def event_change_mode(orig, old_state, new_state):
    """
    On changing mode, if the new area is right, shows dialog if necessary
    """
    global no_audio
    global no_audio_dialog
    global focus_is_active

    if new_state == 0: 
        focus_is_active = True
        if no_audio:
            warning_audio()

    if old_state == 0:
        focus_is_active = False
        if no_audio and no_audio_dialog:
            no_audio_dialog.hide()

def refuse_focus(signal, data):
    data.grab_focus()
    

def create_ui():
    """
    Creates the No Audio Dialog interface
    """
    parent =  context.get_mainwindow().get_toplevel()
    ui = gtk.Dialog("Warning", parent)

    #Properties
    ui.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_TOOLBAR)
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
    ui.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    ui.action_area.set_layout(gtk.BUTTONBOX_SPREAD)

    #Buttons
    conf = context.get_conf()
    keep_closed_feature = conf.get_boolean('audio','keepclosed') or False
    if keep_closed_feature:
        keep_button = ui.add_button("Keep Closed",1)
        keep_button.connect("clicked",activate_hidden, ui)
    hide_button = ui.add_button("Close",2)
    hide_button.connect("clicked",lambda l:ui.hide())
    for child in ui.action_area.get_children():
        child.set_property("width-request", int(wprop*170) )
        child.set_property("height-request", int(hprop*70) )
        child.set_can_focus(False)

    #Taskbar with logo
    strip = Header(size=size, title="Warning")
    ui.vbox.pack_start(strip, False, True, 0)
    strip.show()

    #Labels
    label1 = gtk.Label("No Audio!!")
    label2 = gtk.Label("Pick up the microphone\nPress the mute button")
    desc1 = "bold " + str(int(hprop*64))+"px"
    desc2 = "bold " + str(int(hprop*24))+"px"
    font1=pango.FontDescription(desc1)
    font2=pango.FontDescription(desc2)
    label1.modify_font(font1)
    label2.modify_font(font2)
    label1.set_alignment(0.5,0.5)
    label2.set_alignment(0.5,0.5)
    # Warning icon
    box = gtk.HBox(spacing=0) # between image and text
    image = gtk.Image()
    image.set_from_icon_name(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
    image.set_pixel_size(int(wprop*80))
    box.pack_start(image,True,True,0)
    box.pack_start(label1,True,True,0)  
    image.show()
    box.show()
    #ui.vbox.pack_start(box, True, False, int(hprop*5))
    another_box = gtk.VBox(spacing=int(hprop*20))
    another_box.pack_start(box, True, False, 0)
    another_box.pack_start(label2, True, False, 0)
    another_box.show()
    ui.action_area.set_property('spacing',int(hprop*20))
    ui.vbox.pack_start(another_box, False, False, 10)
    #ui.vbox.pack_start(box, True, False, 0)
    #ui.vbox.pack_start(label2, True, False, 0)
    resize_buttons(ui.action_area,int(wprop*25),True)
    ui.vbox.set_child_packing(ui.action_area, True, True, int(hprop*25), gtk.PACK_END)
    
    label1.show()
    label2.show()
    return ui

def set_font(description):
        """Asign a font description to a text"""
        alist = pango.AttrList()
        font=pango.FontDescription(description)
        attr=pango.AttrFontDesc(font,0,-1)
        alist.insert(attr)
        return alist

def resize_buttons(area, fsize, equal = False):    
        """Adapts buttons to the dialog size"""
        font = set_font("bold "+str(fsize)+"px")
        for button in area.get_children():
            for element in button.get_children():
                if type(element) == gtk.Label:
                    element.set_attributes(font)
                    if equal:
                        element.set_padding(-1,int(fsize/2.6))
