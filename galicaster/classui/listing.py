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
        ManagerUI.__init__(self, 3)
        self.reference = 1

	builder = gtk.Builder()
	builder.add_from_file(get_ui_path('listing.glade'))
	self.gui = builder

	self.box = builder.get_object("listingbox")
	self.vista = builder.get_object("vista")		
	self.scroll = builder.get_object("scrolledw")
	self.vista.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        def force_ctrl(iv, ev):
            ev.state = gtk.gdk.CONTROL_MASK

        self.vista.connect('key-press-event', force_ctrl)
        self.vista.connect('button-press-event', force_ctrl)

	old_style = context.get_conf().get_color_style()
	self.color = context.get_conf().get_palette(old_style)
	
	builder.connect_signals(self)
	self.dispatcher.connect("refresh-row", self.refresh_row_from_mp, self.reference)
	self.dispatcher.connect("start-operation", self.refresh_operation)
	self.dispatcher.connect("stop-operation", self.refresh_operation)
	self.dispatcher.connect("galicaster-status", self.event_change_mode)
		
	self.populate_treeview(self.repository.list().values())
	self.box.pack_start(self.strip,False,False,0)
	self.box.reorder_child(self.strip,0)
	self.box.show()
	self.pack_start(self.box,True,True,0)
		
	
    def event_change_mode(self, orig, old_state, new_state):
        if new_state == self.reference :
            self.refresh()
			
    def insert_data_in_list(self, lista, mps):
        """Appends the mediapackage data into the list"""
	lista.clear()
	for mp in mps:
            duration = mp.getDuration()
	    if duration in ["", None]: 
                duration = 0

	    if mp.status != mediapackage.SCHEDULED:
                lista.append([mp.getIdentifier(), 
			      mp.getTitle(), 
			      mp.getCreator(), 
			      mp.series_title , 
			      long(mp.getSize()),
			      int(duration), 
			      mp.getStartDateAsString(), 
			      mp.status,
			      self.color[mp.getOpStatus("ingest")],
			      mp.getOpStatus("ingest"),
			      mp.getOpStatus("exporttozip"),
			      mp.getOpStatus("sidebyside"),])				    


    def populate_treeview(self, mp):
	"""Establishes which values to be shown, its properties"""
	self.lista = gtk.ListStore(str,str, str, str, long, int, str, int, str, int, int, int)
	# gobject.TYPE_PYOBJECT
	self.insert_data_in_list(self.lista, mp)

	# Edit Cells per column
	render1 = gtk.CellRendererText() #name
	render6 = gtk.CellRendererText() #presenter
	render7 = gtk.CellRendererText() #series
	render2 = gtk.CellRendererText() #size
	render3 = gtk.CellRendererText() #duration
	render4 = gtk.CellRendererText() #date
	render5 = gtk.CellRendererText() #id
	render8 = gtk.CellRendererText() #status
	render9 = gtk.CellRendererText() #operation
	#render9 = gtk.CellRendererText() #bg
	self.renders= [render1, render2, render3, render4, render5, render6, render7, render8, render9]
	self.renders[1].set_property('xalign',1.0)
	self.renders[2].set_property('xalign',0.5)
	self.renders[3].set_property('xalign',0.5)
	self.renders[8].set_property('xalign',0.5)
	
	
	vbar = self.scroll.get_vscrollbar()
	vbar.set_update_policy(gtk.UPDATE_DELAYED)
		
	# Create each column
	#columna5 = gtk.TreeViewColumn("Id",render5,text = 0, background= 8) 
	# column5 wont be append to the treeview
	columna1 = gtk.TreeViewColumn("Name",render1,text = 1, background= 8)
	columna6 = gtk.TreeViewColumn("Presenter", render6, text = 2, background= 8)
	columna7 = gtk.TreeViewColumn("Series", render7, text = 3, background= 8)
	columna2 = gtk.TreeViewColumn("Size", render2, text = 4, background= 8)
	columna3 = gtk.TreeViewColumn("Duration", render3, text = 5, background= 8)
	columna4 = gtk.TreeViewColumn("Date", render4, text = 6, background= 8)
	
	#columna8 = gtk.TreeViewColumn("Status", render8, text = 7, background= 8)
	columna9 = gtk.TreeViewColumn("Ingest", render9)
	columna10 = gtk.TreeViewColumn("Zip", render9)
	columna11 = gtk.TreeViewColumn("SbS", render9)		
	
	#columna8 = gtk.TreeViewColumn("Status", render8, text = 7, background= 8)
	#columna9 = gtk.TreeViewColumn("Operations", render9, text = 9, background= 8)
	#columna9 = gtk.TreeViewColumn("Background",render9, text = 8)

	# Edit columns				
	columna1.set_expand(True)

	# Edit content
	columna2.set_cell_data_func(render2,self.size_readable,None)	
	columna3.set_cell_data_func(render3,self.time_readable,None)
	columna4.set_cell_data_func(render4,self.date_readable,None)
	#columna8.set_cell_data_func(render8,self.status_readable,None)
	columna9.set_cell_data_func(render9,self.operation_readable,"ingest")
	columna10.set_cell_data_func(render9,self.operation_readable,"exporttozip")
	columna11.set_cell_data_func(render9,self.operation_readable,"sidebyside")
	#columna7.set_cell_data_func(render7,self.series_readable,None)
	# Columns 6 and 7 are not edited

	# Set Treeview Model
	self.vista.set_model(self.lista)

	# Append Columns
	self.vista.append_column(columna4) # date
	self.vista.append_column(columna1) # name	
	self.vista.append_column(columna6) # presenter
	self.vista.append_column(columna7) # series
	self.vista.append_column(columna2) # size
	self.vista.append_column(columna3) # duration
	#self.vista.append_column(columna8) # operation former status
	self.vista.append_column(columna9) # operation former status
	self.vista.append_column(columna10) # operation
	self.vista.append_column(columna11) # operation
		

	#self.resize()
	self.equivalent= {6: 0, 1: 1, 2 : 2, 3 : 3, 4: 4, 5 : 5, 7: 3, 9:6, 10:7, 11:8}  # 9
	# data position versus column position

	# Show TreeView
	self.vista.show()

	# Make Headers clickable
	self.vista.set_headers_clickable(True)

	# Make colums sortable
	columna1.set_sort_column_id(1) # name <<
	columna2.set_sort_column_id(4) # size
	columna3.set_sort_column_id(5) # duration
	columna4.set_sort_column_id(6) # date
	columna6.set_sort_column_id(2) # presenter <<
	columna7.set_sort_column_id(3) # series <<
	#columna8.set_sort_column_id(7) # operation form status <<		
	columna9.set_sort_column_id(9) # operation <<
	columna10.set_sort_column_id(10) # operation <<
	columna11.set_sort_column_id(11) # operation <<
	
	self.lista.set_sort_func(5,self.sorting,5)
	self.lista.set_sort_func(1,self.sorting_text,1)
	self.lista.set_sort_func(2,self.sorting_empty,2)
	self.lista.set_sort_func(3,self.sorting_empty,3)
	#self.lista.set_sort_func(7,self.sorting,7)
	#self.lista.set_sort_func(10,self.sorting,10)
	#self.lista.set_sort_func(11,self.sorting,11)
	#self.lista.set_sort_func(12,self.sorting,12)

	self.vista.connect('row-activated',self.on_double_click)
	self.vista.connect('button-release-event',self.menu)

	self.lista.set_sort_column_id(6,gtk.SORT_DESCENDING)

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
	# Search Iter to the liststor
        if self.reference != reference:
            return True
        
	i = None
	for row in self.lista:
	    if row[0] == identifier:
                i = row.iter

        mp = self.repository.get(identifier)
        if i:
            self._refresh(mp,i)

    def refresh_operation(self, origin, operation, package, success = None):
        """Refresh the status of an operation in a given row"""
	identifier = package.identifier
	self.refresh_row_from_mp(origin,identifier, self.reference)

    def refresh_row(self,reference,i):# FIXME keep the sort id 
        mpid = self.lista[i][0] # FIXME set the id as the first metadata
	mp = self.repository.get(mpid)
	self._refresh(mp,i)

    def _refresh(self,mp,i):
        """Fills the new values of a refreshed row"""
	self.lista.set(i,0,mp.getIdentifier())
	self.lista.set(i,1,mp.getTitle())
	self.lista.set(i,2,mp.getCreator())
	self.lista.set(i,3,mp.series_title)
	self.lista.set(i,4,long(mp.getSize()))
	self.lista.set(i,5,int(mp.getDuration()))
	self.lista.set(i,6,mp.getStartDateAsString())
	self.lista.set(i,7,mp.status)
	self.lista.set(i,8,self.color[mp.getOpStatus("ingest")])
	self.lista.set(i,9,mp.getOpStatus("ingest"))
	self.lista.set(i,10,mp.getOpStatus("exporttozip"))
	self.lista.set(i,11,mp.getOpStatus("sidebyside"))
	
    def refresh(self,element=None,package=None):
        # self refresh_row()
        self.refresh_treeview()
	return True
	
#---------------------------- MOUSE AND SELECTION MANAGMENT --------------------


    def on_action(self, action):
        """When an action its selected calls the function associated"""	
	op=action.get_property("tooltip-text")
	if not isinstance(op,str):
            op=action.get_label()

	logger.info("ON_action >> "+op)

        selection = self.vista.get_selection()
        store,rows = selection.get_selected_rows()

        #print self.get_attribute("on_{0}".format(op.lower()))

        if op == "Play": # TODO get attribute on_attribute(so
            last = store.get_iter(rows[len(rows)-1])
            self.on_play(store, None, last)
	elif op == "Edit":
            last = store.get_iter(rows[len(rows)-1])
            self.on_edit(store, None, last)
        elif op == "Delete":
            if self.reference == 1:
                self.on_archive(store, rows)
            elif self.reference == 4:
                self.on_delete(store, rows)
        elif op == "Restore":
            self.on_restore(store, rows)
        elif op == "Empty":
            self.on_empty()
	elif op == "Info":
            last = store.get_iter(rows[len(rows)-1])
            self.on_info(store, None, last)
	elif op == "Operations" or op == "Ingest":
            #self.on_ingest_question(store, rows)
            self.on_operations_question(store, rows)
	else:
            logger.debug('Invalid action: {0}'.format(op))


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

    def on_operations_question(self,store, rows):
        packages = []
        for c in rows:
             iterator = store.get_iter(c)
             packages += [self.repository.get(store[iterator][0])]
        OperationsUI(mediapackage = packages)       

    def on_ingest_question(self,store, rows):
        """Launchs ingest dialog and refresh row afterwards."""

	operation = self.ingest_question() # TODO ingest question for any package
        
        if not operation:
            return True
        iterators = []
        for c in rows:
            iterators += [ store.get_iter(c) ]
        for i in iterators:
            package = self.repository.get(store[i][0])
            if operation.count('nightly'):
                context.get_worker().do_job_nightly(operation.replace("_",""), package)
            else:                
                context.get_worker().do_job(operation, package)
        self.vista.get_selection().select_path(0)
	return True

        
	package = self.repository.get(store[iterator][0])
	self.ingest_question(package)
	self.refresh_row(reference,iterator)
	return True


    def on_play(self, store, reference, iterator):
        """ Retrieve mediapackage and send videos to player"""
	key = store[iterator][0]
	logger.info("Play: " + str(key))
	package = self.repository.get(key)

	if package.status == mediapackage.RECORDED:
	    self.dispatcher.emit("play-list", package, self.reference)
	else:			
	    text = {"title" : "Media Manager",
		    "main" : "This recording can't be played",
		    }
	    buttons = ( gtk.STOCK_OK, gtk.RESPONSE_OK )
	    message.PopUp(message.WARNING, text, 
                          context.get_mainwindow(),
                          buttons)
	return True	

	
    def on_edit(self,store,reference,iterator):
        """Pop ups the Metadata Editor"""
	key = store[iterator][0]
	self.edit(key)		
	self.refresh_row(reference,iterator)
	
    def on_info(self,store,reference,iterator):
	"""Pops up de MP info dialog"""
	key = store[iterator][0]
	self.info(key)
	
    def resize(self):
        """Adapts GUI elements to the screen size"""
	buttonlist = ["playbutton","editbutton","ingestbutton","deletebutton"]
	size = context.get_mainwindow().get_size()
	wprop = size[0]/1920.0
	hprop = size[1]/1080.0
	
	vbar = self.scroll.get_vscrollbar()
	vbar.set_size_request(int(wprop*6),-1)

	self.renders[0].set_property('height', int(hprop*40))
	self.renders[0].set_property('width-chars',int(wprop*56))#name
	self.renders[1].set_property('width-chars',int(wprop*14))#size
	self.renders[2].set_property('width-chars',int(wprop*10))#duration
	self.renders[3].set_property('width-chars',int(wprop*23))#date
	self.renders[5].set_property('width-chars',int(wprop*27))#presenter
	self.renders[6].set_property('width-chars',int(wprop*33.5))#series
	#self.renders[7].set_property('width-chars',int(wprop*12.5))#statusess
	self.renders[8].set_property('width-chars',int(wprop*14))#operations less

	fsize = 12*hprop
	for cell in self.renders:
            font = pango.FontDescription(str(fsize))
	    cell.set_property('font-desc', font)

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

        ManagerUI.__init__(self, 3)
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
        #self.vista.modify_base(gtk.STATE_ACTIVE, color) 

        self.vista.set_show_expanders(False)
        self.vista.set_rubber_banding(True)
        self.vista.set_tooltip_column(1)

        def force_ctrl(iv, ev):
            ev.state = gtk.gdk.CONTROL_MASK

        self.vista.connect('key-press-event', force_ctrl)
        self.vista.connect('button-press-event', force_ctrl)

        #self.vista.can_focus(True)
        scrolledw.add(self.vista)
        self.scroll = scrolledw
        controlbox = gtk.VBox()
        buttonbox = gtk.HButtonBox()
        buttonbox.set_layout(gtk.BUTTONBOX_SPREAD)
        buttonbox.set_homogeneous(True)        
        
        self.box.pack_start(listalign, True, True, 0)
        listalign.add(scrolledw)
        self.box.pack_start(controlbox, False, False, 50) # TODO padding on resize
        controlbox.pack_start(buttonbox,True, True, 10) # IDEM
        self.buttonlist = []
        self.add_button(buttonbox, gtk.STOCK_MEDIA_PLAY, "Play") 
        self.add_button(buttonbox, gtk.STOCK_UNDO, "Restore") 
        self.add_button(buttonbox, gtk.STOCK_CLOSE, "Delete") 
        self.add_button(buttonbox, "user-trash", "Empty") 

    def add_button(self, box, icon, text):
        composition = gtk.VBox()
        image = gtk.Image()
        if not icon.count('user'):
            image.set_from_stock(icon, gtk.ICON_SIZE_DIALOG)
        else:
            image.set_from_icon_name(icon, gtk.ICON_SIZE_DIALOG)
        
        label = gtk.Label(text)
        composition.pack_start(image)
        composition.pack_start(label)
        button = gtk.Button()
        button.add(composition)
        button.set_tooltip_text(text)
        button.connect('clicked', self.on_action)
        self.buttonlist += [button]
        box.pack_start(button)   

    def refresh_treeview(self):
	"""Refresh all the values on the list"""
	logger.info("Refreshing TreeView")
	model, selected = self.vista.get_selection().get_selected_rows()
	self.repository.refresh()
	self.insert_data_in_list(self.lista, self.repository.list_archived().values())

	s = 0 if len(selected) == 0 else selected[0][0]
	self.vista.get_selection().select_path(s)

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
	return True

        
gobject.type_register(ListingClassUI)
gobject.type_register(ArchiveUI)	
