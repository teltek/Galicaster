# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/classui/operations
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.
"""
UI for the operation manager
"""

import gtk
import pango
from os import path

from elements.__init__ import Chooser
from selector import SelectorUI, MainList
from elements.clock import Clock

from galicaster.operations import ingest, export_to_zip, nas#,side_by_side

class OperationsUI(SelectorUI):
    """
    Main window of the Operations Manager.
    It list the available operations, with tabs associated to configuration and confirmation.
    """
    
    __gtype_name__ = 'OperationsUI'

    equivalence = { # TODO list multiple NAS-Polimedia by configuration
        "Ingest": ingest.Ingest, # TODO configure which operations appears # TODO Name it Ingest to MH
        "Export to Zip": export_to_zip.ExportToZip, # TODO should be Export to Zip
        "Ingest to Nas": nas.IngestNas,
        #"Side by Side": sbs.SideBySide       # TODO make SBS operation the new way
        }

    def __init__(self, parent=None, size = [1920,1080], mediapackage = None):
        SelectorUI.__init__(self, parent, size)


        #configuration data
        self.mediapackage = mediapackage # TODO take into account single or multiple MPs
        self.operation = nas.IngestNas # TODO set a default operation, also orange on interface
        self.common = {} # Priority and Schedule 
        self.specific = {} # Specific parameters

        self.list = OperationList(self, size, "Operation Information")
        self.add_main_tab("Operation Selector", self.list)
        self.show_all()

    # TODO remove data on remove_tab
    # TODO remove data on close_selector

class OperationList(MainList):
    """
    List of available operations with some handy information
    """

    def __init__(self, parent, size, sidelabel): # "Could be common
        MainList.__init__(self, parent, size, sidelabel)
        
        self.add_button("OK",self.select)
        self.add_button("Cancel",self.close, True)
        self.operation =  nas.IngestNas # decide it somehow, first alphabetic
        self.append_list()
        self.append_schedule()
        #self.select_current() # Fix operation to default or first
        #self.append_info(self.view.get_selection())
        self.show_all()
        
    def select(self, button=None):
        model,iterator=self.view.get_selection().get_selected()
        if type(iterator) is gtk.TreeIter: # TODO must be an iterator, otherwise chose first
            value1 =  model.get_value(iterator,0)
            value2 =  model.get_value(iterator,1)
            print value1,value2
            self.operation = self.superior.equivalence[ value2 ] # TODO mediapackage is on the operation
            self.operation = value1
            self.common["schedule"]= "immediate" # TODO fetch get selected
            #next_page = ConfigurationList(self.superior, self.size, value2)
            #self.superior.append_tab(next_page,gtk.Label(value2))
            # Open Next tab with main configuration options
        else:
            pass # TODO get first one, should be chosen always

    def close(self, button=None): #it's commmon
        self.superior.close()

    def refresh(self): #it's common
        self.list.clear()
        self.append_list()
        # MAYBE reappend schedule
        #self.select_current()

    def select_current(self): # It can be made common # TODO move to Chooser
        iterator =self.list.get_iter_first()
        if self.operation == None:            
              self.view.get_selection().select_iter(iterator)    
        else:
            iterator = self.list.iter_next(iterator)
            while iterator != None:
                if self.list[iterator][0] == self.operation: # check operation name on superior.operation.sthg
                    self.view.get_selection().select_iter(iterator)                
                    break
                iterator = self.list.iter_next(iterator)
        return self.list,iterator

    def append_list(self):  
        # TODO the list should be available on operations
        # TODO have a chooser for this list
        # TODO when clicked change self.operation OPTIONAL change info panel
        
        """Lists the available operations"""
        available_list = [ (ingest.Ingest, "Ingest"), # TODO fix append list on the top of the module
                           (export_to_zip.ExportToZip, "Export To Zip"),
                           #(side_by_side.SideBySide, "Side by Side"),
                           (nas.IngestNas, "Ingest to Nas")        
                           ]
        variable = "operation"
        selector = Chooser(variable,
                           variable.capitalize(),
                           "tree",
                           available_list,
                           preselection = "Ingest",
                           fontsize = 15)

        self.pack_start(selector, False, False, 0)
        self.reorder_child(selector,0)
        #selector.resize(1)



    def append_schedule(self): # TODO get size from class
        variable = "scheduling" 
        font = 15
        selector = Chooser(variable,
                         variable.capitalize(),
                         "toogle",
                         # operation.commom[variable]["type"],      
                           ["Immediate", "Nightly"],
                           preselection = "Immediate",
                           fontsize = font)
        # TODO attach clock to scheduled

        self.pack_start(selector, False, False, 0)
        self.reorder_child(selector,1)
        selector.resize(1)
        
        # TODO get chooser and place it sbs

