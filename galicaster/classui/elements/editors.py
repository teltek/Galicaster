# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/classui/elements/editors
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.
"""
This module holds different elements to provide selection interface for single variables related to metadata
"""

import gtk
import pango
import gobject
import datetime
from galicaster.classui.calendarwindow import CalendarWindow
from galicaster.utils.iso639 import get_iso_name

NO_SERIES  = "NO SERIES ASSIGNED"
DEFAULT_SERIES = "DEFAULT SERIES"

class Editor(gtk.HBox): # TODO tooltip missing everywhere

    def __init__(self, group, variable, label, size, fontsize):

        gtk.HBox.__init__(self)
        self.wprop = size[0]/1920.0
        self.hprop = size[0]/1080.0
        # TODO get panoramic or 4:3ish
        self.group = group
        self.variable = variable

        label = gtk.Label(label+":")
        label.set_justify(gtk.JUSTIFY_LEFT)
        label.set_alignment(0,0)
        modification = str(int(self.hprop*fontsize))+"px"   
        label.modify_font(pango.FontDescription(modification))
        label.set_width_chars(12)
        self.pack_start(label, False, True, 0)

class Viewer(gtk.HBox):

    def __init__(self, group, variable, label, size, fontsize): 

        gtk.HBox.__init__(self)
        self.wprop = size[0]/1920.0
        self.hprop = size[0]/1080.0
        # TODO get panoramic or 4:3ish
        self.group = group
        self.variable = variable

        label = gtk.Label(label+":")
        label.set_justify(gtk.JUSTIFY_LEFT)
        label.set_alignment(0,0)
        modification = str(int(self.hprop*fontsize))+"px"   
        label.modify_font(pango.FontDescription(modification))
        label.set_width_chars(12)
        self.pack_start(label, False, False, 0)

class TextViewer(Viewer):

    def __init__(self, group, variable, label, size = [1920,1080], fontsize=12, default=""):

        Viewer.__init__(self, group, variable, label, size, fontsize)
        self.set_size_request(500, -1) # for the HBOX, maybe on Main Class
        self.widget = gtk.Label()
        self.widget.set_justify(gtk.JUSTIFY_LEFT)
        self.widget.set_alignment(0,0)
        modification = str(int(self.hprop*fontsize))+"px"   
        self.widget.modify_font(pango.FontDescription(modification))
        self.setValue(default)
        self.pack_start(self.widget, True, True, 0)

    def setValue(self, value):
        self.widget.set_text( value )
        
    def getValue(self):
        value = self.widget.get_text()
        return (self.group, self.variable, value )

class DatetimeViewer(Viewer):

    def __init__(self, group, variable, label, size = [1920,1080], fontsize=12, default=""):

        Viewer.__init__(self, group, variable, label, size, fontsize)
        self.set_size_request(500, -1) # for the HBOX, maybe on Main Class
        self.widget = gtk.Label()
        self.widget.set_justify(gtk.JUSTIFY_LEFT)
        self.widget.set_alignment(0,0)
        modification = str(int(self.hprop*fontsize))+"px"   
        self.widget.modify_font(pango.FontDescription(modification))
        self.setValue(default)
    
    def setValue(self, value):
        self.widget.set_text( value )
        
    def getValue(self):
        value = self.widget.get_text()
        return (self.group, self.variable, value )


class TextEditor(Editor):

    def __init__(self, group, variable, label, default, size=[1920, 1080], fontsize = 12, options = []):
        # TODO include tooltip
        Editor.__init__(self, group, variable, label, size, fontsize)
        self.set_size_request(500, -1)
        self.widget = gtk.Entry()
        self.setValue(default)
        modification = str(int(self.hprop*fontsize))+"px"   
        self.widget.modify_font(pango.FontDescription(modification))
        self.pack_start(self.widget, True, True, 0)
    
    def setValue(self, value):
        self.widget.set_text( value )
        
    def getValue(self): # TODO strip spaces 
        value = self.widget.get_text()
        return ( self.group, self.variable, value )

class SelectEditor(Editor):

    def __init__(self, group, variable, label, default, size=[1920, 1080], fontsize = 12, options = []):
        # TODO include tooltip
        Editor.__init__(self, group, variable, label, size, fontsize)
        self.set_size_request(500, -1)
        self.widget = gtk.Combo()
        self.widget.set_popdown_strings(options)
        self.setValue(default)
        modification = str(int(self.hprop*fontsize))+"px"   
        self.widget.modify_font(pango.FontDescription(modification))
        self.pack_start(self.widget, True, True, 0)
    
    def setValue(self, value):
        self.widget.set_value_in_list( value )
        
    def getValue(self): # TODO strip spaces 
        value = self.widget.get_text()
        return ( self.group, self.variable, value )

class LanguageEditor(Editor):
    
    def __init__(self, group, variable, label, default, size=[1920, 1080], fontsize = 12, options = []):
        Editor.__init__(self, group, variable, label, size, fontsize)
        self.set_size_request(-1, -1)
        liststore = gtk.ListStore(str, str) # TODO real value, showable value
        self.widget = gtk.ComboBox(liststore)
        for value in options:
            liststore.append([value,str(get_iso_name(value))])
        cell = gtk.CellRendererText()
        self.widget.pack_start(cell,True)
        self.widget.add_attribute(cell,'text',1)
        modification = str(int(self.hprop*fontsize))+"px"           
        font = pango.FontDescription(modification)
        cell.set_property('font-desc', font)

        self.setValue(default)
        self.pack_start(self.widget, True, True, 0)   

    def setValue(self, value):
        model = self.widget.get_model()
        iterator = model.get_iter_first()
        while model.get(iterator,0)[0] != value:            
            iterator = model.iter_next(iterator)            
        self.widget.set_active_iter(iterator)

    def getValue(self):
        pair = self.widget.get_active() # TODO return ISO
        value = self.widget.get_model()[pair][0]
        return ( self.group, self.variable, value)


class DatetimeEditor(Editor):

    def __init__(self, group, variable, label, default, size=[1920, 1080], fontsize = 12, options = []):
        # TODO include tooltip
        Editor.__init__(self, group, variable, label, size, fontsize)
        self.set_size_request(-1, -1)
        self.widget = gtk.Button()
        self.label = gtk.Label()
        self.widget.add(self.label)
        self.label.set_padding(20,0) # TODO make it proportional

        modification = str(int(self.hprop*fontsize))+"px"           
        self.label.modify_font(pango.FontDescription(modification))
        self.setValue(default)
        self.widget.connect("clicked",self.edit_date)
        self.pack_start(self.widget, False, True, 0)
    
    def setValue(self, value):
        if isinstance(value, datetime.datetime):
            self.label.set_text( value.replace(microsecond=0).isoformat() ) # MAYBE Remove T??
        else:
            self.label.set_text( value )
        
    def getValue(self): # TODO transform into isoformat
        value = self.label.get_text()
        value = datetime.datetime.strptime(value,"%Y-%m-%dT%H:%M:%S") # IF represatn
        return ( self.group, self.variable, value )

    def edit_date(self,element,event = None):
        """Filter a Rigth button double click, show calendar and update date"""

        try:
            date=datetime.datetime.strptime(self.label.get_text(),"%Y-%m-%dT%H:%M:%S") 
        except ValueError:
            date=0
        v = CalendarWindow(date)
        v.run()
        if v.date != None:
            self.label.set_text(v.date.isoformat())
        return True


class SeriesEditor(Editor):
    
    def __init__(self, group, variable, label, default, size=[1920, 1080], fontsize = 12, options = []):

        Editor.__init__(self, group, variable, label, size, fontsize)
        self.set_size_request(500, -1)
        self.widget = ComboBoxEntryExt(options, NO_SERIES) # TODO create list better
        modification = str(int(self.hprop*fontsize))+"px"   
        self.widget.child.modify_font(pango.FontDescription(modification))
        cell = self.widget.get_cells()[0]
        cell.set_property('font-desc', pango.FontDescription(modification) )
        vbox = gtk.VBox()
        vbox.pack_start(self.widget)
        self.extra = vbox
        self.pack_start(vbox, True, True, 0)
        self.setValue(default)

    def setValue(self, value):
        model = self.widget.get_model()
        iterator = model.get_iter_first()
        while model.get(iterator,0)[0] != value:            
            iterator = model.iter_next(iterator)            
        self.widget.set_active_iter(iterator)
        self.widget.child.set_text( value )
    
        #print self.extra.get_children()
        #self.extra.pack_start(gtk.Label("id:"))
        
    def getValue(self):
        pair = self.widget.get_active() 
        value = self.widget.get_model()[pair][0] # MAYBE use Text for showing an ID as valid value
        return ( self.group, self.variable, value)

class ComboBoxEntryExt(gtk.ComboBoxEntry):

    def __init__(self, listing, text = None):
        """
        From a dict of series (series(id)=name) returns a ComboBoxEntry with a customize searcher
        """

        if text == None:
            text = " NO_SERIES " 
        self.text = text

        liststore = gtk.ListStore(str,str)
        liststore.append([text,None])
        if listing != None:
            for key,all_values in listing.iteritems():
                liststore.append([all_values['title'], key]) # NAME ID
  
        liststore.set_sort_func(0,self.sorting,text) # Put text=NO_SERIES first
        liststore.set_sort_column_id(0,gtk.SORT_ASCENDING)

        self.liststore = liststore # CHECK

        # Filter
        combofilter = liststore.filter_new()
        combofilter.set_visible_func(self.filtering) 

        # Completion
        completion = gtk.EntryCompletion()
        completion.set_model(liststore)
        completion.set_match_func(self.filtering_match, completion)
        completion.set_text_column(0)
        completion.set_inline_selection(True)
        
        super(ComboBoxEntryExt, self).__init__(liststore,0)
     
        self.set_model(combofilter)
        self.child.set_completion(completion)

        # Signals   
        self.child.connect('changed',self.emit_filter,combofilter)
        self.child.connect('activate', self.activating)
        self.child.connect('focus-out-event', self.ensure_match)
        
    def ensure_match(self, origin , event):
        text = self.child.get_text()
        model = self.get_model()
        match = False
        for iterator in model:
            if not match and text in iterator[0]:
                match = True
                self.child.set_text(iterator[0])
        if not match:
            self.child.set_text(self.text)
        return False                

    def activating(self, entry):
        text = entry.get_text()
        if text:
            if text not in [row[0] for row in self.liststore]:
                entry.set_text(self.text)
        return

    def emit_filter(self, origin, cfilter):
        cfilter.refilter()

    def filtering_match(self, completion, key_string, iterator, data = None):
        """Filtering completion"""
        model = completion.get_model()
        series = model.get_value(iterator,0)
        if series == self.text: # always show NO_SERIES
            return True
        elif key_string.lower() in series.lower(): # Show coincidence
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
        elif key_string.lower() in series.lower(): # Show coincidence
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

gobject.type_register(ComboBoxEntryExt)
gobject.type_register(Editor)
gobject.type_register(Viewer)
