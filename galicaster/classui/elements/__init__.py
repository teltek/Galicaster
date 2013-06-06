# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/classui/elements/__init__.py
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

from tracks import Tracks
from clock import Clock

class Chooser(gtk.VBox):
    # TODO made it resizable
    
    def __init__(self, variable, title, selector_type, values, preselection=None, fontsize=15, extra = None):
        gtk.VBox.__init__(self)
        self.set_size_request(300,-1)# NEW
        self.variable = variable
        self.text=title # maybe self.variable is best name for self.text
        self.options = values # TODO if boolean or list show proper options True/False ...
        self.preselected = preselection
        if selector_type != "boolean":
            self.title = gtk.Label(title) #TODO capitalize title    
        else:
            self.title = gtk.Label("") #TODO capitalize title
        self.title.modify_font(pango.FontDescription("bold "+str(fontsize)))
        self.pack_start(self.title, False, True, 0)
        self.title.set_alignment(0.5,0.0)
        self.selector = self.prepare_selector(self.text, selector_type, values, preselection, fontsize, extra)
        self.pack_start(self.selector, False, True, 15) # TODO proportional separation
        # It was False, True, so ask for more space

    def getTitle(self):
        self.title.get_text()
    
    def setTitle(self, title):
        self.title.set_text(title)
    
    def getValues(self): #define for each one
        self.options

    def getSelected(self): # define for each on to ensure getAll works
        return self.preselected
 
    def getAll(self): 
        return {self.variable: self.getSelected()}

    def prepare_selector(self, title, selector_type, values, selection,  fontsize, extra):
        #print title, selector_type
        if selector_type == "combo":
            return Combo(values, selection, fontsize)
        if selector_type == "list":
            return Tracks(values, selection, fontsize)
        if selector_type == "boolean":
            return Checkbox(title, selection)
        if selector_type == "selection":
            return Radiobox(values, selection, fontsize, extra)
        if selector_type == "toogle":
            return Togglebox(values, selection)
        if selector_type == "tree":
            return Listbox(values, selection)

    def resize(self, wprop=1, hprop=1):
        self.selector.resize(wprop, hprop)
        

class Combo(gtk.ComboBox): # WILL BE USED
    
    def __init__(self, values, preselection, font):
        liststore = gtk.ListStore(str,str) # real value, showable value
        gtk.ComboBox.__init__(self, liststore)
        for value in values:
            liststore.append([value,value]) #TODO get or transform to showable values

        cell = gtk.CellRendererText()
        self.pack_start(cell,True)
        self.add_attribute(cell,'text',1)

        self.prepare_selected(preselection)

        self.show_all()

    def prepare_selected(self, selected):        
        model = self.get_model()
        iterator = model.get_iter_first()
        while model.get(iterator,0)[0] != selected: 
            # Check iterator index
            iterator = model.iter_next(iterator)            
        self.set_active_iter(iterator)

    def getSelected(self):
        return self.get_active_text() # TODO text doesn't need to match option, so return option instead

class Checkbox(gtk.CheckButton): # UNUSED
    
      def __init__(self, text, preselection): 
          self.title = text
          gtk.CheckButton.__init__(self, text, False)
          #self.get_label().modify_font(pango.FontDescription(str(font)))
          self.set_active( preselection )
          self.show_all()

      def getTitle():
          return self.text

      def setTitle(self, title):
          self.set_label(title)

      def getSelected(self):
          return self.get_property('active')

class Radiobox(gtk.VButtonBox): # UNUSED

    def __init__(self, values, preselection, font, clock):
        
        gtk.VButtonBox.__init__(self)

        menu = []
        menu += [ gtk.RadioButton(label=values[0])]
        menu += [ gtk.RadioButton(menu[0],label=values[1])]
        menu += [ gtk.RadioButton(menu[0],label=values[2])]

        if clock:
            menu += [ Clock(12, 0 ,font) ]
            menu[len(menu)-1].set_sensitive( (preselection==clock) )
            menu[values.index(clock)].connect('toggled', self.change_clock)
        self.group = menu

        for element in menu:
            self.pack_start(element, False, False, 0)

        for element in menu:
            if type(element) is gtk.RadioButton:
                if element.get_label() == preselection:
                    element.set_active(True)

        self.show_all()

    def change_clock(self, button ):
        self.group[3].set_sensitive(not self.group[3].get_sensitive())
            
    def getSelected(self):
        for button in self.group.get_group():
            if button.get_active():
                return button.get_label()

class Togglebox(gtk.VButtonBox):

    def __init__(self, values, preselection):
        
        gtk.VButtonBox.__init__(self)

        self.set_layout(gtk.BUTTONBOX_EDGE)
        self.set_size_request(-1,130)
        menu = []
        
        for value in values:
            button = gtk.RadioButton(label=value)
            button.set_mode(False)
            button.set_can_focus(False)
            menu += [ button ]
            if values.index(value):
                button.set_group(menu[0])
            if value == preselection:
                button.set_active(True)
            
        self.group = menu

        for element in menu:
            print "add",element
            self.pack_start(element, False, True, 0) # TODO proportional to size

        self.show_all()
            
    def getSelected(self):
        for button in self.group.get_group():
            if button.get_active():
                return button.get_label()
          
    def resize(self, wprop=1, hprop=1):
        for button in self.get_children():
            button.set_property("width-request", int(wprop*150))
            button.set_property("height-request", int(wprop*50))
            label = button.get_children()[0]
            modification = str(int(hprop*20))
            label.modify_font(pango.FontDescription(modification))

class Listbox(gtk.ScrolledWindow):

    def __init__(self, values, preselection):
        
        gtk.ScrolledWindow.__init__(self)
        self.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.set_size_request(-1,206) # TODO get size from parents

        lista, self.view = self.prepare_view(1)# TODO get size from parent
        for value in values:
            lista.append(self.prepare_data(value))
        self.add(self.view)
        self.view.get_selection().select_iter(lista.get_iter_first()) # TODO select preselection
        self.show_all()


    def prepare_view(self, hprop): # TODO get hprop right

        lista = gtk.ListStore(object, str) 
        view = gtk.TreeView() 
        style=view.rc_get_style().copy()
        color = gtk.gdk.color_parse(str(style.base[gtk.STATE_SELECTED]))
        view.modify_base(gtk.STATE_ACTIVE, color)
        view.set_model(lista)
	view.get_selection().set_mode(gtk.SELECTION_SINGLE)
        view.set_headers_visible(False)
        view.columns_autosize()

        render = gtk.CellRendererText() 
        render.set_property('xalign',0.5)
        font = pango.FontDescription("bold "+str(int(hprop*20))) # TODO Get it by pixel size
        render.set_property('font-desc', font)
        render.set_fixed_height_from_font(2)
	column0 = gtk.TreeViewColumn("Operation", render, text = 1) # 
        
        view.append_column(column0)
        column0.set_sort_column_id(0)
        return lista,view

    def prepare_data(self, name): 
        data = [name[0], name[1]]
        return data
           
    def getSelected(self):# TODO test
        model,iterator = self.view.get_selection().get_selected()
        if type(iterator) is gtk.TreeIter:
            value = model.get_value(iterator,0)
            return value
        else:
            return "nothing selected"

          
      

