# -*- codingo:utf-8 -*-
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

import gtk
import gobject

from galicaster.core import context
from galicaster.mediapackage import mediapackage
from galicaster.classui import message
from galicaster.classui.metadata import MetadataClass as Metadata
from galicaster.utils import readable
from galicaster.classui.strip import StripUI
from galicaster.classui.mpinfo import MPinfo
 
logger = context.get_logger()

class ManagerUI(gtk.Box):
    """
    Create Recording Listing in a VBOX with TreeView from an MP list
    """
    __gtype_name__ = 'Manager'

    def __init__(self, element, thepage, title=""):
        """elements set the previous area to which the top bar's back button points to"""
        gtk.Box.__init__(self)
        self.strip = StripUI(element, thepage, text=title )
        
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

    def ingest_question(self): # TODO delete           
        """Pops up a question dialog for available operations."""
        buttons = None
        disabled = not self.conf.get_boolean("ingest", "active")
        day,night = context.get_worker().get_all_job_types()
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
                if job.lower().count("ingest"): # TODO dont remove other ingest operations
                    jobs.remove(job)            
                    day.remove(job)
            for job in night:
                if job.lower().count("ingest"):
                    pass
                    #jobs.remove(job)            
                    #night.remove(job)
                
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
            return False
        elif warning.response == gtk.RESPONSE_OK: # Warning
            return False
        else:
            # TODO do_job for every package
            chosen_job = response_dict[warning.response].lower().replace (" ", "_")
            return chosen_job

    def on_archive(self, store, rows):
        """Remove a mediapackage from the media manager"""

        if not self.conf.get_boolean('basic', 'archive'):
            return self.on_delete(store, rows)

        logger.info("Archive Dialog")

        t1 = "{0} recording{1} {2} going to be deleted.".format(len(rows),
                                                                 "s" if len(rows)>1 else '',
                                                                 "are" if len(rows)>1 else 'is')
        text = {"title" : "Media Manager",
                "main" : "Are you sure you want to delete?",
                "text" : t1
                }

        buttons = ( gtk.STOCK_DELETE, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
        warning = message.PopUp(message.WARNING, text,
                                context.get_mainwindow(),
                                buttons)

        if not warning.response in message.POSITIVE:
            return False

        iterators = []
        for c in rows:
            iterators += [ store.get_iter(c) ]
        for i in iterators:
            key = store[i][0]
            self.deleting(key)
            self.lista.remove(i)

        self.vista.get_selection().select_path(0)
	return True


    def on_delete(self, store, rows):
        """Pops up a dialog. If response is positive, deletes the selection of MP."""

        logger.info("Delete Dialog")
        t1 = "{0} recording{1} {2} going to be deleted.".format(len(rows),
                                                                "s" if len(rows)>1 else '',
                                                                "are" if len(rows)>1 else 'is')
	t2 = "This action will remove the recording{0} from the hard disk.".format( "s" if len(rows)>1 else '')

        text = {"title" : "Media Manager",
                "main" : "Are you sure you want to delete?",
                "text" : t1+"\n\n"+t2
                }

        buttons = ( gtk.STOCK_DELETE, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
        warning = message.PopUp(message.WARNING, text,
                                context.get_mainwindow(),
                                buttons)

        if not warning.response in message.POSITIVE:
            return False

        iterators = []
        for c in rows:
            iterators += [ store.get_iter(c) ]
        for i in iterators:
            key = store[i][0]
            self.hard_deleting(key)
            self.lista.remove(i)

        self.vista.get_selection().select_path(0)
	return True

    def on_trash(self):
        self.dispatcher.emit("change_mode", 4)

    def on_empty(self):
        """Pops up a dialog. If response is positive, deletes all the archive."""

        logger.info("Empty Archive Dialog")
	t1 = "All recordings will be permanently deleted from the hard disk."

        text = {"title" : "Media Manager",
                "main" : "Are you sure you want to empty the archive?",
                "text" : t1
                }

        buttons = ( gtk.STOCK_DELETE, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
        warning = message.PopUp(message.WARNING, text,
                                context.get_mainwindow(),
                                buttons)

        if not warning.response in message.POSITIVE:
            return False

        self.vista.get_selection().select_all()
        store, rows = self.vista.get_selection().get_selected_rows()
        iterators = []
        for c in rows:
            iterators += [ store.get_iter(c) ]
        for i in iterators:
            key = store[i][0]
            self.hard_deleting(key)
            self.lista.remove(i)

        self.vista.get_selection().select_path(0)
	return True


    def on_restore(self, store, rows):
	"""Pops up de MP info dialog"""

        iterators = []
        for c in rows:
            iterators += [store.get_iter(c) ]
        for i in iterators:
            key = store[i][0]
            self.restore(key)
            self.lista.remove(i)

        self.vista.get_selection().select_path(0)
	return True


    def deleting(self, key):
        logger.debug("Deleting {0}".format(key))
        package = self.repository.get(key)
        self.repository.delete(package)    

    def hard_deleting(self, key):
        logger.debug("Hard deleting {0}".format(key))
        package = self.repository.get(key)
        self.repository.hard_delete(package) 

    def restore(self,key):
        """Restore a MP to the Media Manager"""
        logger.debug("Restoring {0}".format(key))
	package = self.repository.get(key)
        self.repository.restore(package)

    def edit(self,key):
        """Pop ups the Metadata Editor"""
        logger.debug("Editting {0}".format(key))
	selected_mp = self.repository.get(key)
	Metadata(selected_mp)
	self.repository.update(selected_mp)

    def info(self,key):
        """Pops up de MP info dialog"""
        logger.debug("Showing Info for {0}".format(key))
        MPinfo(key)

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
	    button.set_property("width-request", int(k1*100) )
	    button.set_property("height-request", int(k1*100) )

	    image = button.get_children()
	    if type(image[0]) == gtk.Image:
		image[0].set_pixel_size(int(k1*80))   

	    elif type(image[0]) == gtk.VBox:
		for element in image[0].get_children():
		    if type(element) == gtk.Image:
			element.set_pixel_size(int(k1*46))

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

    def network_status(self, signal, status):
        """Updates the signal status from a received signal"""
        self.network = status           

gobject.type_register(ManagerUI)


