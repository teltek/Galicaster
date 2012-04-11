# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/ui/about
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


from os import path
import gtk

from galicaster.core import context
from galicaster.classui import get_ui_path

class AboutMsg(gtk.Widget):
    """
    GUI for the Welcoming - Distribution Screen
    """
    __gtype_name__ = 'AboutMessage'
    
    def __init__(self, parent=None ):  
        gui = gtk.Builder()
        gui.add_from_file(get_ui_path('about.glade'))
        dialog = gui.get_object("dialog")
        dialog.set_transient_for(parent)        

        response = dialog.run()
        if response:
            dialog.destroy()
        else:
            dialog.destroy()
