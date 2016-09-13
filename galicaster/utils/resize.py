# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/readable
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

from gi.repository import Pango
from gi.repository import Gtk
from galicaster.core import context

def relabel(label,size,bold):
    if bold:
        modification = "bold "+str(size)
    else:
        modification = str(size)
    label.modify_font(Pango.FontDescription(modification))


def relabel_updating_font(label,size,bold):
    if bold:
        modification = "bold "+str(size)
    else:
        modification = str(size)
    font = Pango.FontDescription(modification)
    label.modify_font(font)
    return font

def resize_button(button,**kwargs):
    try:
        image = button.get_children()
        if type(image[0]) == Gtk.Image:
            image[0].set_pixel_size(int(kwargs.get('size_image',None)))
        elif type(image[0]) == Gtk.Box:
            for element in image[0].get_children():
                if type(element) == Gtk.Image:
                    element.set_pixel_size(int(kwargs.get('size_box',None)))
                if type(element) == Gtk.Label:
                    relabel(image[0],kwargs.get('size_label',None),False)
        elif type(image[0]) == Gtk.VBox:
            for element in image[0].get_children():
                if type(element) == Gtk.Image:
                    element.set_pixel_size(int(kwargs.get('size_vbox',None)))
        else:
            relabel(image[0],kwargs.get('size_label',None),False)
    except Exception as exc:
        logger = context.get_logger()
        logger.debug(exc)

    return button
