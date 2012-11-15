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

from galicaster.classui.calendarwindow import CalendarWindow
import galicaster.mediapackage.mediapackage as mediapackage
from galicaster.core import context
from galicaster.utils import series as listseries
from galicaster.classui import get_ui_path

#DCTERMS = ["title", "creator", "ispartof", "description", "subject", "language", "identifier", "contributor", "created"] # FIXME take out contributor creator
DCTERMS = ["title", "creator", "description", "language", "ispartof"]
metadata ={"title": "Title:", "creator": "Presenter:", "ispartof": "Course/Series:", "description": "Description:", 
           "subject": "Subject:", "language": "Language:", "identifier": "Identifier:", "contributor": "Contributor:", 
           "created":"Start Time:", "Title:":"title", "Presenter:":"creator",  "Course/Series:":"ispartof", 
           "Description:":"description", "Subject:":"subject", "Language:":"language", "Identifier:":"identifier", 
           "Contributor:":"contributor", "Start Time:":"created"}

NO_SERIES  = "NO SERIES ASSIGNED"
DEFAULT_SERIES = "DEFAULT SERIES"

class MetadataClass(gtk.Widget):
    """
    Handle a pop up metadata editor, updating it if necessary
    """
    __gtype_name__ = 'MetadataClass'

    def __init__(self,package = None, parent = None):

        parent = context.get_mainwindow()
        size = parent.get_size()
            
        self.par = parent

        altura = size[1]
        anchura = size[0]        
        k1 = anchura / 1920.0                                      
        k2 = altura / 1080.0
        self.wprop = k1
        self.hprop = k2

        gui = gtk.Builder()
        gui.add_from_file(get_ui_path('metadata.glade'))

        dialog = gui.get_object("metadatadialog")
        dialog.set_property("width-request",int(anchura/2.2))
        dialog.set_property("border-width",int(anchura/50.0))

        if parent != None:
            dialog.set_transient_for(parent.get_toplevel())

        table = gui.get_object('infobox')
        title = gui.get_object('title')
        sl = gui.get_object('slabel')
        cl = gui.get_object('clabel')
        talign = gui.get_object('table_align')

        modification = "bold "+str(int(k2*25))+"px"        
        title.modify_font(pango.FontDescription(modification))
        talign.set_padding(int(k2*40),int(k2*40),0,0)
        mod2 = str(int(k1*35))+"px"        
        sl.modify_font(pango.FontDescription(mod2))
        cl.modify_font(pango.FontDescription(mod2))


        self.fill_metadata(table, package)



        
        # Close Metadata dialog and update
        if dialog.run() == -8:
            self.update_metadata(table,package)

        dialog.destroy()

		
    def fill_metadata(self,table,mp):
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
            
            d=gtk.Entry()
            d.set_name(meta)
            try:
                if  meta == "creator":
                    if len(mp.creators):
                        d.set_text(", ".join(mp.creators))
                    else:
                        d.set_text("")  

                elif meta == "ispartof":
                    d = ComboBoxEntryExt(self.par,listseries.get_series(),
                                         NO_SERIES)
                    d.set_name(meta)
                    if mp.series_title not in [None, ""]:
                        d.child.set_text(mp.series_title)
                    else:     
                        d.child.set_text(NO_SERIES)
                                        
                elif meta in ["contributor", "subject"]: # FIXME do it like creator
                    if len(mp.metadata_episode[meta])>0:
                        d.set_text(", ".join(mp.metadata_episode[meta]))
                    else:
                        d.set_text("")
                else: 
                    d.set_text(mp.metadata_episode[meta])
            except (TypeError, KeyError):                
                if meta == "ispartof":
                    d = ComboBoxEntryExt(self.par,listseries.get_series(), 
                                         NO_SERIES)
                    if mp.series_title not in [None, ""]:
                        d.child.set_text(mp.series_title)
                    else:     
                        d.child.set_text(NO_SERIES)
            
            if meta == "created":
                d.connect("button-press-event",self.edit_date)
            if meta == "title":
                d.set_tooltip_text(d.get_text())

            d.modify_font(pango.FontDescription(modification))

            table.attach(t,0,1,row-1,row,False,False,0,0)
            table.attach(d,1,2,row-1,row,gtk.EXPAND|gtk.FILL,False,0,0)
            t.show()
            d.show()
            row=row+1

    def strip_spaces(self,value):
        """Remove spaces before and after a value"""
        return value.strip()

    def update_metadata(self,table,mp):
        """Write data back to the mediapackage"""
        for child in table.get_children():
            if child.name in DCTERMS:
                if child.name == "creator":
                    if child.get_text() != "":                        
                        new = list(child.get_text().strip().split(','))
                        splitted = map(self.strip_spaces, new)
                        mp.setCreators(splitted)
                    else:
                        mp.setCreators(list())
                elif child.name == "contributor":
                    if child.get_text() != "":
                        new = list(child.get_text().strip().split(','))
                        splitted = map(self.strip_spaces, new)
                        mp.setContributors(splitted)
                    else:
                        mp.setContributors(list())
                elif child.name == "subject":
                    if child.get_text() != "":
                        new = list(child.get_text().strip().split(','))
                        splitted = map(self.strip_spaces, new)
                        mp.setSubjects(splitted)
                    else:
                        mp.setSubjects(list())
                elif child.name == "ispartof":
                    result=child.get_active_text()
                    model = child.get_model()
                    iterator = model.get_iter_first()
                    while iterator != None:
                        if model[iterator][0] == result:
                            break
                        iterator = model.iter_next(iterator)                        
                    identifier = model[iterator][1]
                    series = None
                    if result != NO_SERIES:
                        series = listseries.getSeriesbyId(identifier)

                    if series != None:
                        mp.series = series["id"]
                        mp.series_title = series["name"]

                        if not mp.getCatalogs("dublincore/series") and mp.getURI():
                            new_series = mediapackage.Catalog(path.join(mp.getURI(),"series.xml"),mimetype="text/xml",flavor="dublincore/series")
                            mp.add(new_series)

                    else: 
                        mp.series = None
                        mp.series_title = None

                        catalog= mp.getCatalogs("dublincore/series")
                        if catalog:
                            mp.remove(catalog[0])

                else:
                    mp.metadata_episode[child.name]=child.get_text()

        mp.setTitle(mp.metadata_episode['title'])
        mp.setLanguage(mp.metadata_episode['language'])
        mp.metadata_episode['creator']=mp.creators
        mp.metadata_episode['contributor']=mp.contributors
        mp.metadata_episode['subject']=mp.subjects


    def edit_date(self,element,event):
        """Filter a Rigth button double click, show calendar and update date"""
      
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

    def __init__(self, parent, listing, text = None):
        """
        From a dict of series (series(id)=name) returns a ComboBoxEntry with a customize searcher
        """

        self.par = parent
        if text == None:
            text = " NO_SERIES " 
        self.text = text

        liststore = gtk.ListStore(str,str)
        liststore.append([text,None])
        if listing != None:
            for n, m in listing.iteritems():
                liststore.append([m,n]) # NAME ID
  
        liststore.set_sort_func(0,self.sorting,text) # Put text=NO_SERIES first
        liststore.set_sort_column_id(0,gtk.SORT_ASCENDING)


        # Filter
        combofilter = liststore.filter_new()
        combofilter.set_visible_func(self.filtering) 

        # Completion
        completion = gtk.EntryCompletion()
        completion.set_model(liststore)
        completion.set_match_func(self.filtering2, completion)
        completion.set_text_column(0)
        
        super(ComboBoxEntryExt, self).__init__(liststore,0)
     
        self.set_model(combofilter)
        self.child.set_completion(completion)

        # Signals   
        self.child.connect('changed',self.emit_filter,combofilter)
        self.child.connect('activate', self.activating)

    def activating(self, entry):
        text = entry.get_text()
        if text:
            if text not in [row[0] for row in self.liststore]:
                entry.set_text(self.text)
        return

    def emit_filter(self, origin, cfilter):
        cfilter.refilter()
        #combo.set_model

    def filtering2(self, completion, key_string, iterator, data = None):
        """Filtering completion"""
        model = completion.get_model()
        series = model.get_value(iterator,0)
        if series == self.text: # always show NO_SERIES
            return True
        elif key_string in series: # Show coincidence
            return True
        elif key_string == self.text:
            return True
        else:
            return False  
       
    def filtering(self, model, iterator):
        """Filtering ComboBox"""
        key_string = self.child.get_text()
        series =  model.get_value(iterator,0)
        if series == self.text: # always show NO_SERIES
            return True
        elif key_string in series: # Show coincidence
            return True
        elif key_string == self.text:
            return True
        else:
            return True

    def sorting(self, treemodel, iter1, iter2, NO_ID = None):
        """Sorting algorithm, placing first default series and no series"""
        if treemodel[iter1][0] == NO_ID:
            return False
        if treemodel[iter2][0] == NO_ID:
            return True
        if  treemodel[iter1][0] >  treemodel[iter2][0]:
            return True
        elif treemodel[iter1][0] == treemodel[iter2][0]: 
            if  treemodel[iter1][1] >  treemodel[iter2][1]:
                return True
            else:
                return False
        else:
            return False

gobject.type_register(MetadataClass)
gobject.type_register(ComboBoxEntryExt)
