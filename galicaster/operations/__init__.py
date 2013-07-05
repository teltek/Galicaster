# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/operations/__init__
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import uuid
import datetime
from xml.dom import minidom

from galicaster.mediapackage import mediapackage

class Operation(object):
    """
    Base class for operation objects
    """

    # schedule
    IMMEDIATELY = 0
    NIGHTLY = 1
    SCHEDULED = 2
    IMMEDIATE = "immediate"

    def __init__(self, name, subtype, options, context):
        self.__name = name 
        self.name = subtype
        self.context = context
        self.creation_time = None # Initialized on worker.put
        self.start_time = None # stablished on perform
        self.end_time = None # set on failed or succesful end
        self.options = {}
        self.parse_options(options)

    def configure(self, options, is_action):
        self.parse_options(options)
        self.is_action = is_action

    def perform(self, mp):
        if self.is_action:
            self.logStart(mp)
        else:
            pass #log zip operation inside the other action
        success = True
        try:
            self.do_perform(mp)
        except:
            success = False
        if self.is_action:
            self.logEnd(mp, success)
        else:
            pass # log zip inside another action
        
    def setCreationTime(self):
        self.creation_time = datetime.datetime.utcnow().replace(microsecond=0)

    def setStartTime(self):
        self.start_time = datetime.datetime.utcnow().replace(microsecond=0)

    def setEndTime(self):
        self.end_time = datetime.datetime.utcnow().replace(microsecond=0)

    def logCreation(self, mp):
        """Leaves log when operation is created"""
        self.context[0].info("Creating {0} for {1}".format(self.name, mp.getIdentifier() ))
        self.setCreationTime()
        identifier = mp.getIdentifier()
        newMP = self.context[2].get(identifier)
        newMP.setOp(self.name, mediapackage.OP_PENDING, self.creation_time)
        self.context[2].update(newMP)
        self.context[1].emit('refresh-row', mp.getIdentifier())

    def logNightly(self, mp):
        self.context[0].info("Nightly {0} for {1}".format(self.name, mp.getIdentifier() ))
        identifier = mp.getIdentifier()
        newMP = self.context[2].get(identifier)
        newMP.setOp(self.name, mediapackage.OP_NIGHTLY, self.creation_time)
        self.context[2].update(newMP)
        self.context[1].emit('refresh-row', mp.getIdentifier())

    def logCancelNightly(self, mp):
        self.context[0].info("Canceled {0} for {1}".format(self.name, mp.getIdentifier() ))
        identifier = mp.getIdentifier()
        newMP = self.context[2].get(identifier)
        newMP.setOp(self.name,mediapackage.OP_IDLE, 0)
        self.context[2].update(newMP)
        self.context[1].emit('refresh-row', mp.getIdentifier())

    def logStart(self, mp):
        """Leaves log when operation starts"""
        self.setStartTime()
        self.context[0].info("Executing {0} for {1}".format(self.name, mp.getIdentifier() ))
        identifier = mp.getIdentifier()
        newMP = self.context[2].get(identifier)
        newMP.setOp(self.name, mediapackage.OP_PROCESSING, self.start_time)
        self.context[2].update(newMP)
        self.context[1].emit('start-operation', self.name, mp.getIdentifier())
        self.context[1].emit('refresh-row', mp.getIdentifier())

    def logEnd(self, mp, success):
        """Leaves log when opeartaion ends or fails"""
        self.setEndTime()
        if success:
            self.context[0].info("Finalized {0} for {1}".format(self.name, mp.getIdentifier() ))
        else:
            self.context[0].info("Failed {0} for {1}".format(self.name, mp.getIdentifier() ))
        identifier = mp.getIdentifier()
        newMP = self.context[2].get(identifier)
        newMP.setOp(self.name, mediapackage.OP_DONE if success else mediapackage.OP_FAILED, self.end_time)
        self.context[2].update(newMP)
        self.context[1].emit('stop-operation', self.name, newMP, success)
        self.context[1].emit('refresh-row', mp.getIdentifier())

    def serialize_operation(self):
        """Transform metadata into XML and rewrite"""
        # TODO
        # <Operation type=name id=Identifier>status/duration/result>
        # An operation is defined by name, mpid, priority, schedule and options
        # doc = minidom.Document()
        pass

    def parse_options(self, input_options):
        options = self.validate_options(input_options)
        self.options.update(options)
        for key in self.order:
            if not self.options.has_key(key):
                self.options[key]=self.parameters[key]['default']
        self.schedule = self.options["schedule"]

    def validate_options(self, options):
        return options
        

    def select_tracks(self, mp, tracks): 
        # TODO integrate on Operation since is duplicated in ingest
        tracks = []
        all_tracks = mp.getTracks()
        for track in all_tracks:
            if track.getFlavor() in self.options["track-flavors"]:
                tracks += [ track ]
        return tracks

# DESERIALIZATION

def deserialize_xml(self, xml):
    tree = minidom.parse(xml)
    op_list = tree.getElementsByTagName("operation")
    ops = []
    for op in op_list:
        new_op=deserialize_operation(op)
        ops+=[new_op]
    #TODO Log recovered operations somehow
    return ops 

def deserialize_operation(self, string):
    name = string.getAttribute("name")
    op_id = string.getAttribute("identifier")
    creation_time = string.getAttribute("creation")
        
    properties = string.getElementsByTagName("property")
    props = {}
    for prop in properties:
        klass=prop.get_attribute("name")
        value = klass.firstChild.wholeText.strip().strip("\n")
        props[klass]=value

    mp_id = string.getAttribute("mediapackage")
    new=Operation(name,props["mediapackage"],props["priority"],props["schedule"])
    new.start_time = props["start-time"] # integrate on init?
    new.end_time = props["end-time"] # idem
    


    
