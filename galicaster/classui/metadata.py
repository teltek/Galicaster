# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/ui/metadata
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.
"""
UI for a Metadata Editor Pop UP
"""

import gtk
import datetime # idem
from os import path #idem
import gobject
import pango

from galicaster.classui.calendarwindow import CalendarWindow # idem
import galicaster.mediapackage.mediapackage as mediapackage # TODO remove dependency when series refactorized
from galicaster.core import context
from galicaster.utils import series as listseries # idem
from galicaster.classui.elements.message_header import Header
from galicaster.classui.elements.editors import TextViewer, DatetimeViewer
from galicaster.classui.elements.editors import TextEditor, SelectEditor, LanguageEditor, DatetimeEditor, SeriesEditor, Editor
 # TODO load as choosers on operations do

NO_SERIES  = "NO SERIES ASSIGNED"
DEFAULT_SERIES = "DEFAULT SERIES"

class MetadataClass(gtk.Widget):
    """
    Handle a pop up metadata editor, updating it if necessary
    """
    __gtype_name__ = 'MetadataClass'

    def __init__(self,package = None, parent = None):

        parent = context.get_mainwindow() # TODO get parent from init else get from context

        size = parent.get_size()            
        self.terms = context.get_conf().get_metadata()
        self.create_ui()
        self.fill_metadata(package)
        self.package = package
        self.dialog.show_all()
        self.dialog.present()

    def fill_metadata(self, mp):
        """
        Fill the table with available data
        """

        metadatum = self.terms[0].parameters
        group = "episode"
        # FORMER fontsize was 16

        for meta in metadatum:
            if meta.visibility != "hidden":
                default_value = mp.metadata_episode.get(meta.name) or meta.default # JUST for group episode
                # TODO check meta.name on series, title or id?
                
                if meta.visibility == "edit" and meta.type == "text":
                    widget = TextEditor(group, meta.name, meta.label, default = default_value)
                elif meta.visibility == "edit" and meta.type == "select":
                    widget = SelectEditor(group, meta.name, meta.label, 
                                          default_value, options = meta.options)
                elif meta.visibility == "edit" and meta.type == "language":
                    widget = LanguageEditor(group, meta.name, meta.label, 
                                          default_value, options = meta.options)

                elif meta.visibility == "edit" and meta.type == "datetime":
                    widget = DatetimeEditor(group, meta.name, meta.label, default = default_value)
                elif meta.visibility == "edit" and meta.type == "series":
                    default_value = mp.getSeriesTitle() or NO_SERIES
                    widget = SeriesEditor(group, meta.name, meta.label, 
                                          default_value, options=listseries.get_series())
                else:
                    # PARSE language to iso
                    if isinstance(default_value, datetime.datetime):
                        default_value = default_value.replace(microsecond=0).isoformat()
                    widget = TextViewer(group, meta.name, meta.label, default = default_value)

                self.content.pack_start(widget, True, False, 4)
                widget.show_all()            

                # d = ComboBoxEntryExt(self.par,listseries.get_series(),
                # d.connect("button-press-event",self.edit_date)


        metadatum = self.terms[1].parameters
        group = "custom"
        for meta in metadatum:
            if meta.visibility != "hidden":
                default_value = mp.metadata_custom.get(meta.name) or meta.default # JUST for group episode
               # TODO check meta.name on series, title or id?
                
                if meta.visibility == "edit" and meta.type == "text":
                    widget = TextEditor(group, meta.name, meta.label, default = default_value)
                elif meta.visibility == "edit" and meta.type == "select":
                    widget = SelectEditor(group, meta.name, meta.label, 
                                          default_value, options = meta.options)
                elif meta.visibility == "edit" and meta.type == "language":
                    widget = LanguageEditor(group, meta.name, meta.label, 
                                          default_value, options = meta.options)
                elif meta.visibility == "edit" and meta.type == "datetime":
                    widget = DatetimeEditor(group, meta.name, meta.label, default = default_value)
                elif meta.visibility == "edit" and meta.type == "series":
                    default_value = mp.getSeriesTitle() or NO_SERIES
                    widget = SeriesEditor(group, meta.name, meta.label, 
                                          default_value, options=listseries.get_series())
                else:
                    # PARSE language to iso
                    #if isinstance(default_value, datetime.datetime):
                    #    default_value = default_value.replace(microsecond=0).isoformat()
                    widget = TextViewer(group, meta.name, meta.label, default = default_value)

                self.content.pack_start(widget, True, False, 4)
                widget.show_all() 

    def update_series(self, package, result): # TODO associate to mp before update

        if result != NO_SERIES:
            series = listseries.getSeriesbyName(result)
            package.setSeries(series["list"])
            print "update series:", series
            if not package.getCatalogs("dublincore/series") and package.getURI():
                new_series = mediapackage.Catalog(path.join(package.getURI(),"series.xml"),
                                                  mimetype="text/xml",flavor="dublincore/series")
                package.add(new_series)
        else:
            package.setSeries(None)
            catalog = package.getCatalogs("dublincore/series")
            if catalog:
                package.remove(catalog[0])


    def update_custom(self, package): # TODO associate to mp before update

        if not package.getCatalogs("dublincore/custom") and package.getURI():
            new_custom = mediapackage.Catalog(path.join(package.getURI(),"custom.xml"),
                                              mimetype="text/xml",flavor="dublincore/custom")
            package.add(new_custom)

        if not package.metadata_custom:
            catalog = package.getCatalogs("dublincore/custom")
            if catalog:
                package.remove(catalog[0])


    def update_metadata(self, button = None):
        result = []
        mp = context.get_repository().get(self.package.getIdentifier() )
        in_repo = True if mp else False
        if not in_repo:
            mp = self.package # for Recorder edition
        print "update_metadata", mp

        for child in self.content.get_children():
            if isinstance(child, Editor): # TODO check viewers
                result += [ child.getValue()]
        for group, variable, value in result:
            print group, variable, value
            if group == "episode": # TODO get group reference and update it directly
                mp.metadata_episode[variable] = value
                if variable.lower() == "ispartof": # TODO variable comes as ispartof 
                    self.update_series(mp, value)                
            elif group == "series":
                mp.metadata_series[variable] = value
            elif group == "custom":
                mp.metadata_custom[variable] = value # TODO add to galicaster.mediapackage.mediapackage
                self.update_custom(mp) # TODO review somehow at the end of all group parameters in every group
                print "CUSTOM metadata update on METADATA EDITOR", mp.metadata_custom

        # TODO use update_series before updating the MP
        
        if in_repo:
            context.get_repository().update(mp)
            context.get_dispatcher().emit('refresh-row', mp.getIdentifier())
        
        self.close()

    def refresh_metadata(self):
        # TODO run through all metadata that changed and setValue
        # take into account new values made by changing series
        # some metadata depends on enviroment values like login, place, hostname ...
        pass
        
    def close(self, button = None):
        self.dialog.destroy()        

    def create_ui(self):                  
        parent = context.get_mainwindow()
        size = parent.get_size()

        self.wprop = size[0] / 1920.0
        self.hprop = size[1] / 1080.0
        self.prop = size[0] / float(size[1])

        self.dialog = gtk.Window()
        self.dialog.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_TOOLBAR)
        corrector = 1.3 * self.prop # Correction between panoramic and 4:3ish
        self.dialog.set_property('width-request', int(size[0]/corrector) )
        self.dialog.set_property('height-request', int(size[1]/2.2) )
        self.dialog.set_transient_for(parent)                               
        self.dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT) # TODO set parent
        self.dialog.set_modal(True)
        mainbox = gtk.VBox()
        self.dialog.add(mainbox)

        strip = Header(size=size, title="Metadata Editor")
        mainbox.pack_start(strip, False, True, 0)

        action = gtk.HButtonBox()
        action.set_layout(gtk.BUTTONBOX_SPREAD)
        self.content = gtk.VBox()
        body=gtk.VBox()
        align = gtk.Alignment(0.5, 1.0, 1.0, 1.0)
        align.set_padding(int(self.wprop*20), 0, int(self.wprop*90), int(self.wprop*90))
        align.add(self.content)
        body.pack_start(align, True, False, 0)
        body.pack_start(action, False, True, int(self.wprop*20))

        #align = gtk.Alignment(0.8, 0.8, 0.5, 0.5)
        #align.add(body)
        frame= gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        frame.add(body)
        mainbox.pack_start(frame, True, True, 0)
        
        save = self.add_button(size, action, "Save")
        cancel = self.add_button(size, action, "Cancel")
        save.connect("clicked", self.update_metadata)
        cancel.connect("clicked", self.close)

    def add_button(self, size, box, text):
        button = gtk.Button()
        button.set_label(text)
        button.set_property("width-request", int(self.wprop*150) )
        button.set_property("height-request", int(self.wprop*50) )
        label = button.get_children()[0]
        modification = str(int(self.hprop*20)) #+"px"
        label.modify_font(pango.FontDescription(modification))
        #padding = self.wprop*20/2.6
        #label.set_padding(-1, int(padding))
        #label.set_width_chars(int(self.wprop*10))
        button.set_can_focus(False)
        box.pack_start(button) # TODO connect button
        return button

gobject.type_register(MetadataClass)
