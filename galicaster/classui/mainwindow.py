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
"""
UI for the welcoming page
"""
import re
import gtk

from galicaster import __version__
from galicaster.classui import message
from galicaster.classui import get_image_path
from galicaster.utils.shutdown import shutdown as UtilsShutdown

from galicaster.utils.i18n import _

class GCWindow(gtk.Window):
    """
    GUI for the Welcoming - Distribution Screen
    """
    __gtype_name__ = 'GCWindow'

    def __init__(self, dispatcher=None, state=None, size=None, logger=None):  

        gtk.Window.__init__(self,gtk.WINDOW_TOPLEVEL)
        self.full_size = self.discover_size() # Fullscreen size
        self.custom_size = self.full_size
        expr='[0-9]+[\,x\:][0-9]+' # Parse custom size     
        if re.match(expr,size): 
            self.custom_size = [int(a) for a in size.split(re.search('[,x:]',size).group())]
        elif size=="auto":
            logger.info("Default resolution and fullscreen: "+str(self.full_size))
        else:
            logger.warning("Invalid resolution, set default. Should be 'width,height'. "+size)

        if self.custom_size[0]>self.full_size[0]:
            self.custom_size[0]=self.full_size[0]
            logger.warning("Resolution Width is bigger than the monitor, set to monitor maximum")

        if self.custom_size[1]>self.full_size[1]:
            self.custom_size[1]=self.full_size[1]
            logger.warning("Resolution height is bigger than the monitor, set to monitor maximum")

        self.__def_win_size__=(self.custom_size[0],self.custom_size[1])
        self.set_size_request(self.custom_size[0],self.custom_size[1])

        self.set_title(_("GaliCASTER {0}").format(__version__));    
        self.set_decorated(False)
        self.set_position(gtk.WIN_POS_CENTER)
        self.is_fullscreen = (self.custom_size == self.full_size)
        self.logger = logger

        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(get_image_path('galicaster.svg'),48,48)        
        pixbuf = pixbuf.scale_simple(128, 128, gtk.gdk.INTERP_BILINEAR)
        self.set_icon(pixbuf)
        self.connect('delete_event', lambda *x: self.__on_delete_event())    
        self.dispatcher = dispatcher
        if self.dispatcher:
            self.dispatcher.connect('galicaster-quit',self.close)
            self.dispatcher.connect('galicaster-shutdown',self.shutdown)

        self.nbox = gtk.Notebook()
        self.nbox.set_show_tabs(False)
        self.add(self.nbox)


    def start(self):
        """Shifts to fullscreen mode and triggers content resizing and drawing"""
        if self.is_fullscreen:
            self.fullscreen()
        self.resize_childs()
        self.show_all()
        
    def toggle_fullscreen(self, other = None):
        """Allows shifting between full and regular screen mode.
        For development purposes."""
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.unfullscreen()
        else:
            self.is_fullscreen = True
            self.fullscreen()
        self.resize_childs()

    def resize_childs(self):
        """Resize the children upon the main window screen size."""
        nbook = self.get_child()
        current = nbook.get_nth_page(self.get_current_page())
        current.resize()

        for child in nbook.get_children():
            if child is current:
                continue
            child.resize()            

    def get_size(self):
        """Returns the current size of the main window. """
        if self.is_fullscreen:
            return self.full_size
        else:
            return self.custom_size

    def discover_size(self):
        """Retrieves the current size of the window where the application will be shown"""
        size = (1920,1080)
        try:
            root = gtk.gdk.get_default_root_window()
            screen = root.get_screen()
            pos1,pos2,w,h=screen.get_monitor_geometry(0)
            size = [w,h]
        except:
            if self.logger:
                self.logger.error("Unable to get root screen size")
            
        return size
        

    def insert_page(self, page, label, cod):
        """Insert an area on the main window notebook widget"""
        self.nbox.insert_page(page, gtk.Label(label), cod) 

        
    def set_current_page(self, cod):
        """Changes active area"""
        self.nbox.set_current_page(cod)


    def get_current_page(self):
        """Gets the current page id number"""
        return self.nbox.get_current_page()


    def __on_delete_event(self):
        """Emits the quit signal to its childs"""
        if self.logger:
            self.logger.debug("Delete Event Received")
        if self.dispatcher:
            self.dispatcher.emit('galicaster-quit')


    def close(self, signal):
        """Pops up a dialog asking to quit"""
        text = {"title" : _("Quit"),
                "main" : _("Are you sure you want to QUIT? "), 
                }

        buttons = ( gtk.STOCK_QUIT, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
        self.dispatcher.emit("disable-no-audio")
        warning = message.PopUp(message.WARNING, text,
                                self, buttons)
        self.dispatcher.emit("enable-no-audio")

        if warning.response in message.POSITIVE:
            if self.logger:
                self.logger.info("Quit Galicaster")
            if self.dispatcher:
                self.dispatcher.emit('galicaster-notify-quit')
            gtk.main_quit()
        else:
            if self.logger:
                self.logger.info("Cancel Quit")

    def shutdown(self, signal):
        """Pops up a dialog asking to shutdown the computer"""
        text = {"title" : _("Shutdwon"),
                "main" : _("Are you sure you want to SHUTDOWN? "), 
                }

        buttons = ( gtk.STOCK_QUIT, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
        warning = message.PopUp(message.WARNING, text,
                                self, buttons)

        if warning.response in message.POSITIVE:
            if self.logger:
                self.logger.info("Shutdown Galicaster")
            if self.dispatcher:
                self.dispatcher.emit('galicaster-notify-quit')
            UtilsShutdown()
        else:
            if self.logger:
                self.logger.info("Cancel Shutdown")
        
        
