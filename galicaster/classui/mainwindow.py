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
import gst
import logging

from galicaster import __version__
from galicaster.classui import message

log = logging.getLogger()

class GCWindow(gtk.Window):
    """
    GUI for the Welcoming - Distribution Screen
    """
    __gtype_name__ = 'GCWindow'
    __def_win_size__ = (1024, 768)

    def __init__(self, dispatcher=None ):  
        gtk.Window.__init__(self,gtk.WINDOW_TOPLEVEL)
        self.set_size_request(*self.__def_win_size__) #FIXME make it unchangable
        self.set_title("GaliCASTER " + __version__ );        
        self.connect('delete_event', lambda *x: self.on_delete_event())    
        self.dispatcher = dispatcher
        if self.dispatcher:
            self.dispatcher.connect('galicaster-quit',self.close)
        

    def start(self):
        self.fullscreen()
        self.is_fullscreen = True
        self.show_all()


    def on_delete_event(self):
        log.debug("Delete Event Received")
        if self.dispatcher:
            self.dispatcher.emit('galicaster-quit')


    def close(self, signal ):
        text = {"title" : "Galicaster",
                "main" : "Are you sure you want to QUIT? ", 
                }

        buttons = ( gtk.STOCK_QUIT, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
        size = [ self.get_screen().get_width(), self.get_screen().get_height() ]
        warning = message.PopUp(message.WARNING, text, size, 
                                     self, buttons)

        if warning.response in message.POSITIVE:
            log.info("Quit Galicaster")
            if self.dispatcher:
                self.dispatcher.emit('galicaster-notify-quit')
            gst.info("Quit Galicaster")
            gtk.main_quit()
        else:
            log.info("Cancel Quit")


