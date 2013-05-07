# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/classui/login
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.
"""
Login Dialog UI
"""

import gtk
import pango
from galicaster.classui.elements.message_header import Header
from galicaster.utils.mhhttpclient import MHUserClient

class LoginDialog(gtk.Window):

    def __init__(self, parent=None, mh_host = None):
        if parent:
            size = parent.get_size()
        else: 
            size = (1920,1080)
        self.size = size
        self.wprop = size[0]/1920.0
        self.hprop = size[1]/1080.0
        self.host = mh_host

        # LEVELS
        # 1 mainbox 2 strip, dialog, buttons 3 icon, textbox 4 question box 5 textbox entrybox 

        #TODO check if Dialog is better
        # Levels 1 & 2
        gtk.Window.__init__(self)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_TOOLBAR)
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.set_skip_taskbar_hint(True)
        self.set_modal(True)
        self.set_accept_focus(True)
        self.set_transient_for(parent)
        self.set_keep_above(True)
        self.set_destroy_with_parent(True)

        if self.size[0]<1300:
            self.set_property('width-request',int(self.size[0]/2))
        else:
            self.set_property('width-request',int(self.size[0]/2.5)) 
        mainbox = gtk.VBox()
        strip = Header(size=size,title="Login")
        dialog = gtk.HBox()
        self.buttons = gtk.HButtonBox()
        self.buttons.set_layout(gtk.BUTTONBOX_SPREAD)
        self.getIn = self.add_button("Login", self.check_login)
        self.getOut = self.add_button("Cancel", self.hide_login)
        self.text = gtk.Label("Authentication needed")# Align and decorate
        # TODO center text on the middle of 2 lines
        self.text.set_justify(gtk.JUSTIFY_CENTER)
        #self.text.set_alignment(0,0.5)        
        self.resize_text(self.text,self.wprop, 28, True)#TODO set bold
        self.resize_text(self.getIn.get_children()[0], self.wprop, 20, False)
        self.resize_text(self.getOut.get_children()[0], self.wprop, 20, False)
        # TODO frame
        frame = gtk.Alignment(0.5,0.5,0.9,0.9)
        frame.add(dialog)
        mainbox.pack_start(strip,False,False,0)
        mainbox.pack_start(self.text,False,True,20)
        mainbox.pack_start(frame,False,False,10)
        mainbox.pack_start(self.buttons,False,False, 20)
        self.add(mainbox)
        
        # Levels 3 & 4 on dialog box
        icon = gtk.Image()
        icon.set_from_icon_name(gtk.STOCK_DIALOG_AUTHENTICATION, gtk.ICON_SIZE_DIALOG) # gtk 2.4 or superior
        icon.set_pixel_size(int(self.wprop*100))
        textbox = gtk.VBox()
        entrybox = gtk.VBox()        
        user = gtk.Label("User:")
        password = gtk.Label("Password:")
        self.resize_text(user, self.wprop, 17, False)
        self.resize_text(password, self.wprop, 17, False)
        textbox.pack_start(user)
        textbox.pack_start(password)
        self.entryUser = gtk.Entry()
        self.entryPass = gtk.Entry()
        self.entryUser.set_width_chars(int(self.wprop*46))
        self.entryPass.set_width_chars(int(self.wprop*46))
        self.entryPass.set_visibility(False)
        entrybox.pack_start(self.entryUser)
        entrybox.pack_start(self.entryPass)
        dialog.pack_start(icon,False,False,20)
        dialog.pack_start(textbox,False,False,20)
        dialog.pack_start(entrybox,False,True,0)
        self.user = None

    def check_login(self, button): # Just check if password has at least char
        user = self.entryUser.get_text()
        password = self.entryPass.get_text()
        result = MHUserClient(self.host, user, password).auth()
        if result:
            self.clear_data() #TODO set user on the UI
            self.user = user
            self.hide()
            return True
        else:
             self.text.set_text("Sorry, authentication failed\nTry again")     
             self.entryPass.set_text("") 
             return False

    def hide_login(self, button=None):
        self.clear_data()
        self.text.set_text("Authentication needed")
        self.hide()
        
    def clear_data(self):
        self.entryUser.set_text('')
        self.entryPass.set_text('')
    
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
        return button
    
    def resize_text(self, element, wprop, fontsize, bold):#Refactorize to classui.utils
        fsize=int(wprop*fontsize)
        chars = int(wprop*26)
        font = "{0}{1}".format(fsize, "px")
        attributes = self.set_font(font)
        element.set_attributes(attributes)
        #element.set_padding(-1,int(wprop*fsize/2.6))
        #element.set_width_chars(chars)

    def set_font(self,description):
        """Asign a font description to a text"""
        alist = pango.AttrList()
        font=pango.FontDescription(description)
        attr=pango.AttrFontDesc(font,0,-1)
        alist.insert(attr)
        return alist
