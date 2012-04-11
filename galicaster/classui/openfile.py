# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/ui/mainwindow
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
import logging

from galicaster import __version__
from galicaster.core import context
from galicaster.mediapackage import deserializer
from galicaster.classui import get_ui_path

log = logging.getLogger()

def select_file(mainwindow):

    gui = gtk.Builder()
    gui.add_from_file(guifile)
    gui.add_from_file(get_ui_path("openfile.glade"))
    dialog = gui.get_object("dialog") 
    dialog.set_transient_for(mainwindow)
    response = dialog.run()    
    if response == 1 :
        filename = dialog.get_filename()
        # print filename
        dialog.destroy()          
        return filename
    else:
        dialog.destroy()
        return None           

        
def open_file(filename): # REVIEW name, also checks if we should import it to the main repository
    """
    Open a single file for playing and editing
    """
        
    # shift to player if neccessary
    log.info("Opening a file")
    context.get_dispatcher().emit("change-mode",2) # FIXME import PLA=2
    
    # open dialog
    if path.isdir(filename):
        uri=path.join(filename,"manifest.xml")
    else:
        uri=path.join(path.abspath(filename),"manifest.xml")
        
    if not path.isfile(uri):            
        log.warn("Manifest doesnt exist")
        # raise TypeError, "Manifest doesnt exist"
        # try to play wathever it is (2 videos and 1 audio)
    else:
        mp=deserializer.fromXML(uri)
        context.get_dispatcher().emit("play-list", mp)
