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
import datetime
from os import path
import gobject
import pango
import os

from galicaster.classui.calendarwindow import CalendarWindow
import galicaster.mediapackage.mediapackage as mediapackage
from galicaster.core import context
from galicaster.utils import series as listseries
from galicaster.classui import get_ui_path
from galicaster.classui.elements.message_header import Header

from galicaster.utils.i18n import _

NO_SERIES  = "** NO SERIES SELECTED **"
DEFAULT_SERIES = "DEFAULT SERIES"

DCTERMS = ["title", "creator", "description", "language", "isPartOf"]
EQUIV = { "presenter":"creator", "ispartof": "isPartOf", "series":"isPartOf" }

metadata = { "title": _("Title:"), _("Title:"):"title",
             "creator": _("Presenter:"), _("Presenter:"):"creator", 
             "isPartOf": _("Course/Series:"), _("Course/Series:"):"isPartOf",
             "description": _("Description:"), _("Description:"):"description", 
             "subject": _("Subject:"), _("Subject:"):"subject", 
             "language": _("Language:"), _("Language:"):"language", 
             "identifier": _("Identifier:"), _("Identifier:"):"identifier", 
             "contributor": _("Contributor:"),_("Contributor:"):"contributor", 
             "created":_("Start Time:"), _("Start Time:"):"created"} 

class MetadataClass(gtk.Widget):
    """
    Handle a pop up metadata editor, updating it if necessary
    """
    __gtype_name__ = 'MetadataClass'

    def __init__(self, package = None, series_list = None, parent = None,
                 title=_("Edit Metadata"), subtitle=_("Edit Metadata"), ok_label = _("Save"), ko_label = _("Cancel"),
                 empty_series_label = NO_SERIES):
        """
        """

        parent = context.get_mainwindow()
        size = parent.get_size()
            
        self.par = parent
        altura = size[1]
        anchura = size[0]        
        k1 = anchura / 1920.0                                      
        k2 = altura / 1080.0
        self.wprop = k1
        self.hprop = k2

        self.series_list = series_list
        self.empty_series_label = empty_series_label

        gui = gtk.Builder()
        gui.add_from_file(get_ui_path('metadata.glade'))

        dialog = gui.get_object("metadatadialog")

        # Set up the dialog's label
        gui.get_object("title").set_text(subtitle)

        # Set up the button text
        gui.get_object("slabel").set_label(ok_label)
        gui.get_object("clabel").set_label(ko_label)

        dialog.set_property("width-request",int(anchura/2.2))
        dialog.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_TOOLBAR)
        dialog.set_modal(True)
        dialog.set_keep_above(False)

        #NEW HEADER
        strip = Header(size=size, title=title)
        dialog.vbox.pack_start(strip, True, True, 0)
        dialog.vbox.reorder_child(strip,0)

        if parent != None:
            dialog.set_transient_for(parent.get_toplevel())
        
        table = gui.get_object('infobox')
        dialog.vbox.set_child_packing(table, True, True, int(self.hprop*25), gtk.PACK_END)    
        title = gui.get_object('title')
        sl = gui.get_object('slabel')
        cl = gui.get_object('clabel')
        talign = gui.get_object('table_align')

        modification = "bold "+str(int(k2*25))+"px"        
        title.modify_font(pango.FontDescription(modification))
        title.hide()
        talign.set_padding(int(k2*40),int(k2*40),0,0)
        mod2 = str(int(k1*35))+"px"        
        sl.modify_font(pango.FontDescription(mod2))
        cl.modify_font(pango.FontDescription(mod2))

        # Get "blocked" and "mandatory" parameters
        blocked = set()
        mandatory = set()
        try:
            for term in context.get_conf().get('metadata', 'blocked').split():
                try:
                    blocked.add(EQUIV[term])
                except KeyError:
                    blocked.add(term)
        except (KeyError, AttributeError):
            # 'blocked' was not defined in configuration
            pass
        
        try:
            for term in context.get_conf().get('metadata', 'mandatory').split():
                try:
                    mandatory.add(EQUIV[term])
                except KeyError:
                    mandatory.add(term)
        except (KeyError, AttributeError):
            # 'mandatory' was not defined in configuration
            pass

        self.mandatory = {}
        ok_button = gui.get_object("savebutton")
        self.fill_metadata(table, package, ok_button, blocked, mandatory)
        
        self.check_mandatory(None, ok_button, check_all = True)

        talign.set_padding(int(self.hprop*25), int(self.hprop*10), int(self.hprop*25), int(self.hprop*25))
        dialog.vbox.set_child_packing(dialog.action_area, True, True, int(self.hprop*25), gtk.PACK_END)   
        dialog.show_all()

        self.return_value = dialog.run()
        if self.return_value == -8:
            self.update_metadata(table,package)
        dialog.destroy()


    def fill_metadata(self,table,mp,button,blocked=set(),mandatory=set()):
        """
        Fill the table with available data, empty otherwise
        """        
        for child in table.get_children():
            table.remove(child) #FIXME maybe change the glade to avoid removing any widget
        table.resize(1,2) 
        row = 1

        for meta in DCTERMS:
            t=gtk.Label(metadata[meta])
            t.set_justify(gtk.JUSTIFY_LEFT)
            t.set_alignment(0,0)
            modification = str(int(self.hprop*16))+"px"        
            t.modify_font(pango.FontDescription(modification))
            t.set_width_chars(15)

            # Switch the INSENSITIVE state colour to red, so that we can mark the mandatory parameters
            t.modify_fg(gtk.STATE_INSENSITIVE, gtk.gdk.color_parse('red'))            
            
            if meta in ["ispartof", "isPartOf"]:
                try:
                    default_series = listseries.getSeriesbyId(mp.metadata_series['identifier'])['id']
                except TypeError:
                    default_series = None
                
                d = ComboBoxEntryExt(self.par, self.series_list, default=default_series, empty_label = self.empty_series_label)
                d.set_name(meta)
            else:
                d=gtk.Entry()
                d.set_name(meta)
                try:
                    d.set_text(mp.metadata_episode[meta] or '')
                except KeyError:
                    d.set_text('')
                
            if meta in blocked:
                d.set_sensitive(False)

            if meta in mandatory:
                d.connect_after('changed', self.check_mandatory, button)
                self.mandatory[d] = t
            
            if meta == "created": # currently Unused
                d.connect("button-press-event",self.edit_date)
            if meta == "title":
                d.set_tooltip_text(d.get_text())

            d.modify_font(pango.FontDescription(modification))

            table.attach(t,0,1,row-1,row,False,False,0,0)
            table.attach(d,1,2,row-1,row,gtk.EXPAND|gtk.FILL,False,0,0)
            row=row+1

    def check_mandatory(self, item, button, check_all = False):
        entries = self.mandatory.keys()
        if not check_all:
            # Put 'item' at the beginning of the list
            entries.insert(0, entries.pop(entries.index(item)))

        button.set_sensitive(True)
        for elem in entries:
            try:
                content = elem.get_text()
            except AttributeError:
                # It's the ComboBoxEntry
                try:
                    content = elem.get_model()[elem.get_active_iter()][1]
                except (AttributeError, TypeError):
                    content = None

            # The style has been changed so that labels marked as 'insensitive' will be displayed in red
            self.mandatory[elem].set_sensitive(bool(content))
            
            # Set button's sensitivity. If there is no content, it should be greyed out        
            if not bool(content):
                button.set_sensitive(False)
                # Since the item that changed is at the beginning of the list, we do not need to check the others
                # (unless, of course, we force checking the whole list --to initialize the entries status, for instance--)
                if not check_all:
                    break

        return False

    def strip_spaces(self,value):
        """Remove spaces before and after a value"""
        return value.strip()

    def update_metadata(self,table,mp):
        """Write data back to the mediapackage"""
        for child in table.get_children():
            if child.name in DCTERMS:
                if child.name in ["creator", "contributor", "subject"]:
                    if child.get_text() == "":
                        mp.metadata_episode[child.name] = None
                    else:
                        mp.metadata_episode[child.name] = child.get_text().strip()

                elif child.name in [ "ispartof", "isPartOf" ]:
                    identifier = child.get_model()[child.get_active_iter()][1]
                    series = listseries.getSeriesbyId(identifier)
                    if series:
                        mp.setSeries(series["list"])
                        if not mp.getCatalogs("dublincore/series") and mp.getURI():
                            new_series = mediapackage.Catalog(os.path.join(mp.getURI(),"series.xml"),mimetype="text/xml",flavor="dublincore/series")
                            mp.add(new_series)                    
                    else: 
                        mp.setSeries(None)
                        catalog= mp.getCatalogs("dublincore/series")
                        if catalog:
                            mp.remove(catalog[0])
                else:
                    mp.metadata_episode[child.name]=child.get_text()

    def edit_date(self,element,event):
        """Filter a Right button double click, show calendar and update date"""
      
        if event.type == gtk.gdk._2BUTTON_PRESS and event.button==1:
            text= element.get_text()
            try:
                date=datetime.datetime.strptime(text,"%Y-%m-%dT%H:%M:%S") 
            except ValueError:
                date=0
            v = CalendarWindow(date)
            v.run()
            if v.date != None:
                element.set_text(v.date.isoformat())
        return True


class ComboBoxEntryExt(gtk.ComboBoxEntry):

    def __init__(self, parent, listing=None, default=None, empty_label=""):
        """
        From a dict of series (series(id)=name) returns a ComboBoxEntry with a customize searcher
        """

        self.par = parent
        self.empty_label = empty_label

        liststore = gtk.ListStore(str,str)

        if listing is None:
            listing = []

        try:
            # If 'default' is an existing series id, 
            # set "default_text" to the corresponding series title
            self.default_text = dict(listing)[default]['title']
        except KeyError:
            # "default" is not in the listing, so we ignore it
            self.default_text = None


        # Include empty_label in the list, if it is not None
        if empty_label is not None:
            liststore.append((empty_label, None))

        for element in listing:
            liststore.append([element[1]['title'], element[0]]) # NAME ID

        self.liststore = liststore # CHECK

        # Filter
        combofilter = liststore.filter_new()
        #combofilter.set_visible_func(self.filtering) 

        # Completion
        completion = gtk.EntryCompletion()
        completion.set_model(liststore)
        completion.set_match_func(self.filtering_match, completion)
        completion.set_text_column(0)
        completion.set_inline_selection(True)
        
        super(ComboBoxEntryExt, self).__init__(liststore,0)

        liststore.set_sort_func(0, self.sorting, self.child) # Put default text first
        liststore.set_sort_column_id(0,gtk.SORT_ASCENDING)
     
        self.set_model(combofilter)
        self.child.set_completion(completion)

        # Set the appropriate value
        if empty_label is not None and self.default_text is not None:
            self.set_active(1)
        else:
            self.set_active(0)

        self.current = self.child.get_text()
        self.current_iter = self.get_active_iter()

        # Signals   
        self.child.connect('activate', self.on_activate)
        self.child.connect('focus-out-event', self.ensure_match)
        self.connect('changed', self.on_changed)


    def on_changed(self, myself):
        # This signal gets triggered when the Entry contents change
        if myself.get_active() < 0:
            text = self.child.get_text()
            model = self.get_model()
            iterator = model.get_iter_first()

            while iterator:
                if text == model[iterator][0]:
                #self.child.set_text(iterator[0])
                    self.set_active_iter(iterator)
                    self.current = self.child.get_text()
                    self.current_iter = iterator
                    break
                iterator = model.iter_next(iterator)

        return False

        
    def ensure_match(self, origin, event):
        # Make sure that, if the box contents do not match one of the options in the list,
        # the content falls back to a valid value.
        if self.get_active() < 0:
            self.set_active_iter(self.current_iter)

        return False
                

    def on_activate(self, entry):
        text = entry.get_text().lower()        
        iterator = self.liststore.get_iter_first()
        while iterator:
            rowtext = self.liststore[iterator][0]
            if rowtext.lower().startswith(text):
                # For some reason we cannot set the active iter using this iterator,
                # but modifying the Entry contents triggers the "on_change" callback
                # where the active iterator value is properly updated
                self.child.set_text(rowtext)
                break                
            iterator = self.liststore.iter_next(iterator)

        return False


    def filtering_match(self, completion, key_string, iterator, data = None):
        """Filtering completion"""
        model = completion.get_model()
        series = model[iterator][0]
        if series == self.default_text: # always show default
            return True
        elif key_string.lower() in series.lower(): # Show coincidence
            return True
        elif key_string == self.default_text:
            return True
        else:
            return False  
       
    def filtering(self, model, iterator):
        """Filtering ComboBox"""
        key_string = self.child.get_text()
        series =  model[iterator][0]
        if series == self.default_text: # always show default
            return True
        elif key_string.lower() in series.lower(): # Show coincidence
            return True
        elif key_string == self.default_text:
            return True
        else:
            return True

    def sorting(self, treemodel, iter1, iter2, entry):
        """Sorting algorithm, placing first default series and no series"""
        current_text = entry.get_text()
        if self.empty_label is not None:
            if treemodel[iter1][0] == self.empty_label:
                return -1
            elif treemodel[iter2][0] == self.empty_label:
                return 1
        if current_text:
            if treemodel[iter1][0] == current_text:
                return -1
            elif treemodel[iter2][0] == current_text:
                return 1
        if self.default_text is not None:
            if treemodel[iter1][0] == self.default_text:
                return -1
            elif treemodel[iter2][0] == self.default_text:
                return 1

        # If none of the previous conditions met, respect the original order
        return 0

gobject.type_register(MetadataClass)
gobject.type_register(ComboBoxEntryExt)
