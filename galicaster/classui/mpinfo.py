# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/ui/mpinfo
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.
"""
Pop Up with exhaustive information of a Mediapackage
"""

import gtk
from os import path
import pango

import galicaster.mediapackage.mediapackage as mediapackage
from galicaster.core import context
from galicaster.utils import readable
from galicaster.utils.nautilus import open_folder

from galicaster.utils.i18n import _

EPISODE_NAMES = { 'title': _('Title:'),
            'identifier': _('Identifier:'),
            'folder': _('Folder:'),
            'duration': _('Duration:'),
            'size': _('Size:'),
            'created': _('Recorded on:'),
            'license': _('License:'),
            'temporal': _('Temporal:'),
            'spatial': _('Agent name:'),
            'isPartOf': _('Series:'),
            'contributor': _('Contributor:'),
            'creator': _('Presenter:'),
            'subject': _('Subject:'),
            'language': _('Language:'),
            'description': _('Description:'),
            'rights': _('Rights:'),
             }

SERIES_NAMES = { 'title': _('Title:'),
            'identifier': _('Identifier:'),
            'creator': _('Creator:'),
            'contributor': _('Contributor:'),
            'subject': _('Subject:'),
            'language': _('Language:'),
            'license': _('License:'),
            'description': _('Description:'),
             }


ORDER_EPISODES = [ 'title', 'identifier', 'folder', 'duration', 'size', 'created' , 'license', 'temporal', 'spatial', 'isPartOf', 'contributor', 'creator', 'subject', 'language', 'description', 'rights']

ORDER_SERIES = [ 'title', 'identifier','creator', 'contributor', 'subject', 'language', 'license', 'decription']

class MPinfo(gtk.Window):

    __gtype_name__ = 'MPinfoUI'

    def __init__(self, key, parent = None):
        if not parent:
            parent = context.get_mainwindow()
        size = context.get_mainwindow().get_size()
        self.wprop = size[0]/1920.0
        self.hprop = size[1]/1080.0
        width = int(size[0]/3)
        height = int(size[1]/2.5)
        
        gtk.Window.__init__(self)
        self.set_title(_("Mediapackage Info "))
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.set_default_size(width,height)
        self.set_modal(True)
        if parent:
            self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
            self.set_transient_for(parent)
            self.set_destroy_with_parent(True)

        # INFO       
	mp = context.get_repository().get(key)

        

        # Metadata info
        data = {}
        data['title'] = mp.title
        data['identifier'] = mp.identifier
        data['folder'] = mp.getURI()
        data['duration'] = readable.time(int(mp.getDuration())/1000)
        data['size'] = readable.size(mp.getSize())
        data['created'] = readable.date(mp.getStartDateAsString(),
                                   "%B %d, %Y - %H:%M").replace(' 0',' ')

        basic, basic_table = self.add_framed_table(_("Basic"))    
        for item in ORDER_EPISODES:
            if item in data:
                self.add_data(basic_table,EPISODE_NAMES[item], data[item])
            elif item in mp.metadata_episode:
                self.add_data(basic_table,EPISODE_NAMES[item], mp.metadata_episode[item])                

        # Operations info
        ops, ops_table = self.add_framed_table(_("Operations"))
        self.add_data(ops_table,_("Ingest:"),
                      mediapackage.op_status[mp.getOpStatus("ingest")])
        self.add_data(ops_table,_("Zipping:"),
                      mediapackage.op_status[mp.getOpStatus("exporttozip")])
        self.add_data(ops_table,_("Side by Side:"),
                      mediapackage.op_status[mp.getOpStatus("sidebyside")])

        
        # Series info
        if mp.getSeries():
            series, series_table = self.add_framed_table(_("Series"))
            for item in ORDER_SERIES:
                if item in mp.metadata_series:
                    self.add_data(series_table,SERIES_NAMES[item], mp.metadata_series[item])

        # Track info
        tracks, track_table = self.add_framed_table(_("Tracks"), True)
        first = True
        for track in mp.getTracks():
            if not first:
                self.add_data(track_table,"","")
            first = False
            self.add_data(track_table,_("Name:"),track.getIdentifier())
            self.add_data(track_table,_("Flavor:"),track.getFlavor())
            self.add_data(track_table,_("Type:"),track.getMimeType())
            filename = str(path.split(track.getURI())[1])
            self.add_data(track_table,_("File:"),filename)

        # Catalog info
        cats, cat_table = self.add_framed_table(_("Catalogs"), True)
        first = True
        for cat in mp.getCatalogs():
            if not first:
                self.add_data(cat_table,"","")
            first = False
            self.add_data(cat_table,_("Name:"),cat.getIdentifier())
            self.add_data(cat_table,_("Flavor:"),cat.getFlavor())
            self.add_data(cat_table,_("Type:"),cat.getMimeType())
            filename = str(path.split(cat.getURI())[1])
            self.add_data(cat_table,_("File:"),filename)

        #PACKING
        box = gtk.VBox()
        box.pack_start(basic,False,True,int(self.hprop*10))
        box.pack_start(ops,False,True,int(self.hprop*10))
        if mp.getSeries():
            box.pack_start(series,False,True,int(self.hprop*10))
        box.pack_start(tracks,False,True,int(self.hprop*10))
        box.pack_start(cats,False,True,int(self.hprop*10))
        external_align=gtk.Alignment(0.5,0,0.8,0.8)
        external_align.add(box)

        self.add(external_align)

        #BUTTONS
        self.buttons = gtk.HButtonBox()
        self.buttons.set_layout(gtk.BUTTONBOX_SPREAD)

        self.add_button(_("Close"), self.close)
        self.add_button(_("Open Folder"), self.openfolder, mp.getURI())
        box.pack_end(self.buttons, False, False, int(self.hprop*10))
        self.show_all()
		    
    def add_framed_table(self,name, expanded = False):
        """Stablished a framed table for the information to be shown in"""
        frame =gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        expander= gtk.Expander()
        if expanded:
            expander.set_label(name)
            expander.set_expanded(False)
            #expander.set_label_fill(False)
        else:
            frame.set_label(name)
            
        table = gtk.Table()
        align= gtk.Alignment(0.75,0,0.9,0.9)
        align.add(table)
        if expanded:
            expander.add(align)
            frame.add(expander)
        else:
            frame.add(align)
        return frame,table


    def add_data(self,table,name,value):
        """Attach data to the table"""
        row = table.get_property("n-rows")
        title = gtk.Label(name)
        title.set_alignment(1,0)

        modification = str(int(self.hprop*16))+"px"        
        title.modify_font(pango.FontDescription(modification))

        title.set_width_chars(-1)
        title.set_max_width_chars(int(self.wprop*50))
            
        data=gtk.Label(value)
        data.set_selectable(True)
        data.set_alignment(0,0)
        data.modify_font(pango.FontDescription(modification))

        table.attach(title,0,1,row,row+1,gtk.FILL,False,
                     0,0)
        table.attach(data,1,2,row,row+1,gtk.EXPAND|gtk.FILL,False,
                     int(self.wprop*10),0)

    def add_button(self, text, connection, data = None, end=False):
        """Adds a action button on the bottom of the window"""
        k1 = self.wprop
        button = gtk.Button(text)
        button.set_property("width-request", int(k1*150))
        button.set_property("height-request", int(k1*50))
        label = button.get_children()[0]
        modification = str(int(self.hprop*17))
        label.modify_font(pango.FontDescription(modification))
        if not end:
            self.buttons.pack_start(button)
        else:
            self.buttons.pack_end(button)
        if data:
            button.connect("clicked",connection, data)
        else:
            button.connect("clicked",connection)
        return button

    def openfolder(self, button, folder):
        """Bypass to open a folder on the system file manager"""
        open_folder(folder)

    def close(self,button=None):
        self.destroy() 
