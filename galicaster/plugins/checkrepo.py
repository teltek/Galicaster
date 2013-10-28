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
import os

from galicaster.core import context
from galicaster.mediapackage import mediapackage

logger = context.get_logger()
worker = context.get_worker()
conf = context.get_conf()

def init():	
    try:
        dispatcher = context.get_dispatcher()
        dispatcher.connect('after-process-ical', check_repository)  
        dispatcher.connect('collect_recordings', merge_recordings)
        dispatcher.connect('recorder-error', restart_galicaster)

    except ValueError:
	    pass

def restart_galicaster(self, origin, error_message):
    if (error_message.startswith("Internal GStreamer error: negotiation problem")):
        logger.info("GStreamer errror: " + error_message)
        logger.info("killing Galicaster")
        os.system("/usr/share/galicaster/contrib/scripts/kill_gc " + error_message)    

def merge_recordings(self, mpUri):
    dest = os.path.join(mpUri,"CHECK_REPO")
    repofile = os.path.join(mpUri,"FILE_LIST")
    if os.path.isfile(dest):
        mp_list = context.get_repository()
        rectemp = mp_list.get_rectemp_path()
        timesfile = open(dest,"r")
        timespan = timesfile.readline()
        times = timespan.split(',')
        start = datetime.datetime.strptime(times[0], "%Y-%m-%d %H:%M:%S")
        end = datetime.datetime.strptime(times[1], "%Y-%m-%d %H:%M:%S")
        timesfile.close()
        repocheck = open(repofile, "a")
        for fname in os.listdir(rectemp):
            filepath = os.path.join(rectemp, fname)
            if os.path.isdir(filepath):
                for item in (os.listdir(filepath)):
                    fileitem = os.path.join(filepath, item)
                    timestamp = os.path.getmtime(fileitem)
                    time = datetime.datetime.utcfromtimestamp(timestamp)
                    if start < time and end > time :
                        repocheck.write(filepath+"\n")
                        break
            if os.path.isfile(filepath):
                filesize=os.path.getsize(filepath)
                logger.info("found file: %s - size: %s", filepath , str(filesize))
                if (filesize):
                    logger.info("removing file: %s - size: %s", filepath , str(filesize))
                    os.remove(filepath)
        repocheck.close()
        
        os.system("/usr/share/galicaster/contrib/scripts/concat_mp " + mpUri + " " + repofile )
        duration = -1
        durpath = os.path.join(mpUri,"DURATION.txt")
        if os.path.isfile(durpath):
            durfile = open(durpath,"r")
            duration = durfile.readline()
            durfile.close()
            os.remove(durpath)
        os.remove(dest)
        os.remove(repofile)
        logger.info("merge packages: " + mpUri)    
        for uid,mp in mp_list.iteritems():
            if (mp.getURI() == mpUri) :
                if (duration == -1) :
                    duration = mp.getDuration()
                for t in mp.getTracks():
                    mp.remove(t);
                filename = 'presentation.mp4'
                dest = os.path.join(mpUri, os.path.basename(filename))
                etype = 'video/' + dest.split('.')[1].lower()
                flavour = 'presentation/source'
                mp.add(dest, mediapackage.TYPE_TRACK, flavour, etype, duration) # FIXME MIMETYPE
                mp.forceDuration(duration)
                mp_list.update(mp)
                logger.info("merging complete for UID:%s - URI: %s",uid, mpUri)
        for fname in os.listdir(rectemp):
            filepath = os.path.join(rectemp, fname)
            if os.path.isfile(filepath):
                filesize=os.path.getsize(filepath)
                logger.info("found file: %s - size: %s", filepath , str(filesize))
                if (filesize):
                    logger.info("removing file: %s - size: %s", filepath , str(filesize))
                    os.remove(filepath)
        
        
def check_repository(self):
    #mp_list is collection of mediapackages ID's
    if context.get_state().is_recording :
        return
    mp_list = context.get_repository()

    for uid,mp in mp_list.iteritems():
        start = mp.getDate()
        end = start + datetime.timedelta(seconds=(mp.getDuration()/1000))
        if mp.status == mediapackage.SCHEDULED and start < datetime.datetime.utcnow() and end > datetime.datetime.utcnow():
            dest = os.path.join(mp.getURI(),"CHECK_REPO")
            if not os.path.isfile(dest):
                repocheck = open(dest, "w")
                repocheck.write(str(start) + "," +  str(end) + ",\n")
                repocheck.close()
            #duration update            
            x = datetime.datetime.utcnow() - start
            x = x.seconds-2            
            mp.setDuration(mp.getDuration() - x*1000)
            #start-datetime update
            mp.setDate(datetime.datetime.utcnow()+datetime.timedelta(seconds=2))
            #repository update
            mp_list.update(mp)

        scheduler = context.get_scheduler()
        try:
                    scheduler.create_new_timer(mp)
        except ValueError:
                    #log or set default value
                    pass
		#logging
        logger.info("Mediapackage with UID:%s have been reprogrammed", uid)
