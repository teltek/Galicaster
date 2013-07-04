# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/ui/listing
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import gtk
import gobject
import pango

from galicaster.classui.managerui import ManagerUI
from galicaster.core import context
from galicaster.mediapackage import mediapackage
from galicaster.classui import get_ui_path
from galicaster.classui.operations import OperationsUI
from galicaster.operations import loader
from galicaster.utils import readable
from galicaster.classui import message

logger = context.get_logger()

rcstring = """
style "big-scroll" {
    GtkRange::stepper-size = 20
    GtkRange::slider-width = 25
}

class "GtkRange" style "big-scroll"

"""

gtk.rc_parse_string(rcstring)
#gtk.rc_reset_styles(self.main_window.get_settings())


class ListingClassUI(ManagerUI):
    """
    Create Recording Listing in a VBOX with TreeView from an MP list
    """
    __gtype_name__ = 'Listing'

    def __init__(self):
        ManagerUI.__init__(self, 3, 1, "Media Manager")
        self.reference = 1

        self.create_ui()
	self.vista.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        # COLOR PALETTE
	old_style = context.get_conf().get_color_style()
	self.color = context.get_conf().get_palette(old_style)
	
	self.dispatcher.connect("refresh-row", self.refresh_row_from_mp, self.reference)
	self.dispatcher.connect("galicaster-status", self.event_change_mode)
	self.dispatcher.connect("start-operation", self.refresh_operation)
	self.dispatcher.connect("stop-operation", self.refresh_operation)
		
        # populate treeview
	self.populate_treeview(self.repository.list().values())
	self.box.pack_start(self.strip,False,False,0)
	self.box.reorder_child(self.strip,0)
	self.box.show()
	self.pack_start(self.box,True,True,0)		
	
    def event_change_mode(self, orig, old_state, new_state):
        if new_state == self.reference :
            self.refresh()

    def insert_data_in_list(self, lista, mps):
        lista.clear()
        for mp in mps:
            if mp.status != mediapackage.SCHEDULED:
                lista.append([mp, mp.getStartDateAsString()])

    def set_columns(self):

        # Definition  
        renderTitle = gtk.CellRendererText()
        renderTitle.set_property('ellipsize', pango.ELLIPSIZE_END)
        renderTitle.set_property('xalign',0.0)
        renderTitle.set_property('background', self.color[0])
        renderText =  gtk.CellRendererText()
        renderText.set_property('xalign',0.0)
        renderText.set_property('background', self.color[0])
        renderValue = gtk.CellRendererText()
        renderValue.set_property('xalign', 0.5)
        renderValue.set_property('background', self.color[0])
        renderOperation = gtk.CellRendererText()
        renderOperation.set_property('xalign', 0.5)

	ops = loader.get_operations()
        shortnames = []
        for op in ops:
            shortnames += [ op[0][1].get("shortname") ]

        title = { "column-title" : "Title", 'render' : renderTitle, 'function' : self.render_title,
                  "fixed-width" : 200, "wprop" : 56, "sorting": self.sort }
        presenter = { "column-title" : "Presenter", 'render' : renderText, 'function' : self.render_presenter,
                      "fixed-width" : 125, "wprop" : 27, "sorting": self.sorting_empty }
        series = { "column-title" : "Series", 'render' : renderText, 'function' : self.render_series,
                   "fixed-width" : 135, "wprop" : 33, "sorting": self.sorting_empty }
        date = { "column-title" : "Date", 'render' : renderText, 'function' : self.render_date,
                 "fixed-width" : 140, "wprop" : 23, "sorting": self.sort }
        size = { "column-title" : "Size", 'render' : renderValue, 'function' : self.render_size,
                 "fixed-width" : 88, "wprop" : 14, "sorting": self.sort }
        duration = { "column-title" : "Duration", 'render' : renderValue, 'function' : self.render_duration,
                     "fixed-width" : 93, "wprop" : 10, 'sorting': self.sort  }
        definitions = [ date, title, presenter, series, size, duration]
        if self.reference == 1:
            for op in shortnames:
                operation = {"column-title" : op, 'render' : renderOperation, 
                             'function' : self.render_operation, "fixed-width" : 95, "wprop" : 8, 
                             'sorting': self.sort  }
                definitions += [ operation]

        columns = []

        for value in definitions:
            column = gtk.TreeViewColumn( value["column-title"], value['render'])
            column.set_fixed_width(value["fixed-width"])
            column.set_cell_data_func(value['render'], value['function'], 
                                      None if value['render'] != renderOperation else value['column-title'])
            column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            columns += [column]
            column.set_sort_column_id(len(columns))
            self.vista.append_column(column)
            if value == title:
                column.set_expand(True)
            if value.has_key('sorting'):
                self.lista.set_sort_func(len(columns), 
                                         value['sorting'], 
                                         value['column-title'])
        return definitions, columns

    def populate_treeview(self, mp):
	self.lista = gtk.ListStore(object, str) # Just mp
        self.insert_data_in_list(self.lista, mp) # insert all mps
        definitions, columns = self.set_columns()

	vbar = self.scroll.get_vscrollbar()
	vbar.set_update_policy(gtk.UPDATE_DELAYED)
                
        self.definitions = definitions
        self.columns = columns

	self.vista.set_model(self.lista)
	self.vista.set_headers_clickable(True)

	self.vista.connect('row-activated',self.on_double_click)
	self.vista.connect('button-release-event',self.menu)

        self.lista.set_sort_column_id(1 ,gtk.SORT_ASCENDING) # Sort by Date column
        self.vista.show()

   
    def render_title(self, column, cell, model, iterator, user_data = None ): 
        mp = model[iterator][0]
        cell.set_property('text', mp.getTitle())

    def render_presenter(self, column, cell, model, iterator, user_data = None ):
        mp = model[iterator][0]
        cell.set_property('text', mp.getCreator())

    def render_series(self, column, cell, model, iterator, user_data = None ):
        mp = model[iterator][0]
        cell.set_property('text', mp.series_title)

    def render_size(self, column, cell, model, iterator, user_data = None ):
        mp = model[iterator][0]
        value = mp.getSize()
        result = readable.size(value)
        cell.set_property('text', result) 

    def render_date(self, column, cell, model, iterator, user_data = None ):
        mp = model[iterator][0]
        value = mp.getStartDateAsString()
        result = readable.date(value)
        cell.set_property('text', result)

    def render_duration(self, column, cell, model, iterator, user_data = None ):
        mp = model[iterator][0]
        value = mp.getDuration() if mp.getDuration() else 0
        result = readable.time(int(value)/1000)
        cell.set_property('text', result)

    def render_operation(self, column, cell, model, iterator, user_data = None ):
        mp = model[iterator][0]
        status = mp.getOpStatus(user_data)
        old_style = context.get_conf().get_color_style()
        palette = context.get_conf().get_palette()
        color = self.color[status] if old_style else palette[status]
        cell.set_property('background', color)
        if status > 1:
            cell.set_property('foreground', "#FFFFFF")
        else:
            cell.set_property('foreground', "#333333")
        cell.set_property('text', mediapackage.op_status[status] )

    def refresh_treeview(self):
	"""Refresh all the values on the list"""
	logger.info("Refreshing TreeView")
	model, selected = self.vista.get_selection().get_selected_rows()
	self.repository.refresh()
	self.insert_data_in_list(self.lista, self.repository.list().values())

	s = 0 if len(selected) == 0 else selected[0][0]
	self.vista.get_selection().select_path(s)

    def refresh_row_from_mp(self, origin, identifier, reference):
	"""Refresh the values of a single row"""
	# Search Iter to the liststore
        if self.reference != reference:
            return True
	i = None
	for row in self.lista:
	    if row[0].getIdentifier() == identifier:
                i = row.iter

        mp = self.repository.get(identifier)
        if i:
            self._refresh(mp,i)

    def refresh_operation(self, origin, operation, package, success = None):
        """Refresh the status of an operation in a given row"""
        identifier = package
        if not isinstance(package, unicode):
            identifier = package.getIdentifier()
	self.refresh_row_from_mp(origin, identifier, self.reference)

    def refresh_row(self,reference,i):# FIXME keep the sort id 
        mp = self.lista[i][0] # FIXME set the id as the first metadata
	#mp = self.repository.get(mpid)
	self._refresh(mp,i)

    def _refresh(self,mp,i):
        self.lista.set(i, 0, mp)
        self.lista.set(i, 1, mp.getStartDateAsString())
	
    def refresh(self,element=None,package=None):
        # self refresh_row()
        self.refresh_treeview()
	return True

    def get_deletable(self, packages):
        ops = loader.get_operations()
        shortnames = []
        for op in ops:
            shortnames += [ op[0][1].get("shortname") ]

        not_deletable = set()
        for mp in packages:
            for op in shortnames:
                if mp.getOpStatus(op) not in [0, 4, 5]:
                    not_deletable.update([mp])

        return list(not_deletable)

    def get_executable(self, packages, operation):
        not_exectuble = []
        for mp in packages:
            if mp.getOpStatus(operation) not in [0, 4, 5]:
                not_deletable += [ mp]
        return not_executable

	
#---------------------------- MOUSE AND SELECTION MANAGMENT --------------------


    def on_action(self, action):
        """When an action its selected calls the function associated"""	
	op=action.get_property("tooltip-text")
	if not isinstance(op,str):
            op=action.get_label()

	logger.info("ON_action >> "+op)

        selection = self.vista.get_selection()
        store,rows = selection.get_selected_rows()
        if not len(rows) and not op.count("Empty"):
            self.on_noselection()
        else:
            available = self.active_operations(store,rows)
            if op == "Play": # TODO get attribute on_$operation
                last = store.get_iter(rows[len(rows)-1])
                self.on_play(store, None, last)
            elif op.count("Edit"):
                last = store.get_iter(rows[len(rows)-1])
                self.on_edit(store, None, last)
            elif op.count("Delete"):
                if self.reference == 1:
                    self.on_archive(store, rows)
                elif self.reference == 4:
                    self.on_delete(store, rows)
            elif op.count("Restore"):
                self.on_restore(store, rows)
            elif op.count("Empty"):
                self.on_empty()
            elif op == "Trash":
                self.on_trash()
            elif op == "Info":
                last = store.get_iter(rows[len(rows)-1])
                self.on_info(store, None, last)
            elif op.count("New"):
                self.on_operations_question(store, rows, 0)
            elif op.count("Clear"):
                if available:
                    self.on_operations_question(store, rows, 1)
                else:
                    self.on_no_available()                   
                    
            elif op.count("Execute"):
                if available:
                    self.on_operations_question(store, rows, 2)
                else:
                    self.on_no_available()         
            else:
                logger.debug('Invalid action: {0}'.format(op))

    def active_operations(self, store, rows):
        packages = []
        for c in rows:
            iterator = store.get_iter(c)
            packages += [ store[iterator][0] ] 
        active = True if loader.get_nightly_operations( packages ) else False
        return active

    

    def create_menu(self):
        """Creates a menu to be shown on right-button-click over a MP"""
	menu = gtk.Menu()
	if self.conf.get_boolean('ingest', 'active'):
            operations = ["Play", "Edit", "Operations", "Info", "Delete"]
	else:
	    operations = ["Play", "Edit", "Info", "Delete"]

        for op in operations:
            item = gtk.MenuItem(op)
	    menu.append(item)
	    item.connect("activate", self.on_action)
	    item.show()
	return menu


    def menu(self,widget,event):
        """ 
	If rigth-button is clicked: ensure proper selection, get row,  create menu and pop it
	"""		
	if event.button == 3:
            reference,column,xcell,ycell = widget.get_path_at_pos(int(event.x),int(event.y))
	    c = self.lista.get_iter(reference)
	    self.vista.get_selection().unselect_all()
	    self.vista.get_selection().select_iter(c)	
	    menu = self.create_menu()
	    menu.popup(None,None,None,event.button,event.time)
	    menu.show()
	    return True
	return False


    def on_double_click(self,treeview,reference,column):
        """Set the player for previewing if double click"""
	self.on_play(treeview.get_model(),reference,treeview.get_model().get_iter(reference))

    def on_operations_question(self,store, rows, ui): # Move to 
        packages = []
        for c in rows:
             iterator = store.get_iter(c)
             packages += [store[iterator][0]]
        OperationsUI( mediapackage=packages, UItype=ui )

    def on_play(self, store, reference, iterator):
        """ Retrieve mediapackage and send videos to player"""
        package = store[iterator][0]
	key = store[iterator][0].getIdentifier()
	logger.info("Play: " + str(key))

	if package.status == mediapackage.RECORDED:
	    self.dispatcher.emit("play-list", package, self.reference)
	else:			
	    text = {"title" : "Media Manager",
		    "main" : "This recording can't be played",
		    }
	    buttons = ( gtk.STOCK_OK, gtk.RESPONSE_OK )
	    message.PopUp(message.WARNING, text,  # TODO will fail move to managerui
                          context.get_mainwindow(),
                          buttons)
	return True 
	
    def on_edit(self,store,reference,iterator):
        """Pop ups the Metadata Editor"""
	key = store[iterator][0].getIdentifier()
	self.edit(key)		
	self.refresh_row(reference,iterator)
	
    def on_info(self,store,reference,iterator):
	"""Pops up de MP info dialog"""
	key = store[iterator][0].getIdentifier()
	self.info(key)

    def create_ui(self):
        
        listingbox = gtk.VBox()
        self.box = listingbox
        listalign = gtk.Alignment(0.5, 0.5, 0.88, 0.99) # why not 1
        scrolledw = gtk.ScrolledWindow()
        scrolledw.set_policy(gtk.POLICY_NEVER,gtk.POLICY_ALWAYS)
        scrolledw.set_placement(gtk.CORNER_TOP_LEFT)
        scrolledw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        
        self.vista = gtk.TreeView()
        style=self.vista.rc_get_style().copy()
        color = gtk.gdk.color_parse(str(style.base[gtk.STATE_SELECTED]))
        self.vista.modify_base(gtk.STATE_ACTIVE, color)

        style=self.vista.rc_get_style().copy()
        color = gtk.gdk.color_parse(str(style.base[gtk.STATE_SELECTED]))
        #self.vista.modify_base(gtk.STATE_ACTIVE, color) 

        self.vista.set_show_expanders(False)
        self.vista.set_rubber_banding(True)
        self.vista.set_tooltip_column(1)

        def force_ctrl(iv, ev):
            ev.state = gtk.gdk.CONTROL_MASK
        if context.get_conf().get('mediamanager', 'selection').lower() == 'touch':
            self.vista.connect('key-press-event', force_ctrl)
            self.vista.connect('button-press-event', force_ctrl)

        #self.vista.can_focus(True)
        scrolledw.add(self.vista)
        self.scroll = scrolledw

        # SHORTCUT BUTTONS
        shortcut = gtk.HButtonBox()
        shortcut.set_layout(gtk.BUTTONBOX_START)
        allb = gtk.Button("All")
        noneb = gtk.Button("None")
        allb.set_can_focus(False)
        noneb.set_can_focus(False)
        shortcut.pack_start(allb)
        shortcut.pack_start(noneb)
        allb.connect("clicked", lambda l:self.vista.get_selection().select_all())
        noneb.connect("clicked", lambda l:self.vista.get_selection().unselect_all())
        self.shortcutlist = [allb, noneb]
        control_below=gtk.HBox()
        control_below.pack_start( shortcut, True, True, 0 )

        if self.reference == 1:
            gototrash = gtk.HButtonBox()
            gototrash.set_layout(gtk.BUTTONBOX_END)
            trash_button = gtk.Button("Trash")
            gototrash.pack_start( trash_button )
            trash_button.connect("clicked", self.on_trash)
            trash_button.set_can_focus(False)
            control_below.pack_start( gototrash, True, True, 0 )      
            self.shortcutlist += [trash_button]

        # CONTROL BOX
        controlbox = gtk.VBox()
        buttonbox = gtk.HButtonBox()
        buttonbox.set_layout(gtk.BUTTONBOX_SPREAD)
        buttonbox.set_homogeneous(True)
        newbox = gtk.HBox()
        newbox.pack_start(buttonbox, True, True)
        if self.reference == 1:
            secondarybox = gtk.HButtonBox()
            secondarybox.set_layout(gtk.BUTTONBOX_SPREAD)
            secondarybox.set_homogeneous(True)   
            controlbox.set_homogeneous(False)
            newbox.pack_start(secondarybox, True, True)
            self.secondarybox = secondarybox
        self.buttonbox = buttonbox
        
        self.box.pack_start(listalign, True, True, 0)
        listbox = gtk.VBox()
        listbox.pack_start(scrolledw, True, True, 0)
        listbox.pack_start(control_below, False, False, 0)
        listalign.add(listbox)
        self.box.pack_start(controlbox, False, False, 50) # TODO proportionality
        #controlbox.pack_start(buttonbox,True, True, 10)
        #controlbox.pack_start(secondarybox,True, True, 10)
        controlbox.pack_start(newbox,True, True, 0)
        self.define_buttons()

    def define_buttons(self):
        self.buttonlist = []
        self.add_button(self.buttonbox, "media-playback-start", "Play", "Play") 
        self.add_button(self.buttonbox, gtk.STOCK_COPY, "Edit", "Edit Metadata") 
        self.add_button(self.secondarybox, gtk.STOCK_GO_UP, "New Ops", "New operations") 
        self.add_button(self.secondarybox, gtk.STOCK_CLEAR, "Clear Ops", "Clear nightly operations") 
        self.add_button(self.secondarybox, gtk.STOCK_EXECUTE, "Execute Ops", "Execute nightly operations Now") 
        self.add_button(self.buttonbox, gtk.STOCK_CLOSE, "Delete", "Delete selected recordings") 

    def add_button(self, box, icon, text, tooltip):
        composition = gtk.VBox()
        image = gtk.Image()
        image.set_from_icon_name(icon, gtk.ICON_SIZE_DIALOG)
        
        label = gtk.Label(text)
        composition.pack_start(image)
        composition.pack_start(label)
        button = gtk.Button()
        button.add(composition)
        button.set_tooltip_text(tooltip)
        button.set_can_focus(False)
        button.connect('clicked', self.on_action)
        box.pack_start(button)   


    def do_resize(self, buttonlist, secondlist=[]): 
        """Force a resize on the Media Manager"""
        size = context.get_mainwindow().get_size()
        self.strip.resize()
	altura = size[1]
	anchura = size[0]

	k1 = anchura / 1920.0
	k2 = altura / 1080.0
	self.proportion = k1

        buttonlist = self.buttonlist
	for button in buttonlist:
	    button.set_property("width-request", int(k1*100) )
	    button.set_property("height-request", int(k1*100) )

	    image = button.get_children()
	    if type(image[0]) == gtk.Image:
		image[0].set_pixel_size(int(k1*80))   

	    elif type(image[0]) == gtk.VBox:
		for element in image[0].get_children():
		    if type(element) == gtk.Image:
			element.set_pixel_size(int(k1*46))

	for button in self.shortcutlist:
	    button.set_property("width-request", int(k1*100) )
	    button.set_property("height-request", int(k1*50) )
            fsize = 12*k2
            font = pango.FontDescription(str(fsize))
            label = button.get_children()[0]
	    if type(label) == gtk.Label:
                attr = pango.AttrList()
                attr.insert(pango.AttrFontDesc(font,0,-1))
                label.set_attributes(attr)
   
	for name in secondlist:
	    button2 = self.gui.get_object(name)
	    button2.set_property("width-request", int(k2*85) )
	    button2.set_property("height-request", int(k2*85) )

	    image = button2.get_children()
	    if type(image[0]) == gtk.Image:
		image[0].set_pixel_size(int(k1*56))
                image[0].show()

	    elif type(image[0]) == gtk.VBox:
		for element in image[0].get_children():
		    if type(element) == gtk.Image:
			element.set_pixel_size(int(k1*46))

	return True


    def resize(self):
         """Adapts GUI elements to the screen size"""
         buttonlist = ["playbutton","editbutton","ingestbutton","deletebutton"]
         size = context.get_mainwindow().get_size()
         wprop = size[0]/1920.0
         hprop = size[1]/1080.0
         fsize = 12*hprop
         font = pango.FontDescription(str(fsize))
         #columnae = self.vista.get_columns()
         columnae =self.columns
         for index,column in enumerate(columnae):
             cell = column.get_cells()[0]
             #cell = self.definitions[index]['render']
             cell.set_property('font-desc', font)
             cell.set_property('height', int(hprop*40))
             cell.set_property('width-chars', 
                                int( wprop*self.definitions[index]["wprop"] )
                                )

         for column in self.vista.get_columns():
             first = column.get_widget()
             if not first:
                 label = gtk.Label(" "+column.get_title())
             else:
                 label = column.get_widget()
             attr = pango.AttrList()
             attr.insert(pango.AttrFontDesc(font,0,-1))
             label.set_attributes(attr)
             if not first:
                 label.show()			
                 column.set_widget(label)
             column.queue_resize()

         self.do_resize(buttonlist)
         return True

class ArchiveUI(ListingClassUI):

    def __init__(self):

        ManagerUI.__init__(self, 1, 1, "Trash")
        self.reference = 4
        self.create_ui()
        #self.box

        # Set selection mode
	self.vista.get_selection().set_mode(gtk.SELECTION_MULTIPLE) # could SELECTION_MULTIPLE


	old_style = context.get_conf().get_color_style()
	self.color = context.get_conf().get_palette(old_style)
	
        # connect signals
        #builder.connect_signals(self)
	self.dispatcher.connect("refresh-row", self.refresh_row_from_mp, self.reference)
	self.dispatcher.connect("galicaster-status", self.event_change_mode)
		
        # populate treeview
	self.populate_treeview(self.repository.list_archived().values())
	self.box.pack_start(self.strip,False,False,0)
	self.box.reorder_child(self.strip,0)
	self.box.show()
	self.pack_start(self.box,True,True,0)

    def define_buttons(self):
        self.buttonlist = []
        self.add_button(self.buttonbox, "media-playback-start", "Play", "Play") 
        self.add_button(self.buttonbox, "edit-undo", "Restore", "Restore selected recordings") 
        self.add_button(self.buttonbox, "user-trash", "Empty Trash", "Delete All recording on Trash" )

    def refresh_treeview(self):
	"""Refresh all the values on the list"""
	logger.info("Refreshing TreeView")
	model, selected = self.vista.get_selection().get_selected_rows()
	self.repository.refresh()
	self.insert_data_in_list(self.lista, self.repository.list_archived().values())

	s = 0 if len(selected) == 0 else selected[0][0]
	self.vista.get_selection().select_path(s)

        
gobject.type_register(ListingClassUI)
gobject.type_register(ArchiveUI)
