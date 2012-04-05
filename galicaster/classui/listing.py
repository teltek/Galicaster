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


import sys
import os
from os import path

import pygtk
import gtk
import gobject
import datetime
import pango
import logging

from galicaster.core import context
from galicaster.mediapackage import mediapackage
from galicaster.classui import get_ui_path
from galicaster.classui import message
from galicaster.classui.metadata import MetadataClass as Metadata

log = logging.getLogger()


EXP_STRINGS = [ (0, 'B'), (10, 'KB'),(20, 'MB'),(30, 'GB'),(40, 'TB'), (50, 'PB'),]
ONE_MB = 1024*1024
dcterms = ["title", "creator", "ispartof", "description", "subject", "language", "identifier", "contributor", "created"]
metadata ={"title": "Title:", "creator": "Presenter:", "ispartof": "Course/Series:", "description": "Description:", 
           "subject": "Subject:", "language": "Language:", "identifier": "Identifier:", "contributor": "Contributor:", 
           "created":"Start Time:", "Title:":"title", "Presenter:":"creator", "Course/Series:":"ispartof", 
           "Description:":"description", "Subject:":"subject", "Language:":"language", "Identifier:":"identifier", 
           "Contributor:":"contributor", "Start Time:":"created"}


color = {0: "#FFFFFF",
	 1: "#FFFFFF",
	 2: "#FFFFFF",
	 3: "#FFFFFF",	       
	 4: "#FFFFA0",
	 5: "#FFABAB",
	 6: "#C8FFC8", 
	 7: "#C8FFC8",
	 8: "#ABFFAB",
	 9: "#FF9955" }

rcstring = """
style "big-scroll" {
        GtkRange::stepper-size = 20
        GtkRange::slider-width = 25
	}

class "GtkRange" style "big-scroll"

"""


#style "big-scroll" {        
#        GtkRange::stepper-size = 25
#        GtkRange::stepper-spacing = 10
#        GtkRange::arrow-scaling = 0.1
#        GtkRange::slider-width = 50
#        GtkRange::trough-border = 2
#        GtkRange::width-request = 100
#        GtkRange::height-request = 100
#        GtkRange::scroll-arrow-vlength = 50
#	}

#class "GtkRange" style "big-scroll"

gtk.rc_parse_string(rcstring)
#gtk.rc_reset_styles(self.main_window.get_settings())



class ListingClassUI(gtk.Box):
	"""
	Create Recording Listing in a VBOX with TreeView from an MP list
	"""
	__gtype_name__ = 'Listing'


	def __init__(self):
		gtk.Box.__init__(self)

		builder = gtk.Builder()
		builder.add_from_file(get_ui_path('listing.glade'))
		self.gui = builder

		self.box = builder.get_object("listingbox")
		self.vista = builder.get_object("vista")		
		self.scroll = builder.get_object("scrolledw")
		self.vista.get_selection().set_mode(gtk.SELECTION_SINGLE) # could SELECTION_MULTIPLE
		self.conf = context.get_conf()
		self.dispatcher = context.get_dispatcher() 
		self.repository = context.get_repository()
		self.network = False
		self.parse_ingesting()

		builder.connect_signals(self)
		self.dispatcher.connect("galicaster-status", self.event_change_mode)
		self.dispatcher.connect("refresh-row", self.refresh_row_from_mp)
		self.dispatcher.connect("net-up", self.network_status,True)
		self.dispatcher.connect("net-down", self.network_status,False)

		# ENABLE INGEST BUTTON
		#self.gui.get_object("ingestbutton").set_sensitive(True) if self.conf.get("ingest", "active") == "True" else False)
		self.populate_treeview(self.repository.list().values())
		self.box.show()
		self.pack_start(self.box,True,True,0)

	
	def event_change_mode(self, orig, old_state, new_state):
		if new_state == 1:
			self.refresh()



	def insert_data_in_list(self, lista, mps):
		lista.clear()
                for mp in mps:
			duration = mp.getDuration() # TODO parse via function as creators
			if duration in ["", None]: 
				duration = 0

			if mp.status != mediapackage.SCHEDULED:
				lista.append([mp.metadata_episode['identifier'], #FIXME Add property in mp
					      mp.metadata_episode['title'], #FIXME Add property in mp
					      self.list_readable(mp.creators), 
					      str(mp.series), 
					      long(mp.getSize()),
					      int(duration), 
					      mp.getStartDateAsString(), 
					      mp.status,
					      color[mp.status]])	
				    


	def populate_treeview(self, mp):
		# 1/2-2012 edpck@uib.no size: long -> type_int64
		self.lista = gtk.ListStore(str, str, str, str, gobject.TYPE_INT64, int, str, int, str)
		self.insert_data_in_list(self.lista, mp)

		# Edit Cells per column
		# TODO rename and set as dict
		render1 = gtk.CellRendererText() #name
		render6 = gtk.CellRendererText() #presenter
		render7 = gtk.CellRendererText() #series
		render2 = gtk.CellRendererText() #size
		render3 = gtk.CellRendererText() #duration
		render4 = gtk.CellRendererText() #date
		render5 = gtk.CellRendererText() #id
		render8 = gtk.CellRendererText() #status
		#render9 = gtk.CellRendererText() #bg

		window=gtk.gdk.get_default_root_window()
		self.size = [ 1920 , 1080 ]
		wsize = 1920
		try: 
			#wsize =  window.get_screen().get_width()
			self.size = [ window.get_screen().get_width(), window.get_screen().get_height()]
		except:
			log.error("Screen width not catched")
		self.wprop = self.size[0] / 1920.0
		self.hprop = self.size[1] / 1080.0	


		render6.set_property('width-chars',int(self.wprop*38))
		render7.set_property('width-chars',int(self.wprop*24)) # should be a short version of the Series' name

		render2.set_property('width-chars',int(self.wprop*15))
		render2.set_property('xalign',1.0)

		render3.set_property('width-chars',int(self.wprop*14))
		render3.set_property('xalign',0.5)

		render4.set_property('width-chars',int(self.wprop*26))
		render4.set_property('xalign',0.5)
		render8.set_property('width-chars',int(self.wprop*16))
		
		render1.set_property('height', int(self.hprop*40))
	
		fsize = self.hprop*12
		
		for cell in [render1, render2, render3, render4, render5, render6, render7, render8 ]:
			font = pango.FontDescription(str(fsize))
			cell.set_property('font-desc', font)
		
		vbar = self.scroll.get_vscrollbar()
		vbar.set_size_request(int(self.wprop*50),-1)
		vbar.set_update_policy(gtk.UPDATE_DELAYED)
		

		# Create each column

		header= gtk.VBox()
		name = gtk.Label("Name")
		name.set_property("ypad",int(self.hprop*5))
		header.pack_start(name)
		header.show_all()		

		columna5 = gtk.TreeViewColumn("Id",render5,text = 0, background= 8) # column5 wont be append to the treeview
		columna1 = gtk.TreeViewColumn("Name",render1,text = 1, background= 8)
		columna1.set_widget(header)
		columna6 = gtk.TreeViewColumn("Presenter",render6,text = 2, background= 8)
		columna7 = gtk.TreeViewColumn("Series",render7,text = 3, background= 8)
		columna2 = gtk.TreeViewColumn("Size",render2,text = 4, background= 8)
		columna3 = gtk.TreeViewColumn("Duration",render3,text = 5, background= 8)
		columna4 = gtk.TreeViewColumn("Date",render4,text = 6, background= 8)
		columna8 = gtk.TreeViewColumn("Status",render8,text = 7, background= 8)
		#columna9 = gtk.TreeViewColumn("Background",render9, text = 8)

		# Edit columns				
		columna1.set_expand(True)
		columna1.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)

		# Edit content
		columna2.set_cell_data_func(render2,self.size_readable,None)	
		columna3.set_cell_data_func(render3,self.time_readable,None)
		columna4.set_cell_data_func(render4,self.date_readable,None)
		columna8.set_cell_data_func(render8,self.status_readable,None)
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
		self.vista.append_column(columna8) # status
		self.equivalent= {6: 0, 1: 1, 2 : 2, 3 : 3, 4: 4, 5 : 5, 7 : 3} # column versus position

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
		columna8.set_sort_column_id(7) # status <<

		self.lista.set_sort_func(5,self.sorting,5)
		self.lista.set_sort_func(1,self.sorting_text,1)
		self.lista.set_sort_func(2,self.sorting_empty,2)
		self.lista.set_sort_func(3,self.sorting_empty,3)
		self.lista.set_sort_func(7,self.sorting,7)

		self.vista.connect('row-activated',self.on_double_click)
		self.vista.connect('button-release-event',self.menu)

		self.lista.set_sort_column_id(6,gtk.SORT_DESCENDING)
		


	def sorting(self, treemodel, iter1, iter2, data, regular=True, ascending=1):
		
		first =treemodel[iter1][data]
		second = treemodel[iter2][data]

		if  first >  second:
			return 1 * ascending

		elif first == second:
			if regular:
				if self.vista.get_column(self.equivalent[data]).get_sort_order() == gtk.SORT_DESCENDING:
					ascending=-1
				# order by date
				response = self.sorting(treemodel,iter1,iter2,6,False,ascending) 
				return response
			else:
				return 0		       
		else:
			return -1 * ascending

	def sorting_text(self, treemodel, iter1, iter2, data, regular=True, ascending=1):
		# Null sorting
		first = treemodel[iter1][data]
		second = treemodel[iter2][data]
		if first != None:
			first = first.lower()
		if second != None:
			second = second.lower()

		if first in ["",None] and second in ["",None]:
			if self.vista.get_column(self.equivalent[data]).get_sort_order() == gtk.SORT_DESCENDING:
					ascending=-1
			# order by date
			response = self.sorting(treemodel,iter1,iter2,6,False,ascending) 
			return response

		elif  first in ["",None]:
			if self.vista.get_column(self.equivalent[data]).get_sort_order() == gtk.SORT_DESCENDING:	
				return -1  
			else:
				return 1

		elif  second in ["",None]:
			if self.vista.get_column(self.equivalent[data]).get_sort_order() == gtk.SORT_DESCENDING:	
				return 1  
			else:
				return -1

		# Regular sorting
		if first > second:
			return 1 * ascending
		elif first == second:
			if self.vista.get_column(self.equivalent[data]).get_sort_order() == gtk.SORT_DESCENDING:
				ascending=-1
			# order by date
			response = self.sorting(treemodel,iter1,iter2,6,False,ascending) 
			return response 
		else:
			return -1 * ascending

	def sorting_empty(self, treemodel, iter1, iter2, data, regular=True, ascending=1):
		# Null sorting
		first = treemodel[iter1][data]
		second = treemodel[iter2][data]
		if first in ["",None] and second in ["",None]:
			if self.vista.get_column(self.equivalent[data]).get_sort_order() == gtk.SORT_DESCENDING:
					ascending=-1
			# order by date
			response = self.sorting(treemodel,iter1,iter2,6,False,ascending) 
			return response

		elif  first in ["",None]:
			if self.vista.get_column(self.equivalent[data]).get_sort_order() == gtk.SORT_DESCENDING:	
				return -1  
			else:
				return 1

		elif  second in ["",None]:
			if self.vista.get_column(self.equivalent[data]).get_sort_order() == gtk.SORT_DESCENDING:	
				return 1  
			else:
				return -1

		# Regular sorting
		if first > second:
			return 1 * ascending
		elif first == second:
			if self.vista.get_column(self.equivalent[data]).get_sort_order() == gtk.SORT_DESCENDING:
				ascending=-1
			# order by date
			response = self.sorting(treemodel,iter1,iter2,6,False,ascending) 
			return response 
		else:
			return -1 * ascending

	def refresh_treeview(self):
		log.info("Refreshing TreeView")
		model, selected = self.vista.get_selection().get_selected_rows()
		self.repository.refresh()
		self.insert_data_in_list(self.lista, self.repository.list().values())

		#self.vista.grab_focus()
		s = 0 if len(selected) == 0 else selected[0][0]
		self.vista.get_selection().select_path(s)

	def refresh_row_from_mp(self, origin, identifier):
		# Search Iter to the liststor
		i = None
		for row in self.lista:
			if row[0] == identifier:
				i = row.iter

		mp = self.repository.get(identifier)
		self._refresh(mp,i)


	def refresh_row(self,reference,i):# FIXME keep the sort id 
		mpid = self.lista[i][0] # FIXME set the id as the first metadata
		mp = self.repository.get(mpid)
		self._refresh(mp,i)

	def _refresh(self,mp,i):
		self.lista.set(i,0,mp.metadata_episode['identifier'])
		self.lista.set(i,1,mp.metadata_episode['title'])
		self.lista.set(i,2,self.list_readable(mp.creators))
		self.lista.set(i,3,mp.series_title)
		self.lista.set(i,4,long(mp.getSize()))#FIXME dont use the function use the value
		self.lista.set(i,5,int(mp.getDuration()))
		self.lista.set(i,6,mp.getStartDateAsString())
		self.lista.set(i,7,mp.status)
		self.lista.set(i,8,color[mp.status])

	def refresh(self,element=None,package=None):
		# self refresh_row()
		self.refresh_treeview()
		return True
	
		
#-------------------------------- DATA PRESENTATION --------------------------------


	def size_readable(self,column,cell,model,iterador,user_data):
		""" Generates human readable string for a number.
		Returns: A string form of the number using size abbreviations (KB, MB, etc.) """
		num = float(cell.get_property('text'))
		i = 0
		rounded_val = 0
		while i+1 < len(EXP_STRINGS) and num >= (2 ** EXP_STRINGS[i+1][0]):
			i += 1
			rounded_val = round(float(num) / 2 ** EXP_STRINGS[i][0], 2)

		resultado = '%s %s' % (rounded_val, EXP_STRINGS[i][1])
		cell.set_property('text',resultado)
		return resultado

	def date_readable(self,column,cell,model,iterador,user_data):
		""" Generates date readable string from an isoformat datetime. """		
		iso = (cell.get_property('text'))
		date = datetime.datetime.strptime(iso, '%Y-%m-%dT%H:%M:%S')
		novo = date.strftime("%d-%m-%Y %H:%M")
		cell.set_property('text',novo)		
		return novo

	def time_readable(self,column,cell,model,iterador,user_data):
		""" Generates date hout:minute:seconds from seconds """		
		ms = cell.get_property('text')
		iso = int(ms)/1000
		dur = datetime.time(iso/3600,(iso%3600)/60,iso%60)		
		novo = dur.strftime("%H:%M:%S")
		cell.set_property('text',novo)		
		return novo

	def list_readable(self,listed):
		""" Generates a string of items from a list, separated by commass """		
		novo = ""
		if len(listed):
			novo  = ", ".join(listed)
		return novo

	def list_readable2(self,column,cell,model,iterador,user_data):
		""" Generates a string of items from a list, separated by commass """		
		ms = cell.get_property('text')		
		if ms != "[]":
			novo  = ", ".join(list(ms))
		else:
			novo=""
		cell.set_property('text',novo)		
		return novo

	def status_readable(self,column,cell,model,iterator,user_data):
		""" Set text equivalent for numeric status of mediapackages """	
		ms = cell.get_property('text')
		novo = mediapackage.mp_status[int(ms)]
		cell.set_property('text',novo)
		
	def series_readable(self,column,cell,model,iterator,user_data):
		""" Set text equivalent for numeric status of mediapackages """	
		ms = cell.get_property('text')
		if ms == None:
			novo=""
		else: 
			novo=self.repository.get((model[iterator])[0]).series_title
		cell.set_property('text',novo)
		return novo






	#row = model[iterator]
	#	if ms.count("5"):#RED-failed 
	#		row[8]="#FFABAB"
	#	elif ms.count("4"): # YELLOW- recorded
	#		row[8]="#FFFFA0"
	#	elif ms.count("6") or ms.count("7"): # LIGHT GREEN- ingesting or pending
	#		row[8]="#C8FFC8"
	#	elif ms.count("8"):# GREEN - ingested
	#		row[8]="#ABFFAB"
	#	else: # WHITE - not recorded yet
	#		row[8]="#FFFFFF"
	#
		return novo


#---------------------------- MOUSE AND SELECTION MANAGMENT --------------------------------

	def on_action(self, action):
		"""
		When an action its selected calls the function associated 
		"""	
		op=action.get_property("tooltip-text")
		if not isinstance(op,str):
			op=action.get_label()

		log.info("ON_action >> "+op)


		if op == "Delete":
			#self.vista.get_selection().selected_foreach(self.delete)
			model, selected = self.vista.get_selection().get_selected_rows()
			iters = []
			for row in selected:
				iterator=self.lista.get_iter(row)
				iters.append(iterator)
			for i in iters:
				self.delete(self.lista,i)
				#TODO connect "row-deleted" to delete package
		#elif op == "Zip":
		#	self.vista.get_selection().selected_foreach(self.zip)
		elif op == "Ingest":
			self.vista.get_selection().selected_foreach(self.ingest_question)
		elif op == "Play":
			self.vista.get_selection().selected_foreach(self.play)# FIX single operation
		elif op == "Edit":
			self.vista.get_selection().selected_foreach(self.edit)# FIX single operation
		else:
			log.debug('Invalid action')
			   

	def create_menu(self):
		menu = gtk.Menu()
		if self.conf.get("ingest", "active") == "True":
			operations = ["Play", "Edit", "Ingest", "Delete"]
		else:
			operations = ["Play", "Edit", "Delete"]

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
			# print "Showing Operations Menu"
			reference,column,xcell,ycell = widget.get_path_at_pos(int(event.x),int(event.y))
			c = self.lista.get_iter(reference)
			self.vista.get_selection().unselect_all()
			self.vista.get_selection().select_iter(c)	
			menu = self.create_menu()
			# pop up: shell,item,position_func,mousebutton,time,optional_data
			menu.popup(None,None,None,event.button,event.time)
			menu.show()
			return True
		return False


	def on_double_click(self,treeview,reference,column):
		"""
		Set the player for previewing if double click
		"""
		self.play(treeview.get_model(),reference,treeview.get_model().get_iter(reference))


#---------------------------------------- ACTION CALLBACKS -------------------------------------------------#

	def delete(self,store,iterator):
		log.info("Delete: "+store[iterator][0])
		t1 = "This action will remove the recording from the hard disk."
		t2 = 'Recording:  "'+store[iterator][1]+'"'
		text = {"title" : "Delete",
			"main" : "Are you sure you want to delete?",
			"text" : t1+"\n\n"+t2
			}
		buttons = ( gtk.STOCK_DELETE, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
		size = [ self.window.get_screen().get_width(), self.window.get_screen().get_height() ]
		warning = message.PopUp(message.WARNING, text, size, 
					self.get_toplevel(), buttons)
		
		if warning.response in message.POSITIVE:
			package = self.repository.get(store[iterator][0])
			self.repository.delete(package)
			self.lista.remove(iterator)
			self.vista.get_selection().select_path(0)
		return True


	def zip(self,store, zip_path, iterator):# FIXME use Class message.PopUp
		log.info("Zip: "+store[iterator][4])


		builder = gtk.Builder() # create a module for dialogs
		builder.add_from_file(get_ui_path('save.glade'))       
		dialog=builder.get_object("dialog")
		response = dialog.run()
		if response == 1:
			package = self.repository.get(store[iterator][0])
			self.repository.export_to_zip(package,dialog.get_filename())            
		dialog.destroy()
		return True


	def ingest(self,store,reference,iterator):
		log.info("Ingest requested on: " + store[iterator][0])

		if not self.network:
			text = {"title" : "Media Manager",
				"main" : "No connection available with the\nMatterhorn Core available."}
			icon = message.WARNING
			buttons = ( gtk.STOCK_OK, gtk.RESPONSE_OK)
			
			size = [ self.window.get_screen().get_width(), 
				 self.window.get_screen().get_height() ]

			warning = message.PopUp(icon, text, size, 
						self.get_toplevel(), buttons)
		elif self.repository.list_by_status(mediapackage.INGESTING):
			text = {"title" : "Media Manager",
				"main" : "There is another recording being ingested.\nPlease wait until it's finished."}
			icon = message.WARNING
			buttons = ( gtk.STOCK_OK, gtk.RESPONSE_OK)
			
			size = [ self.window.get_screen().get_width(), 
				 self.window.get_screen().get_height() ]

			warning = message.PopUp(icon, text, size, 
						self.get_toplevel(), buttons)
			
			
		else:
			
			package = self.repository.get(store[iterator][0])

			if package.status in [ mediapackage.RECORDED, mediapackage.PENDING, 
					       mediapackage.INGESTED, mediapackage.INGEST_FAILED]:

				context.get_worker().ingest(package)
				self.refresh_row(reference,iterator)

			else:
				log.warning(store[iterator][0]+" cant be ingested")

		return True


	def pending(self,store,reference,iterator):		
		package = self.repository.get(store[iterator][0])
		if package.status in [ mediapackage.RECORDED, mediapackage.INGESTED, mediapackage.INGEST_FAILED ]:
			log.info("Enqueue: " + store[iterator][0])
			package.status = mediapackage.PENDING			
			self.repository.update(package)
			self.refresh_row(reference,iterator)
		elif package.status == mediapackage.PENDING :
			log.info("Cancel ingest: " + store[iterator][0])
			package.status = mediapackage.RECORDED			
			self.repository.update(package)
			self.refresh_row(reference,iterator)
			
		elif package.status != mediapackage.INGESTING:
			log.warning(store[iterator][0]+" cant be enqueued to Ingest")


	def ingest_question(self,store,reference,iterator):
		package = self.repository.get(store[iterator][0])
		buttons = None

		if self.conf.get("ingest", "active") != "True":			
			text = {"title" : "Media Manager",
				"main" : "The ingest service is disabled."}
			icon = message.WARNING
			buttons = ( gtk.STOCK_OK, gtk.RESPONSE_OK)

		elif package.status == mediapackage.PENDING:
			text = {"title" : "Media Manager",
				"main" : "Do you wan to cancel the ingest,\n"+
				"or do you want to ingest it now?"}

			buttons = ( "Cancel Ingest", gtk.RESPONSE_ACCEPT, 
				    "Ingest Now", gtk.RESPONSE_APPLY, 
				    gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT
				    )
			icon = message.QUESTION
			
		elif package.status in [ mediapackage.RECORDED, mediapackage.INGEST_FAILED ]:			
			text = {"title" : "Media Manager",
				"main" : "Do you want to enqueue \n"+
				"this recording for ingesting?"}

			buttons = ( "Ingest", gtk.RESPONSE_ACCEPT, 
				    "Ingest Now", gtk.RESPONSE_APPLY , 
				    gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT
				    )
			icon = message.QUESTION

		elif package.status == mediapackage.INGESTED:
			text = {"title" : "Media Manager",
				"main" : "This recording was already ingested.\n"+
				"Do you want to enqueue it again?"}

			buttons = ( "Ingest", gtk.RESPONSE_ACCEPT, 
				    "Ingest Now", gtk.RESPONSE_APPLY, 
				    gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT
				    )
			icon = message.WARNING

		elif package.status == mediapackage.INGESTING:
			text = {"title" : "Media Manager",
				"main" : "This package is already being ingested."}
			icon = message.WARNING
			buttons = (gtk.STOCK_OK, gtk.RESPONSE_OK)


			
		else: 
			text = {"title" : "Media Manager",
				"main" : "This recording can't be ingested."}
			icon = message.WARNING
			buttons = ( gtk.STOCK_OK, gtk.RESPONSE_OK)

		size = [ self.window.get_screen().get_width(), 
			 self.window.get_screen().get_height() ]

		warning = message.PopUp(icon, text, size, 
					self.get_toplevel(), buttons)

		if warning.response == gtk.RESPONSE_OK: # Warning
			return True
		elif warning.response == gtk.RESPONSE_APPLY: # Force Ingest
			self.ingest(store, reference, iterator)			
		elif warning.response == gtk.RESPONSE_ACCEPT: # Enqueue or cancel enqueue
			self.pending(store, reference, iterator)

		return True

		
	def play(self,store,reference,iterator):
		""" 
		Retrieve mediapackage and send videos to player
		"""
		log.info("Play: "+store[iterator][0])
		key = store[iterator][0]
		package = self.repository.get(key)

		if package.status in [mediapackage.RECORDED, mediapackage.PENDING, 
				      mediapackage.INGESTED, mediapackage.INGESTING,
				      mediapackage.INGEST_FAILED]:
			self.dispatcher.emit("play-list", package)
		else:			
			text = {"title" : "Media Manager",
				"main" : "This recording can't be played",
				}
			buttons = ( gtk.STOCK_OK, gtk.RESPONSE_OK )
			size = [ self.window.get_screen().get_width(), self.window.get_screen().get_height() ]
			warning = message.PopUp(message.WARNING, text, size, 
						self.get_toplevel(), buttons)
		return True


	def change_mode(self,button): # UNUSED
		text=button.get_children()[0].get_text()
		if text == "Recorder":
			self.dispatcher.emit("change-mode", 0)
		else:
			self.dispatcher.emit("change-mode", 2)
	

#--------------------------------------- Edit METADATA -----------------------------
	
	def edit(self,store,reference,iterator):
		ide = store[iterator][0]
		log.info("Edit: "+ide)
		selected_mp = self.repository.get(ide)
		meta = Metadata(selected_mp)
		self.repository.update(selected_mp)
		self.refresh_row(reference,iterator)


	def resize(self,size): 
		altura = size[1]
		anchura = size[0]

		def relabel(label,size,bold):           
			if bold:
				modification = "bold "+str(size)
			else:
				modification = str(size)
			label.modify_font(pango.FontDescription(modification))
        
		k1 = anchura / 1920.0
		k2 = altura / 1080.0
		self.proportion = k1

		for name  in ["playbutton","editbutton","ingestbutton","deletebutton"]:
			button = self.gui.get_object(name) 
			button.set_property("width-request", int(k2*100) )
			button.set_property("height-request", int(k2*100) )
			
			image = button.get_children()
			if type(image[0]) == gtk.Image:
				image[0].set_pixel_size(int(k1*80))   
                     
			elif type(image[0]) == gtk.VBox:
				for element in image[0].get_children():
					if type(element) == gtk.Image:
						element.set_pixel_size(int(k1*46))

		return True

	def parse_ingesting(self):
		"""Check if any recording was ingesting before the previous running"""
		mps = self.repository.list_by_status(mediapackage.INGESTING)
		for mp in mps:
			mp.status = mediapackage.INGEST_FAILED
			self.repository.update(mp)
			log.warn("Mediapackage %s status changed to INGEST FAILED", mp.identifier)

	def network_status(self,signal,status):
		self.network = status


gobject.type_register(ListingClassUI)

def main(args):
    v = listing()
    gtk.main()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv)) 
