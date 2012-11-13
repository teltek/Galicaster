# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/ui/managerui
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.
"""
UI for the Media Manager and Player area
"""

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
from galicaster.utils import readable
from galicaster.utils.resize import relabel
from galicaster.classui.strip import StripUI
from galicaster.classui.mpinfo import MPinfo

 
logger = logging.getLogger()

ONE_MB = 1024*1024
dcterms = ["title", "creator", "ispartof", "description", "subject", "language", "identifier", "contributor", "created"]
metadata ={
    "title": "Title:", "creator": "Presenter:", "ispartof": "Course/Series:", 
    "description": "Description:", "subject": "Subject:", 
    "language": "Language:", "identifier": "Identifier:", 
    "contributor": "Contributor:", "created":"Start Time:", 
    "Title:":"title", "Presenter:":"creator", "Course/Series:":"ispartof", 
    "Description:":"description", "Subject:":"subject", 
    "Language:":"language", "Identifier:":"identifier", 
    "Contributor:":"contributor", "Start Time:":"created",
}


class ManagerUI(gtk.Box):
    """
    Create Recording Listing in a VBOX with TreeView from an MP list
    """
    __gtype_name__ = 'Manager'

    def __init__(self, element):
        """elements set the previous area to which the top bar's back button points to"""
        gtk.Box.__init__(self)
        self.strip = StripUI(element)
        

	self.conf = context.get_conf()
	self.dispatcher = context.get_dispatcher() 
	self.repository = context.get_repository()
	self.network = False	    

	self.dispatcher.connect("net-up", self.network_status, True)
	self.dispatcher.connect("net-down", self.network_status, False)


    def sorting(self, treemodel, iter1, iter2, data, regular=True, ascending=1):	 
        """Basic Sort comparisson"""
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
        """Sort algorithm, giving similar value to capital and regular letters"""
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
        """Sorting algorithm, placing empty values always and the end, both descending and ascending"""
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
        

#-------------------------------- DATA PRESENTATION --------------------------------


    def size_readable(self,column,cell,model,iterador,user_data):
        """Generates human readable string for a number.
        Returns: A string form of the number using size abbreviations (KB, MB, etc.) """
        resultado = readable.size(cell.get_property('text'))
        cell.set_property('text',resultado)
        return resultado

    def date_readable(self,column,cell,model,iterador,user_data):
        """ Generates date readable string from an isoformat datetime. """		
        novo=readable.date(cell.get_property('text'))
        cell.set_property('text',novo)		
        return novo

    def time_readable(self,column,cell,model,iterador,user_data):
        """Generates date hout:minute:seconds from seconds."""		
        ms = cell.get_property('text')
        novo = readable.time(int(ms)/1000)
        cell.set_property('text',novo)		
        return novo

    def list_readable(self,listed):
        """Generates a string of items from a list, separated by commas."""		
        novo = readable.list(listed)
        return novo

    def status_readable(self,column,cell,model,iterator,user_data):
        """Set text equivalent for numeric status of mediapackages."""	
        ms = cell.get_property('text')
        novo = mediapackage.mp_status[int(ms)]
        cell.set_property('text',novo)

    def operation_readable(self,column,cell,model,iterator,operation):
        """Sets text equivalent for numeric operation status of mediapackages."""	
        mp=self.repository.get((model[iterator])[0])
        status=mp.getOpStatus(operation)
        out = mediapackage.op_status[status]
        cell.set_property('text', out)
        old_style = context.get_conf().get_color_style()
        if old_style:
            color = model[iterator][8]
        else:
            palette = context.get_conf().get_palette()
            color = palette[status]
        cell.set_property('background', color)
     

    def series_readable(self,column,cell,model,iterator,user_data):
        """Sets text equivalent for numeric status of mediapackages."""	
        ms = cell.get_property('text')
        if ms == None:
            novo=""
        else: 
            novo=self.repository.get((model[iterator])[0]).series_title
        cell.set_property('text',novo)
        return novo

#---------------------------------------- ACTION CALLBACKS ------------------

    def ingest_question(self,package):            
        """Pops up a question dialog for available operations."""
        buttons = None
        disabled = not self.conf.get_boolean("ingest", "active")
        day,night = context.get_worker().get_all_job_types_by_mp(package)
        jobs = day+night
        text = {"title" : "Media Manager",
                "main" : "Which operation do you want to perform?"
                        }
        text['text'] = ''
        icon = message.QUESTION

        if disabled:                                         
            text['text']=text['text']+"The ingest service is disabled."

        if not self.network:                                         
            text['text']=text['text']+"Ingest disabled because of network problems."
            for job in day:
                if job.lower().count("ingest"):
                    jobs.remove(job)            
                    day.remove(job)
            for job in night:
                if job.lower().count("ingest"):
                    pass
                    #jobs.remove(job)            
                    #night.remove(job)

        for job in day:
            op_state = package.operation[job.lower().replace(" ", "")]
            if op_state == mediapackage.OP_DONE:
                text['text']="\n" + text['text'] + job + " already perfomed"
            elif op_state == mediapackage.OP_NIGHTLY:
                text['text']="\n"+ text['text'] + job + " will be performed tonight" 
            

        index = 0
        response_dict = {}
        grouped1 = []
        grouped2 = []
        for job in day:
            index+=1  
            response_dict[index]=job
            grouped1.append(job)
            grouped1.append(index)

        for job in night:
            index+=1
            response_dict[index]=job
            grouped2.append(job)
            grouped2.append(index)

        grouped2.append("Cancel")
        grouped2.append(0) 

        buttons = tuple(grouped1)
        buttons2 = tuple(grouped2)
        if icon == message.QUESTION:
            icon = "INGEST"

        warning = message.PopUp(icon,text,
                                context.get_mainwindow(),
                                buttons2, buttons)

        if warning.response == 0:               
            return True
        elif warning.response == gtk.RESPONSE_OK: # Warning
            return True
        else:
            chosen_job = response_dict[warning.response].lower().replace (" ", "_")
            if chosen_job.count('nightly'):
                context.get_worker().do_job_nightly(chosen_job.replace("_",""), package)
            else:                
                context.get_worker().do_job(chosen_job, package)
            return True


    def play(self,key):
	"""Retrieves mediapackage and send videos to player."""
	logger.info("Play: "+str(key))
	package = self.repository.get(key)

	if package.status == mediapackage.RECORDED:
	    self.dispatcher.emit("play-list", package)
	else:			
	    text = {"title" : "Media Manager",
		    "main" : "This recording can't be played",
		    }
	    buttons = ( gtk.STOCK_OK, gtk.RESPONSE_OK )
	    warning = message.PopUp(message.WARNING, text, 
                                    context.get_mainwindow(),
				    buttons)
	return True


    def change_mode(self,button):
        """Handles a change mode"""
	text=button.get_children()[0].get_text()
        
	if text == "Recorder":
	    self.dispatcher.emit("change-mode", 0)
	else:
	    self.dispatcher.emit("change-mode", 2)


#--------------------------------------- METADATA -----------------------------

    def edit(self,key):
        """Pop ups the Metadata Editor"""
	logger.info("Edit: "+str(key))
	selected_mp = self.repository.get(key)
	meta = Metadata(selected_mp)
	self.repository.update(selected_mp)

    def info(self,key):
        """Pops up de MP info dialog"""
        logger.info("Info: "+str(key))
        dialog = MPinfo(key)

    def do_resize(self, buttonlist, secondlist=[]): 
        """Force a resize on the Media Manager"""
        size = context.get_mainwindow().get_size()
        self.strip.resize()
	altura = size[1]
	anchura = size[0]

	k1 = anchura / 1920.0
	k2 = altura / 1080.0
	self.proportion = k1

	for name  in buttonlist:
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

	for name in secondlist:
	    button = self.gui.get_object(name) 
	    button.set_property("width-request", int(k2*85) )
	    button.set_property("height-request", int(k2*85) )

	    image = button.get_children()
	    if type(image[0]) == gtk.Image:
		image[0].set_pixel_size(int(k1*56))   

	    elif type(image[0]) == gtk.VBox:
		for element in image[0].get_children():
		    if type(element) == gtk.Image:
			element.set_pixel_size(int(k1*46))

	return True

    def delete(self,key):
        """Pops up a dialog. If response is positive, deletes a MP."""
	logger.info("Delete: "+str(key))
	package = self.repository.get(key)
	t1 = "This action will remove the recording from the hard disk."
	t2 = 'Recording:  "'+package.getTitle()+'"'
	text = {"title" : "Delete",
		"main" : "Are you sure you want to delete?",
		"text" : t1+"\n\n"+t2
		    }
	buttons = ( gtk.STOCK_DELETE, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
	warning = message.PopUp(message.WARNING, text,
                                context.get_mainwindow(),
                                buttons)

	if warning.response in message.POSITIVE:                
	    self.repository.delete(package)
	    return True
	else:
	    return False


    def network_status(self, signal, status):
        """Updates the signal status from a received signal"""
        self.network = status
            

gobject.type_register(ManagerUI)

def main(args):
    """Launcher for debugging purposes"""
    v = listing()
    gtk.main()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv)) 
