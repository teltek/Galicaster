# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/operations/export_to_zip
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
Export to Zip Operation module
"""
import os
import datetime

from galicaster.core import context
from galicaster.mediapackage import serializer, mediapackage
from __init__ import Operation

class ExportToZip(Operation):

    order = ["location", "use-namespace", "ziptype", "tracks","flavors"]
    show = ["location", "use-namespace", "tracks" ]
    parameters = {
         "location": {
            "type": "file",
            "default": "${title}.zip", # TODO use format
            "description": "Zip filename where to save the mediapackage",
            },
         "destination": {
            "type": "foldere",
            "default": "/home/",#TODO get export folder
            "description": "Location where to save the zip file",
            },
         "use-namespace": {
            "type": "boolean",
            "default": True,
            "description": "Wheter XML namespace is included on metadata files",
            },
         "ziptype": {
            "type": "select",
            "default": "native",
            "description": "Wheter XML namespace is included on metadata files",
            "options": ["native","system"],
            },
         # TODO native or system zip
        "tracks": {
            "type": "list",
            "default": None,
            "description": "Tracks to be processed",
            },
         "flavors": {
            "type": "list",
            "default": None, # None, "all", 
            "description": "Tracks to be processed, selected by flavor, meant to select tracks before its creation",
            },
         }
         
    def __init__(self, mp=None, priority=Operation.NORMAL,schedule=Operation.IMMEDIATELY):
        Operation.__init__(self, "exporttozip", mp, priority, schedule)
        #TODO GUI-List External Writable Media - Flash Memory and External HD

    def configure(self, options={}, is_action=True):

        self.parse_options(options) #TODO integrate on Operation
        self.is_action = is_action  #idem

        self.name = datetime.datetime.now().replace(microsecond=0).isoformat()
        self.location = self.options["location"] or os.path.join(os.path.expanduser('~'), name + '.zip')
        self.schedule = self.options["schedule"]
        
        # include all tracks and flavors for now
        #self.tracks=self.select_tracks(self.mp, self.parameters['track-flavors']['default'])
        #self.ziptype = self.options["ziptype"]
        

    def perform(self, mp): # TODO log creation
        if self.is_action:
            self.logStart(mp)
        else:
            pass #log zip operation inside the other action
        success = True
        try: 
            serializer.save_in_zip(mp, self.location, self.options["use-namespace"], context.get_logger())
            # TODO choose native or system
        except:
            success = False
        if self.is_action:
            self.logEnd(mp, success)
        else:
            pass # log zip inside another action
