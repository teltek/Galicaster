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
from galicaster.core import context

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

        # TODO get directly from mediapackage
        advanced = loader.get_nightly_operations(mediapackage) 

        self.list = OperationList(self, size, "Operation Information", len(advanced))
        self.add_main_tab("Operation Selector", self.list)
        if advanced:
               self.list2 = AdvancedList(self, size, "Advanced Operation Manager")
               self.add_main_tab("Advanced", self.list2)
               self.notebook.prev_page()
        self.show_all()

class OperationList(MainList):
    """
    List of available operations with some handy information
    """

    def __init__(self, parent, size, sidelabel, advanced=False): # "Could be common
        MainList.__init__(self, parent, size, sidelabel, advanced)
        
        self.add_button("Select",self.select)
        if advanced:
            self.add_button("Advanced",self.shift)
        self.add_button("Cancel",self.close, True)
        self.chooser = []
        self.chooser += [self.append_list()]
        self.chooser += [self.append_schedule()]
        self.show_all()
        
    def select(self, button=None):
        parameters = {}
        for element in self.chooser:
            parameters[element.variable] = element.getSelected()
        operation, defaults = parameters.pop('operation')
        group = (operation, defaults, parameters)
        context.get_worker().enqueue_operations(group, self.superior.mediapackage) # TODO send a signal better
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
        variable = "schedule" 
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

    def shift(self, button = None):
        self.superior.notebook.next_page()


class AdvancedList(MainList):
    """
    List of advanced operations like cancel nightly or sync all
    """

    def __init__(self, parent, size, sidelabel): # "Could be common
        MainList.__init__(self, parent, size, sidelabel)
        
        self.add_button("Select",self.select)
        #self.add_button("Cancel",self.close, True)
        self.add_button("Back",self.shift)

        self.chooser = []
        self.chooser += [self.append_ops()]
        self.chooser += [self.append_advanced()]
        self.show_all()

    def select(self, button=None):
        options = {}
        for element in self.chooser:
            options[element.variable] = element.getSelected()
        if options.get("advanced") == "Do All Now":
            # TODO send signal
            context.get_worker().do_now_nightly_operations(options["operation"], self.superior.mediapackage)
        else:
            # TODO send signal
            context.get_worker().cancel_nightly_operations(options["operation"], self.superior.mediapackage)
        
        # TODO change queue and status for every operation

        self.close(True)

    def shift(self, button=None):
        self.superior.notebook.prev_page()

    def append_ops(self):  
        # TODO the list should be available on operations
        """Lists the available operations"""

        available_list = loader.get_nightly_operations(self.superior.mediapackage)
        new_list = [ (x, str(x)) for x in available_list]
        available_list = new_list
        variable = "operation"
        selectorUI = Chooser(variable,
                             "Active Operations",
                             "tree",
                             available_list,
                             preselection = available_list[0],
                             fontsize = 15)

        self.pack_start(selectorUI, False, False, 0)
        self.reorder_child(selectorUI,0)
        # TODO selector resize(size)
        return selectorUI

    def append_advanced(self): # TODO get size from class
        variable = "advanced" 
        font = 15
        selectorUI = Chooser(variable,
                             "Advanced Options",
                             "toogle",
                             # operation.commom[variable]["type"],      
                             ["Cancel All", "Do All Now"],
                             preselection = "Cancel All",
                             fontsize = font)

        self.pack_start(selectorUI, False, False, 0)
        self.reorder_child(selectorUI,1)
        selectorUI.resize(1)
        return selectorUI
