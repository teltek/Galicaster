# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/checkrepo
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""This plugin check repository mediapackages. If anyone it's SCHEDULED when must be RECORDING, change start_time and duration, then start recording
"""

import datetime

from galicaster.core import context
from galicaster.mediapackage import mediapackage

logger = context.get_logger()

def init():	
    dispatcher = context.get_dispatcher()
    dispatcher.connect('ical-processed', check_repository)	

def check_repository(self):
    global logger
    #mp_list is collection of mediapackages ID's
    mp_list = context.get_repository()

    for uid,mp in mp_list.iteritems():
        if mp.status == mediapackage.SCHEDULED and mp.getDate() < datetime.datetime.utcnow() and mp.getDate()+datetime.timedelta(seconds=(mp.getDuration()/1000)) > datetime.datetime.utcnow():
            #duration update			
	    x = datetime.datetime.utcnow() - mp.getDate()
	    x = x.seconds-2			
	    mp.setDuration(mp.getDuration() - x*1000)
	    #start-datetime update
	    mp.setDate(datetime.datetime.utcnow()+datetime.timedelta(seconds=2))
	    #repository update
	    mp_list.update(mp)
            
	    scheduler = context.get_scheduler()
	    try:
                scheduler.create_timer(mp)
                logger.info("Mediapackage with UID:%s have been reprogrammed", uid)
	    except Exception as exc:
                logger.error("Error trying to create a new timer for MP {}: {}".format(uid, exc))
        
