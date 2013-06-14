# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/classui/selector
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
Base class for creating selector and manager UIs
"""

import gtk
import pango

from galicaster.core import context
from galicaster.classui.elements.message_header import Header

class SelectorUI(gtk.Window):
    
    """
    Main window of Selector. 
    It holds at least 3 tabs, list of options, configuration and confirmation
    """

    def __init__(self, parent=None, size = None):
        if not parent:
            parent = context.get_mainwindow()
        if not size:
            size = context.get_mainwindow().get_size()
        self.size=size
        width = int(size[0]/2.2)
        height = int(size[1]/3.0)

        gtk.Window.__init__(self)
        self.set_title(" ")
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.set_default_size(width,height)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_TOOLBAR)
        #self.set_skip_taskbar_hint(True)
        #self.set_modal(True) # TODO ensure this is neessary
        if parent: # parent is always created?
            #self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
            self.set_transient_for(parent)
            self.set_destroy_with_parent(True)

        strip = Header(size=size, title="Operations")
        self.notebook = gtk.Notebook() # Main object of the selector
        self.notebook.set_show_tabs(False)
        box = gtk.VBox()
        self.add(box)
        box.pack_start(strip, False, True, 0)
        box.pack_start(self.notebook, True, True, 0)

    def add_main_tab(self, label, options):
        tab1 = gtk.Label(label)
        self.append_tab(options,tab1)
        
    def append_tab(self, widget, label):
        """Add a tab with a new edition area"""
        self.notebook.append_page(widget,label)
        self.set_title(label.get_text())
        self.notebook.next_page()

    def remove_tab(self):
        """If configuration tabs are finished or canceled, tab is removed and previous tab recovere"""
        current_num=self.notebook.get_current_page()
        self.notebook.prev_page()
        new_num = self.notebook.get_current_page()

        # TODO transform commented lines into function clean_temp_data f.e.
        #current=self.notebook.get_nth_page(current_num)        
        # For profile selector
        #if current == self.profile:
        #    self.profile = None
        #elif current == self.track:
        #    self.track = None
        new=self.notebook.get_nth_page(new_num)
        self.notebook.remove_page(current_num)        
        text=self.notebook.get_tab_label(new).get_text()
        new.refresh()
        self.set_title(text)
        # Test another sequence if updating is slow
    
    def close(self):
        """Handles UI closure, destroying tabs and updating changes"""
        #TODO eliminates variables and objects 
        self.destroy()          

class MainList(gtk.HBox):
    """
    Main List of a Selector UI
    append_list, append_info and prepare_view have to be defined on each subtype
    """

    def __init__(self, parent=None, size=(1920,1080), info_label = None, additional = False):
        self.superior = parent
        self.size = size
        wprop = size[0]/1920.0
        hprop = size[1]/1080.0
        self.wprop = wprop
        self.hprop = hprop
        gtk.HBox.__init__(self, False, int(wprop*5)) # last is margin

        self.set_border_width(int(wprop*20))
        self.vbox = gtk.VBox(False,0)

        self.buttons = gtk.VButtonBox()
        self.buttons.set_layout(gtk.BUTTONBOX_START)
        self.buttons.set_spacing(int(wprop*5))

        sidebox = gtk.VBox(False,0)  
        #sidebox.set_size_request(int(wprop*750),-1) # TODO use simillar size to Chooser

        self.pack_start(self.vbox, True, True, 0)
        sidebox.pack_start(self.buttons, False, False, int(hprop*10))
        self.pack_start(sidebox,False,False,int(wprop*15))
        

    def add_button(self, text, connection, end=False):
        """Adds an action button to the right side of the Box"""
        k1 = self.wprop
        button = gtk.Button(text)
        button.set_property("width-request", int(k1*150))
        button.set_property("height-request", int(k1*50))
        label = button.get_children()[0]
        modification = str(int(self.hprop*20))
        label.modify_font(pango.FontDescription(modification))
        if not end:
            self.buttons.pack_start(button)
        else:
            self.buttons.pack_end(button)
        button.connect("clicked",connection)
        button.set_can_focus(False)
        return button
        
    def close(self,button=None):
        """Leaves and close the profile tab"""
        self.superior.close()
