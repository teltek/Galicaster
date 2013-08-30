# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.
"""
A Custom taskbar or header for Galicaster messages, dialogs and other popups
"""

import gtk
import pango
from galicaster.classui import get_image_path

class Header(gtk.Frame):

    def __init__(self, size=[1920,1080],title = None):
        
        wprop = size[0]/1920.0
        hprop = size[1]/1080.0
        gtk.Frame.__init__(self)
        box = gtk.HBox()
        box.set_border_width(int(wprop*10))
        strip = gtk.Image()
        pixbuf = gtk.gdk.pixbuf_new_from_file(get_image_path('logo.svg')) 
        pixbuf = pixbuf.scale_simple(
            int(pixbuf.get_width()*wprop*0.6),
            int(pixbuf.get_height()*wprop*0.6),
            gtk.gdk.INTERP_BILINEAR)
        strip.set_from_pixbuf(pixbuf)
        strip.set_alignment(0.05,0.5)
        box.pack_start(strip, True, True, 0) # introduce hprop
        if title:
            label = gtk.Label(title)
            label.set_alignment(0.95,0.5)
            font = pango.FontDescription("bold "+str(int(15)*hprop))
            label.modify_font(font)
            box.pack_end(label, True, True, 0) # introduce hprop
        self.add(box)
        box.show_all()
        
