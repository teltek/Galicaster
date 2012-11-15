## -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/classui/profile
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.
"""
UI for the profile selector
"""


import gtk
import gobject
import pango

from galicaster.core import context
from galicaster.core import conf
from galicaster.recorder import get_modules

from galicaster.recorder.pipeline import v4l2
from galicaster.recorder.pipeline import vga2usb
from galicaster.recorder.pipeline import hauppauge
from galicaster.recorder.pipeline import pulse
from galicaster.recorder.pipeline import blackmagic
from galicaster.recorder.pipeline import videotest
from galicaster.recorder.pipeline import audiotest
from galicaster.recorder.pipeline import oldblackmagic

FLAVORS = ["presentation","presenter","other"]


class ProfileUI(gtk.Window):
    """
    Main window of the Profile Selector.
    It holds two tabs, one for profiles and another for tracks.
    """

    __gtype_name__ = 'ProfileUI'

    def __init__(self, parent=None, width = None, height=None, tester=False):
        """If tester is active, edition cappabilities are available"""
        if not parent:
            parent = context.get_mainwindow()
        size = context.get_mainwindow().get_size()
        width = int(size[0]/2.2)
        height = int(size[1]/2.0)
        gtk.Window.__init__(self)
        self.set_title(" ")
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.set_default_size(width,height)
        self.set_modal(True)
        if parent:
            self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
            self.set_transient_for(parent)
            self.set_destroy_with_parent(True)

        self.notebook = gtk.Notebook()
        self.notebook.set_show_tabs(False)
        self.add(self.notebook)
        
        self.list=ListProfileBox(self, size, tester)
        self.profile=None
        self.track=None       

        tab1 = gtk.Label("Profile Selector")
        self.append_tab(self.list,tab1)
        self.show_all()

    def append_tab(self, widget, label):
        """Add a tab with a new edition area"""
        self.notebook.append_page(widget,label)
        self.set_title(label.get_text())
        self.notebook.next_page()

    def remove_tab(self):
        """Once edition is finished, remove a edition tab"""
        current_num=self.notebook.get_current_page()
        self.notebook.prev_page()
        new_num = self.notebook.get_current_page()
        current=self.notebook.get_nth_page(current_num)
        if current == self.profile:
            self.profile = None
        elif current == self.track:
            self.track = None
        new=self.notebook.get_nth_page(new_num)
        self.notebook.remove_page(current_num)        
        text=self.notebook.get_tab_label(new).get_text()
        new.refresh()
        self.set_title(text)


    def close(self):
        """Handles UI closure, destroying tabs and updating changes"""
        if self.profile:
            self.profile.destroy()
        if self.track:
            self.track.destroy()
        context.get_conf().update()
        context.get_dispatcher().emit("reload-profile")
        self.destroy()          

class ProfileDialog(gtk.HBox):
    """
    Profiles Information of Galicaster
    """

    def __init__(self, parent=None, size=(1920,1080)):
        self.superior = parent
        wprop = size[0]/1920.0
        hprop = size[1]/1080.0
        self.wprop = wprop
        self.hprop = hprop
        gtk.HBox.__init__(self, False, int(wprop*5))

        self.set_border_width(int(wprop*20))
        self.vbox = gtk.VBox(False,0)

        self.buttons = gtk.VButtonBox()
        self.buttons.set_layout(gtk.BUTTONBOX_START)
        self.buttons.set_spacing(int(wprop*5))

        scrolled = gtk.ScrolledWindow()
        scrolled.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        
        self.list,self.view = self.prepare_view()  
        self.view.get_selection().connect("changed",self.append_info)
        scrolled.add(self.view)

        sidebox = gtk.VBox(False,0)  
        frame = gtk.Frame()

        label= gtk.Label("Profile Tracks")
        alist = pango.AttrList()
        font = pango.FontDescription("bold "+str(int(self.hprop*15)))
        attr=pango.AttrFontDesc(font,0,-1)
        alist.insert(attr)
        label.set_attributes(alist)

        frame.set_label_widget(label)
        frame.set_label_align(0.5,0.5)
        frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        align=gtk.Alignment(1,0.5,0.95,0.9)
        self.sidetable = gtk.Table(homogeneous=True)
        self.sidetable.set_size_request(int(wprop*300),-1)
        align.add(self.sidetable)
        frame.add(align)

        self.vbox.pack_end(scrolled, True, True, 0)
        self.pack_start(self.vbox, True, True, 0)
        sidebox.pack_start(self.buttons, False, False, int(hprop*10))
        sidebox.pack_start(frame, False, False, int(hprop*15))
        self.pack_start(sidebox,False,False,int(wprop*15))
        

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

    def append_profiles(self): 
        """Lists the available profiles"""
        profile_list = context.get_conf().get_profiles()        
        for name,profile in profile_list.iteritems():
            if not profile.to_delete:
                self.list.append(self.prepare_data(profile))      

    def append_info(self, selection = None):
        """Completes the profile auxiliar data on the right side of the box"""
        model,iterator = selection.get_selected()
        if not iterator:
            return None
        table = self.sidetable
        for child in table.get_children():
            table.remove(child)

        profile = model.get_value(iterator,0)        
        row=0
        for track in profile.tracks:           
            label = gtk.Label(track.flavor+":  ")
            label.set_alignment(1,0)
            label.set_width_chars(int(self.hprop*15))
            widget= gtk.Label(track.name)
            widget.set_alignment(0,0)
            widget.set_ellipsize(pango.ELLIPSIZE_END)
            alist = pango.AttrList()
            font = pango.FontDescription(str(int(self.hprop*13)))
            attr=pango.AttrFontDesc(font,0,-1)
            alist.insert(attr)
            label.set_attributes(alist)
            widget.set_attributes(alist)
            label.show()
            widget.show()
            table.attach(label,0,1,row,row+1,gtk.EXPAND|gtk.FILL,False,0,0)
            table.attach(widget,1,2,row,row+1,gtk.EXPAND|gtk.FILL,False,0,0)            
            row+=1           

    def append_tracks(self,profile):
        """Lists the available tracks on a profile"""
        for track in profile.tracks:
            self.list.append([track, track.name])       

    def show_tracks(self, button):
        """Change the tab to the track editor"""
        model,iterator = self.view.get_selection().get_selected()
        if type(iterator) is gtk.TreeIter:
            value = model.get_value(iterator,0)
            self.profile=ProfileBox(value,self.superior)
            tab2=gtk.Label(self.superior.get_title()+" > "+value.name)
            self.superior.append_tab(self.profile,tab2)
        
    def close(self,button=None):
        """Leaves and close the profile tab"""
        self.superior.remove_tab()        
        self.destroy()      

class ListProfileBox(ProfileDialog):
    def __init__(self, parent, size, tester = False):
        ProfileDialog.__init__(self, parent, size)

        select = self.add_button("Select",self.change_selected_profile)
        if tester:
            edit = self.add_button("Edit",self.show_tracks)        
            new = self.add_button("New", self.new_profile)                                         
            duplicate = self.add_button("Duplicate", self.duplicate_profile)
            delete = self.add_button("Delete", self.delete_profile)
        close=self.add_button("Close",self.close, True)

        self.append_profiles()
        self.select_current_profile()
        self.append_info(self.view.get_selection())
        self.show_all()    

    def select_current_profile(self):
        iterator =self.list.get_iter_first()
        while iterator != None:
            if self.list[iterator][1] == context.get_conf().get_current_profile().name:
                self.view.get_selection().select_iter(iterator)                
                text=self.list[iterator][1]               
                break
            iterator = self.list.iter_next(iterator)

        return self.list,iterator

    def prepare_data(self, profile):
        
        profile_name = profile.name
        presenter = []
        presentation = []
        other = []
        for track in profile.tracks:
            if track.flavor == "presenter":
                presenter.append(track.name)
            elif track.flavor == "presentation":
                presentation.append(track.name)
            elif track.flavor == "other":
                other.append(track.name)
        
        data = [
            profile, profile_name,
            #, ", ".join(presenter), ", ".join(presentation), ", ".join(other)     
            ]

        return data

    def prepare_view(self):        
        lista = gtk.ListStore(object, str)
        view = gtk.TreeView() 
        view.set_model(lista)
	view.get_selection().set_mode(gtk.SELECTION_SINGLE)
        view.set_headers_visible(False)
        view.columns_autosize()

        render = gtk.CellRendererText()
        #render.set_property('width-chars',25)
        render.set_property('xalign',0.5)
        #render.set_property('height', 40)
        font = pango.FontDescription("bold "+str(int(self.hprop*20)))
        render.set_property('font-desc', font)
        render.set_fixed_height_from_font(1)

        image = gtk.CellRendererPixbuf()

	column0 = gtk.TreeViewColumn("Profile", render, text = 1)
	column1 = gtk.TreeViewColumn("Current", image)
        column1.set_cell_data_func(image, self.show_current_image)
        view.append_column(column1)
        view.append_column(column0)

        column0.set_sort_column_id(1)
        lista.set_sort_func(1,self.sorting)
	lista.set_sort_column_id(1,gtk.SORT_ASCENDING)          
        return lista,view  

    def sorting(self, treemodel, iter1, iter2):
        first = treemodel[iter1][1]
        second = treemodel[iter2][1]

        if first == "Default" or first < second:
            return -1
        elif second == "Default" or second < first:
            return 1

    def show_current_image(self, column, cell, model, iterator, data=None):
        profile = model[iterator][0]
        if profile == context.get_conf().get_current_profile():
            cell.set_property("stock-id", gtk.STOCK_YES)
        else:
            cell.set_property("stock-id", 0)
        return None
    
    def change_selected_profile(self, button):

        model,iterator=self.view.get_selection().get_selected()
        if type(iterator) is gtk.TreeIter:
            profile=model.get_value(iterator,0)
            
            context.get_conf().change_current_profile(profile.name)
        #self.refresh()
        self.close()

    def delete_profile(self, origin):
        model,iterator = self.view.get_selection().get_selected()
        if type(iterator) is not gtk.TreeIter:
            return

        profile = model.get_value(iterator,0)
        if profile.name == "Default":
            return

        if profile == context.get_conf().get_current_profile():
            context.get_conf().set_default_profile_as_current()            
            
        profile.to_delete = True
        model.remove(iterator)
        self.refresh()

    def new_profile(self, origin):
        new = conf.Profile("New Profile")
        new.path = context.get_conf().get_free_profile()
        ProfileBox(new,self.superior)
        self.superior.profile=ProfileBox(new,self.superior)
        tab2=gtk.Label(self.superior.get_title()+" > "+new.name)
        self.superior.append_tab(self.superior.profile,tab2)
        return new

    def duplicate_profile(self, origin):
        model,iterator = self.view.get_selection().get_selected()
        if type(iterator) is not gtk.TreeIter:
            return

        profile = model.get_value(iterator,0)
        
        new_profile = conf.Profile (                                    
            profile.name+" copy",
            context.get_conf().get_free_profile()
            )
        
        for track in profile.tracks:
            new_profile.add_track(track)
        context.get_conf().add_profile(new_profile)
        self.refresh()

    def refresh(self):
        self.list.clear()
        self.append_profiles()
        self.select_current_profile()

    def close(self, button=None):
        self.superior.close()
        

class ProfileBox(ProfileDialog):

    def __init__(self, profile, parent):
        """
        Fills the Track tab with the track data of a profile
        """
        ProfileDialog.__init__(self, parent)
        self.profile = profile
        new = self.add_button("Save", self.save_profile)        
        edit = self.add_button("Edit", self.edit_track)        
        new = self.add_button("New track", self.new_track)  
        delete = self.add_button("Delete track",self.delete_track) 
        close = self.add_button("Cancel", self.close, True)    

        self.append_tracks(profile)
        self.profile_name = gtk.Entry()
        self.profile_name.set_text(profile.name)
        self.vbox.pack_start(self.profile_name,False,False,10)

        self.show_all()
    
    def prepare_view(self): 
        """Creates the list and the view of available tracks."""
        lista = gtk.ListStore(gobject.TYPE_PYOBJECT, str)
        view = gtk.TreeView() 
        view.set_model(lista)
	view.get_selection().set_mode(gtk.SELECTION_SINGLE)
        render = gtk.CellRendererText()
	column0 = gtk.TreeViewColumn("Tracks", render, text = 1)
	#column1 = gtk.TreeViewColumn("Presenter", render, text = 1)
	#column2 = gtk.TreeViewColumn("Presentation", render, text = 2)
	#column3 = gtk.TreeViewColumn("Other", render, text = 3)
        view.append_column(column0)
        #view.append_column(column1)
        #view.append_column(column2)
        #view.append_column(column3)
        return lista,view

    def edit_track(self, origin):
        """Pops up the track editor for a given track"""
        model,iterator = self.view.get_selection().get_selected()
        if type(iterator) is gtk.TreeIter:            
            track = model.get_value(iterator,0)
            tab3=gtk.Label(self.superior.get_title()+" > "+track.name)
            edit = TrackBox(self.profile, track, self.superior)
            self.superior.track=edit 
            self.superior.append_tab(edit,tab3)
            return track
        return None
        
    def new_track(self, origin):
        """Creates a new track on a given profile and pops up the editor"""
        new=conf.Track()
        tab3=gtk.Label(self.superior.get_title()+" > "+"New Track")
        self.superior.track=TrackBox(self.profile,new, self.superior)
        self.superior.append_tab(self.superior.track,tab3)
        return new
        
    def delete_track(self, origin):
        """Deletes a given track of the current profile in edition"""
        model,iterator = self.view.get_selection().get_selected()
        if type(iterator) is gtk.TreeIter:
            track = model.get_value(iterator,0)
            self.profile.remove_track(track)
            model.remove(iterator)
            self.refresh()

    def save_profile(self, origin):
        """Saves to memory the modification of a profile"""
        old_key=self.profile.name
        self.profile.name = self.profile_name.get_text()        
            
        if not context.get_conf().get_profiles().has_key(self.profile.name):
            CONF= context.get_conf()
            CONF.add_profile(self.profile,old_key)
            if self.profile == CONF.get_current_profile():
                CONF.force_set_current_profile(self.profile.name)
            
        self.close()   
        return self.profile

    def refresh(self):
        """After edition, refreshes profile values"""
        self.list.clear()
        self.append_tracks(self.profile)

    def close(self,button=None):
        """Leaves and close a track tab"""
        self.superior.remove_tab() 
        self.destroy() 


class TrackBox(gtk.HBox):
    """
    Track editor and tester
    """
    def __init__(self, profile=None, device=None, parent=None):
        """Edit manager for track of device in a profile"""
        self.superior = parent
        gtk.HBox.__init__(self, False, 5)
        self.set_border_width(20)
        self.profile = profile
        self.device = device

        self.buttons = gtk.VButtonBox()
        self.buttons.set_layout(gtk.BUTTONBOX_START)
        self.buttons.set_spacing(5)

        save = self.add_button("Save", self.retrieve_data)        
        #test = self.add_button("Test", self.test_track, True)      
        cancel = self.add_button("Cancel", self.close, True)  

        self.table = None
        self.model = None

        if device.device:
            self.table,self.model,self.combo = self.prepare_device(device)
            self.combo.connect("changed",self.show_options)
        else:
            self.table,self.model,self.combo = self.prepare_empty_device()
            self.combo.connect("changed",self.show_options)

        self.table.attach(self.combo,1,2,0,1,0,0)
        self.pack_start(self.table,True,True,0)
        self.pack_start(self.buttons,False,False,20)
        self.show_all() 


    def add_button(self, text, connection, end=False): 
        """Adds an action button to the right side of the Box"""
        k1 = 1
        button = gtk.Button(text)
        button.set_property("width-request", int(k1*150))
        button.set_property("height-request", int(k1*50))
        label = button.get_children()[0]
        modification = str(20)
        label.modify_font(pango.FontDescription(modification))
        if not end:
            self.buttons.pack_start(button)
        else:
            self.buttons.pack_end(button)
        button.connect("clicked",connection)
        return button

    def prepare_empty_device(self):
        """Pops up an empty track"""
        table = gtk.Table(2, 2, True) 
        label=gtk.Label("Type")
        label.set_width_chars(20)
        label.set_alignment(0.0,0.5)


        table.attach(label,0,1,0,1,0,0)
        liststore = gtk.ListStore(str,gobject.TYPE_PYOBJECT)
        modules=get_modules()
        for name,klass in modules.iteritems():
            liststore.append([name,klass])
        types = gtk.ComboBox(liststore)
        cell = gtk.CellRendererText()
        types.pack_start(cell,True)
        types.add_attribute(cell,'text',0)
        types.set_name("device")
        return table,liststore,types

    def prepare_device(self, selected):
        """Pops up an existing track"""
        table,model,types = self.prepare_empty_device()
        iterator = model.get_iter_first()
        while model.get(iterator,0)[0] != selected.device: 
            # Check iterator index
            iterator = model.iter_next(iterator)            
        types.set_active_iter(iterator)
        self.show_options(types,table)

        for child in table.get_children():
            if child.name:
                try:
                    self.set_random_data(child,selected[child.name])
                except:
                    print child.name + " had a data problem"    

        return table,model,types
    

    def show_options(self, origin, table= None):
        """Creates the text and menu widget for every possible value on a given track"""
        if table == None:
            table = self.table
        model = origin.get_model()

        for child in table.get_children():
            if type(child) is gtk.Label and child.get_text()=="Type":
                pass
            elif child == origin:        
                pass
            else:
                table.remove(child)
        table.resize(1,1)
        klass = model[origin.get_active()][1]
        options = klass.gc_parameters

        row=2
        for name in klass.order:
            values=options[name]
        #for name,values in options.iteritems():
            kind = values["type"]
            label=gtk.Label(name.title())
            label.set_width_chars(20)
            label.set_alignment(0.0,0.5)
            table.attach(label,0,1,row,row+1,False,False,0,0)
            if kind in [ "text", "device", "caps"]  :
                widget = gtk.Entry()
                widget.set_text(values['default'])
                widget.set_alignment(0.0)
                
            elif kind == "flavor":
                store = gtk.ListStore(str)
                widget = gtk.ComboBox(store)
                for option in FLAVORS:
                    store.append([option])
                cell = gtk.CellRendererText()
                widget.pack_start(cell,True)
                widget.add_attribute(cell,'text',0)
                widget.set_active(FLAVORS.index(values['default']))

            elif kind == "integer":
                adjust = gtk.Adjustment(
                    values["default"],values["range"][0],
                    values["range"][1],1,1)
                widget = gtk.SpinButton(adjust,1.0,0)
                widget.set_alignment(0.0)

            elif kind == "float":
                adjust = gtk.Adjustment(
                    values["default"],values["range"][0],
                    values["range"][1],0.1,1)
                widget = gtk.SpinButton(adjust,0.1,1)
                widget.set_alignment(0.0)

            elif kind == "boolean":
                widget=gtk.CheckButton("Active")
                if values['default'] in ["False", "false", "no", "No",]:
                    widget.set_mode(False)
                else:
                    widget.set_mode(True)
                widget.set_alignment(0.0,0.5)

            elif kind == "select":
                store = gtk.ListStore(str) 
                widget = gtk.ComboBox(store)
                for value in values['options']:
                    store.append([value])
                cell = gtk.CellRendererText()
                widget.pack_start(cell,True)
                widget.add_attribute(cell,'text',0)
                widget.set_active(values['options'].index(values['default']))
            widget.set_name(name)
            if kind not in ['integer', 'float']:
                table.attach(widget,1,2,row,row+1,gtk.FILL,False,0,0)
            else:
                table.attach(widget,1,2,row,row+1,False,False,0,0)
            label.show()
            widget.show()
            row+=1

    def retrieve_data(self, button=None):
        """Reads random data for a track variable"""
        for child in self.table.get_children():            
            if child.name:
                self.device[child.name] = str(self.get_random_data(child))
        if self.device not in self.profile.tracks:
            self.profile.add_track(self.device)

        self.close()
        return self.device    

    def get_random_data(self, widget):
        """Depending on the widget type, retrieves the active value"""
        if type(widget) is gtk.Entry:
            return widget.get_text()
        elif type(widget) is gtk.CheckButton:
            return widget.get_active()
        elif type(widget) is gtk.ComboBox:
            return widget.get_active_text()            
        elif type(widget) is gtk.SpinButton:
            return widget.get_text()

    def set_random_data(self, widget, data):
        """Depending on the widget type, sets a new active value"""
        if type(widget) is gtk.Entry:
            widget.set_text(data)

        elif type(widget) is gtk.CheckButton:
            if data in [ "Active", "active"]:
                widget.set_active(True)
            else:
                widget.set_active(True)

        elif type(widget) is gtk.ComboBox:
            model = widget.get_model()
            iterator=model.get_iter_first()
            while model.get(iterator,0)[0] != data:# check iterator index
                iterator = model.iter_next(iterator)
            widget.set_active_iter(iterator)

        elif type(widget) is gtk.SpinButton: 
            data = float(data)
            widget.set_value(data)

    def test_track(self, button=None):
        """Pops up a Test window for the current track"""
        device = {}
        for child in self.table.get_children():            
            if child.name:
                device[child.name] = str(self.get_random_data(child))
        #TestWindow(device)    

    def close(self,button=None):
        """Leaves and close a track tab"""
        self.superior.remove_tab()
        self.destroy()
