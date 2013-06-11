1# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/classui/strip
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.
"""
Top bar widget including back to previous page button and Galicaster logo
"""

import gtk

from galicaster.core import context
from galicaster.classui import get_image_path
from galicaster.utils.resize import relabel
from galicaster.classui.about import GCAboutDialog

class StripUI(gtk.VBox):
    """
    GUI for the Welcoming - Distribution Screen
    """
    __gtype_name__ = 'StripUI'
    
    def __init__(self, back_page, uitype=0, auth=False, text =""):  
        """
        Creates a top bar widget with the Galicaster Logo.
        If a back_page is provided - the tab number on the Core notebook wiget - it will show a back to the previous page button. 
        UItype=0 Distrib 1 Media manager, 2 Recorder, 3 Recorder blocked
        Authentication includes user and logout icon
        """
        gtk.VBox.__init__(self)

        self.UItype = uitype
        self.handlers = {}
        self.back_page = back_page
        self.text = text

        self.createBUI( uitype, auth )

        if uitype not in [0, 3]:
            self.handlers[self.previous] = self.previous.connect("clicked", self.emit_signal, 
                                                                 "change-mode")
            
        self.handlers[self.about]=self.about.connect("button-press-event", self.show_about_dialog)
        self.show_all()

    def createBUI(self, uitype=0, authentication=False):
        #UI type 0 Media manager
        #UI type 1 Distribution
        #UI type 2 Recorder

        self.logos = []
        self.buttons = []
        self.labels = []
        self.aligns = []
        self.events = []

        align = gtk.Alignment(0.5, 0.5, 1.0, 1.0) # TODO replace scale for padding
        if uitype < 2:
            self.aligns += [(align, 52, 20, 54)]
        else: 
            self.aligns += [(align, 9, 20, 54)]
        self.pack_start(align,True, True, 0) # TODO set padding resized
        
        table = gtk.VBox()
        align.add(table)
        
        line1 = gtk.HButtonBox()
        line2 = gtk.HBox()
        line3 = gtk.HButtonBox()
        #line1.set_layout(gtk.BUTTONBOX_CENTER)
        line3.set_layout(gtk.BUTTONBOX_END)

        if uitype not in [0, 3]:
            previous = gtk.Button()
            previous.set_can_focus(False)
            image = gtk.Image()
            image.set_from_icon_name("gtk-go-back-ltr", gtk.ICON_SIZE_DND)
            image.set_pixel_size(50)            
            previous.set_image(image)
            self.buttons += [(previous,220,60)]
            self.events += [previous]
            self.previous = previous
        else:
            #TODO eventbox for handler
            logo2 = gtk.Image()
            logo2_file = 'teltek.svg'
            self.logos += [(logo2, logo2_file)]

        #TODO resize button     
        about = gtk.EventBox()
        self.events += [about]
        logo = gtk.Image()
        logo_file = 'logo.svg'
        self.logos += [(logo, logo_file)]

        # TODO only create if login
        user = gtk.HBox()
        name= gtk.Label("LOGIN")
        name.set_justify(gtk.JUSTIFY_LEFT)
        self.labels = [(name,20)]
        image2 = gtk.Image()
        image2.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_DND)
        icon = gtk.Button()
        icon.set_can_focus(False)
        icon.set_image(image2)
        icon.set_focus_on_click(False)
        icon.set_relief(gtk.RELIEF_NONE)
        
        icon.check_resize()
        #self.buttons += [(icon, 50, 50)]
        #user.pack_start(name, True, True, 0)
        #user.pack_start(icon, True, True, 0)
           
        self.about = about
        self.user = name
        self.logout = icon
        self.padding = align

        align_left = gtk.Alignment(0.0, 0.5, 0, 0)
        align_left.add(logo2 if uitype in [0, 3] else previous)
        self.aligns += [(align_left,5,5,0)]
        line2.pack_start(align_left, True, True, 0) # TODO always add logo if not previous
        
        if uitype > 1:
            align_center_top = gtk.Alignment(0.5, 1.0, 0, 0)
            align_center_bottom = gtk.Alignment(0.5, 0.5, 0, 0)
            clock = gtk.Frame()
            clock.set_label_align(0.0, 0.5)
            clock.set_shadow_type(gtk.SHADOW_ETCHED_IN)
            clockLabel = gtk.Label("00:00")
            clock.add(clockLabel)
            align_center_top.add(clock)
            self.clock=clockLabel
            self.labels += [(clockLabel,25)]
            line1.pack_start(align_center_top, False, False, 0)
            self.status = gtk.EventBox()
            align_center_bottom.add(self.status)
            line2.pack_start(align_center_bottom, False, False, 0)
            self.events += [self.status]
        elif uitype == 1:
            titleLabel = gtk.Label(self.text)
            self.labels += [(titleLabel,40)]
            line2.pack_start(titleLabel, False, False, 0)
            line2.reorder_child(titleLabel,1)

        align_right = gtk.Alignment(1.0, 0.5, 0, 0)
        align_right.add(logo)
        self.aligns += [(align_right,5,5,0)]
        line2.pack_start(align_right, True, True, 0)

        line3.pack_end(user, True, True, 0)
        table.pack_start(line1, False, False, 0)
        table.pack_start(line2, True, True, 0)
        #table.pack_start(line3, True, True, 10) # TODO resize spacing

        self.resize()

    def emit_signal(origin, button, signal):
        """Connect a button to a signal emission"""
        dispatcher = context.get_dispatcher()
        dispatcher.emit(signal, origin.back_page)
        
    def show_about_dialog(self, origin, button):
        """Pop up the About Dialog"""
        GCAboutDialog()

    def get_all_buttons(self):
        return self.events

    def resize(self): 
        """Adapts GUI elements to the screen size"""
        size = context.get_mainwindow().get_size()
        k1 = size[0] / 1920.0
        k2 = size[1] / 1080.0
   
        for pair in self.logos:            
            logo, name = pair
            pixbuf = gtk.gdk.pixbuf_new_from_file(get_image_path(name))    
            pixbuf = pixbuf.scale_simple(
                int(pixbuf.get_width()*k1),
                int(pixbuf.get_height()*k1),
                gtk.gdk.INTERP_BILINEAR)
            logo.set_from_pixbuf(pixbuf)

        for pair in self.buttons:
            button, width, height = pair
            button.set_property("width-request", int(k1*width) )
            button.set_property("height-request", int(k1*height) )
            for align in button.get_children():
                image = align.get_child().get_children()[0]
                if isinstance(image, gtk.Image):
                    #print image.get_stock()
                    #print type(image)
                    #print image.get_pixel_size()
                    image.set_pixel_size(int(k1*50))
                #print dir(image)

                #print image.get_name()
                #print image.get_icon_name()
                #print image.get_image()

        for pair in self.labels:
            label, font = pair
            relabel(label,int(k1*font),True)
        for pair in self.aligns:
            align, top, bottom, sides = pair
            align.set_padding(int(k1*top), int(k1*bottom), int(k1*sides), int(k1*sides) )

