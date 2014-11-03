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
