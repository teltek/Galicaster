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

from gi.repository import Gtk
from gi.repository import GObject
from galicaster.utils import series

from galicaster.core import context
from galicaster.mediapackage import mediapackage
from galicaster.classui import message
from galicaster.classui.metadata import MetadataClass as Metadata
from galicaster.classui.strip import StripUI
from galicaster.classui.mpinfo import MPinfo

from galicaster.utils.i18n import _

logger = context.get_logger()

OPERATION_NAMES = { 'Export to Zip': _('Export to Zip'),
            'Export to Zip Nightly': _('Export to Zip Nightly'),
            'Cancel Export to Zip Nightly': _('Cancel Zip Nightly'),
            'Ingest': _('Ingest'),
            'Ingest Nightly': _('Ingest Nightly'),
            'Cancel Ingest Nightly': _('Cancel Ingest Nightly:'),
            'Side by Side': _('Side by Side'),
            'Side by Side Nightly': _('Side by Side Nightly'),
            'Cancel Side by Side Nightly': _('Cancel SbS Nightly'),
            'Cancel': _('Cancel'),
             }

class ManagerUI(Gtk.Box):
    """
    Create Recording Listing in a VBOX with TreeView from an MP list
    """
    __gtype_name__ = 'Manager'

    def __init__(self, element):
        """elements set the previous area to which the top bar's back button points to"""
        Gtk.Box.__init__(self)
        self.strip = StripUI(element)

	self.conf = context.get_conf()
	self.dispatcher = context.get_dispatcher()
	self.repository = context.get_repository()
	self.network = False

	self.dispatcher.connect_ui("opencast-connected", self.network_status, True)
	self.dispatcher.connect_ui("opencast-unreachable", self.network_status, False)


    def sorting(self, treemodel, iter1, iter2, data, regular=True, ascending=1):
        """Basic Sort comparisson"""
        first =treemodel[iter1][data]
        second = treemodel[iter2][data]

        if  first >  second:
            return 1 * ascending

        elif first == second:
            if regular:
                if self.vista.get_column(self.equivalent[data]).get_sort_order() == Gtk.SortType.DESCENDING:
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
            if self.vista.get_column(self.equivalent[data]).get_sort_order() == Gtk.SortType.DESCENDING:
                ascending=-1
            # order by date
            response = self.sorting(treemodel,iter1,iter2,6,False,ascending)
            return response

        elif  first in ["",None]:
            if self.vista.get_column(self.equivalent[data]).get_sort_order() == Gtk.SortType.DESCENDING:
                return -1
            else:
                return 1

        elif  second in ["",None]:
            if self.vista.get_column(self.equivalent[data]).get_sort_order() == Gtk.SortType.DESCENDING:
                return 1
            else:
                return -1

	    # Regular sorting
        if first > second:
            return 1 * ascending
        elif first == second:
            if self.vista.get_column(self.equivalent[data]).get_sort_order() == Gtk.SortType.DESCENDING:
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
            if self.vista.get_column(self.equivalent[data]).get_sort_order() == Gtk.SortType.DESCENDING:
                ascending=-1
            # order by date
            response = self.sorting(treemodel,iter1,iter2,6,False,ascending)
            return response

        elif  first in ["",None]:
            if self.vista.get_column(self.equivalent[data]).get_sort_order() == Gtk.SortType.DESCENDING:
                return -1
            else:
                return 1

        elif  second in ["",None]:
            if self.vista.get_column(self.equivalent[data]).get_sort_order() == Gtk.SortType.DESCENDING:
                return 1
            else:
                return -1

	    # Regular sorting
        if first > second:
            return 1 * ascending
        elif first == second:
            if self.vista.get_column(self.equivalent[data]).get_sort_order() == Gtk.SortType.DESCENDING:
                ascending=-1
            # order by date
            response = self.sorting(treemodel,iter1,iter2,6,False,ascending)
            return response
        else:
            return -1 * ascending


#---------------------------------------- ACTION CALLBACKS ------------------

    def ingest_question(self,package):
        """Pops up a question dialog for available operations."""
        disabled = not self.conf.get_boolean("ingest", "active")
        day,night = context.get_worker().get_all_job_types_by_mp(package)
        jobs = day+night
        text = {"title" : _("Media Manager"),
                "main" : _("Which operation do you want to perform?")
               }
        text['text'] = ''

        if disabled or not self.network:
            for job in day:
                if job.lower().count("ingest"):
                    jobs.remove(job)
                    day.remove(job)
            for job in night:
                if job.lower().count("ingest"):
                    pass
                    #jobs.remove(job)
                    #night.remove(job)

        if disabled:
            text['text']=text['text']+_("The ingest service is disabled. ")
        elif not self.network:
            text['text'] = text['text'] + _("Ingest disabled because of network problems. ")

        for job in day:
            op_state = package.operation[job.lower().replace(" ", "")]
            if op_state == mediapackage.OP_DONE:
                text['text']=text['text'] + "\n" + _("{0} already performed").format(OPERATION_NAMES[job])
            elif op_state == mediapackage.OP_NIGHTLY:
                text['text']=text['text'] + "\n" + _("{0} will be performed tonight").format(OPERATION_NAMES[job])


        response_list = ['Ingest', # Resp 1
                         'Ingest Nightly', # Resp 2
                         'Cancel Ingest Nightly', # Resp 3
                         'Export to Zip', # Resp 4
                         'Export to Zip Nightly', # Resp 5
                         'Cancel Export to Zip Nightly', # Resp 6
                         'Side by Side', # Resp 7
                         'Side by Side Nightly', # Resp 8
                         'Cancel Side by Side Nightly'] # Resp 9

        operations = {}
        for job in jobs:
            if job in response_list:
                operations[job] = response_list.index(job)+1


        operations_dialog = message.PopUp(message.OPERATIONS,text,
                                context.get_mainwindow(),
                                operations)

        if operations_dialog.response == Gtk.ResponseType.REJECT or \
            operations_dialog.response == Gtk.ResponseType.DELETE_EVENT or \
            operations_dialog.response == Gtk.ResponseType.OK:
            return True

        elif 0 < operations_dialog.response < len(response_list):
            chosen_job = response_list[operations_dialog.response-1].lower().replace (" ", "_")
            if chosen_job.count('nightly'):
                context.get_worker().do_job_nightly(chosen_job.replace("_",""), package)
            else:
                context.get_worker().do_job(chosen_job, package)
            return True

        else:
            logger.error("Incorrect operation response: {}".format(operations_dialog.response))
            return False



#--------------------------------------- METADATA -----------------------------

    def edit(self,key):
        """Pop ups the Metadata Editor"""
	logger.info("Edit: {0}".format(str(key)))
	selected_mp = self.repository.get(key)
	Metadata(selected_mp, series.get_series())
	self.repository.update(selected_mp)

    def info(self,key):
        """Pops up de MP info dialog"""
        logger.info("Info: {0}".format(str(key)))
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

	for name in buttonlist:
	    button = self.gui.get_object(name)
	    button.set_property("width-request", int(k1*100) )
	    button.set_property("height-request", int(k1*100) )

	    image = button.get_children()
	    if type(image[0]) == Gtk.Image:
		image[0].set_pixel_size(int(k1*80))

	    elif type(image[0]) == Gtk.VBox:
		for element in image[0].get_children():
		    if type(element) == Gtk.Image:
			element.set_pixel_size(int(k1*46))

	for name in secondlist:
	    button2 = self.gui.get_object(name)
	    button2.set_property("width-request", int(k2*85) )
	    button2.set_property("height-request", int(k2*85) )

	    image = button2.get_children()[0].get_children()
	    if type(image[0]) == Gtk.Image:
		image[0].set_pixel_size(int(k1*56))
                image[0].show()

	    elif type(image[0]) == Gtk.VBox:
		for element in image[0].get_children():
		    if type(element) == Gtk.Image:
			element.set_pixel_size(int(k1*46))

	return True

    def delete(self,key, response=None):
        """Pops up a dialog. If response is positive, deletes a MP."""
        self.selected = key
	package = self.repository.get(key)
	logger.info("Delete: {0}".format(str(key)))
	t1 = _("This action will remove the recording from the hard disk.")
	t2 = _('Recording: "{0}"').format(package.getTitle())
	text = {"title" : _("Media Manager"),
		"main" : _("Are you sure you want to delete?"),
		"text" : t1+"\n\n"+t2
		    }
	buttons = ( Gtk.STOCK_DELETE, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT)
	message.PopUp(message.WARN_DELETE, text,
                      context.get_mainwindow(),
                      buttons, response)



    def network_status(self, signal, status):
        """Updates the signal status from a received signal"""
        self.network = status

GObject.type_register(ManagerUI)
