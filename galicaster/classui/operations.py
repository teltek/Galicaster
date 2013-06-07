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

from galicaster.operations import loader

class OperationsUI(SelectorUI):
    """
    Main window of the Operations Manager.
    It list the available operations, with tabs associated to configuration and confirmation.
    """
    
    __gtype_name__ = 'OperationsUI'

    def __init__(self, parent=None, size = [1920,1080], mediapackage = None):
        SelectorUI.__init__(self, parent, size)

        #configuration data
        self.mediapackage = mediapackage # TODO take into account single or multiple MPs
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
        self.chooser = []
        self.chooser += [self.append_list()]
        self.chooser += [self.append_schedule()]
        self.show_all()
        
    def select(self, button=None):
        options = {}
        for element in self.chooser:
            options[element.variable] =element.getSelected()
        operation = options.pop('operation')
        operation.configure(options = options)        
        loader.enqueue_operations(operation,self.superior.mediapackage) # TODO send a signal better
        self.close(True)

    def close(self, button=None): #it's commmon
        self.superior.close()

    def append_list(self):  
        # TODO the list should be available on operations
        """Lists the available operations"""

        available_list = loader.get_operations()
        variable = "operation"
        selectorUI = Chooser(variable,
                           variable.capitalize(),
                           "tree",
                           available_list,
                           preselection = available_list[0],
                           fontsize = 15)

        self.pack_start(selectorUI, False, False, 0)
        self.reorder_child(selectorUI,0)
        # TODO selector resize(size)
        return selectorUI

    def append_schedule(self): # TODO get size from class
        variable = "scheduling" 
        font = 15
        selectorUI = Chooser(variable,
                         variable.capitalize(),
                         "toogle",
                         # operation.commom[variable]["type"],      
                           ["Immediate", "Nightly"],
                           preselection = "Immediate",
                           fontsize = font)
        # TODO attach clock to scheduled

        self.pack_start(selectorUI, False, False, 0)
        self.reorder_child(selectorUI,1)
        selectorUI.resize(1)
        return selectorUI
        
        # TODO get chooser and place it sbs
