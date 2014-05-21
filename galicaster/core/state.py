# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/core/state
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


"""
Galicaster state:
 - hostname = galicaster name
 - state.net = True | False
 - state.is_recording = True | False
 - state.mp = Mediapackage if state.is_recording else None
 - state.area = 0 | 1 | 2 | 3 | 4
"""

REC= 0
PLA= 2
MMA= 1
DIS= 3
PIN= 4 

AREA = ["Recorder", "Media Manager", "Player", "Distribution", "Authentification"]

class State(object):
    def __init__(self, hostname="Galicaster"):
        self.hostname = hostname
        self.net = True #TODO update on startup
        self.is_recording = False
        self.is_error = False
        self.status = "Initialization" #Recorder status
        self.mp = None # should be key
        self.area = REC # TODO set to DIS if admin=True
        self.profile = None # profile Object
        
    def start_record(self, mp):
        self.is_recording = True
        self.mp = mp # Should be Key
        
    def change_area(self, area):
        self.area = area

    def get_all(self):
        "Returns all state parameters as a direct"
        
        return { "hostname": self.hostname,
                 "net" : self.net,
                 "is-recording": self.is_recording,
                 "recorder-status" : self. status,
                 "current-profile" : self.profile.name,
                 "active-area" : AREA[self.area],
                 "current-mediapackage" : self.mp}
        
    
    

