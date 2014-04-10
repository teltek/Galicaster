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
from galicaster.classui import get_ui_path, get_image_path
from galicaster.classui.elements.message_header import Header

from galicaster import __version__
from galicaster.utils.i18n import _

PROGRAM = "Galicaster"
COPY = "Copyright © 2014 Teltek Video Research"
WEB = "http://galicaster.teltek.es"
LICENSE = """
Galicaster, Multistream Recorder and Player
Copyright (c) 2014, Teltek Video Research <galicaster@teltek.es>

This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License. 
To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
or send a letter to Creative Commons, 171 Second Street, Suite 300, San Francisco, California, 94105, USA. 
"""

AUTHORS = [
"Héctor Canto",
"Hugo Caloto",
"Rubén González",
"Rubén Pérez"
]

DOCS = (
"Héctor Canto",
"Hugo Caloto",
"Rubén González",
"Rubén Pérez"
)

ARTISTS = [
"Héctor Canto",
"Natalia García"
]

class GCAboutDialog(gtk.AboutDialog):

     __gtype_name__ = 'GCAboutDialog'

     def __init__(self, parent=None):
         if not parent:
             parent = context.get_mainwindow()
         gtk.AboutDialog.__init__(self)
         if parent:
             self.set_transient_for(parent)
         
         size=context.get_mainwindow().get_size()
         k = size[0]/1920.0
         self.set_resizable(True)
         self.set_default_size(int(0.3*size[0]),int(0.4*size[1]))
         self.set_title(_("About Galicaster {version}").format(version = __version__))
         
         strip = Header(size=size, title=_("About"))
         self.vbox.pack_start(strip, False, True, 0)
         self.vbox.reorder_child(strip,0)
         strip.show()
         self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_TOOLBAR)
         
         #self.set_decorated(True)
         self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)

         self.set_program_name(PROGRAM)
         self.set_version(__version__)
         self.set_website(WEB)
         self.set_website_label(_("Galicaster Website"))
         self.set_authors(AUTHORS)
         self.set_documenters(DOCS)
         self.set_artists(ARTISTS)
         self.set_copyright(COPY)
         self.set_license(LICENSE)
         pixbuf = gtk.gdk.pixbuf_new_from_file(get_image_path('logo.svg')) 
         pixbuf = pixbuf.scale_simple(
              int(pixbuf.get_width()*k),
              int(pixbuf.get_height()*k),
              gtk.gdk.INTERP_BILINEAR)

         #self.set_logo(pixbuf)

         #ADD TELTEK LOGO
         box=self.get_content_area()
         company_logo=gtk.Image()
         pixbuf = gtk.gdk.pixbuf_new_from_file(get_image_path('teltek.svg')) 
         pixbuf = pixbuf.scale_simple(
              int(pixbuf.get_width()*k),
              int(pixbuf.get_height()*k),
            gtk.gdk.INTERP_BILINEAR)

         company_logo.set_from_pixbuf(pixbuf)

         box.pack_end(company_logo,True,True,0)
         company_logo.show()

         #ADD THANKS
         #thanks=gtk.Button("Thanks")
         #buttons=self.get_action_area()
         #thanks.connect("clicked",self.show_thanks)
         #buttons.pack_start(thanks)
         #buttons.reorder_child(thanks,0)
         #thanks.show()
         
         #self.run()
         #self.destroy()

     def show_thanks(self, orgin):
         dialog = gtk.Dialog()
         dialog.set_title(_("Special thanks to..."))
         dialog.add_button("Close",gtk.RESPONSE_CLOSE)
         dialog.set_default_size(350,150)
         dialog.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_SPLASHSCREEN)
         box = dialog.get_content_area()
         textbuffer= gtk.TextBuffer()
         textbuffer.set_text("")
         label= gtk.TextView(textbuffer)
         align= gtk.Alignment()
         align.set_padding(10,-1,10,10)
         align.add(label)
         box.pack_start(align, True, True, 0)
         align.show()
         label.show()
         #dialog.run()
         #dialog.destroy()



         
         
         


     
