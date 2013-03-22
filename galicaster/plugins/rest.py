# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/rest
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import json
import os
import threading
from bottle import route, run, response
import gtk

# pip install bottle

from galicaster.core import context
from galicaster.mediapackage.serializer import set_manifest
from galicaster.utils import readable

"""
Description: Galicaster REST endpoint using bottle micro web-framework.
Status: Experimental 
"""

repo = None

def init():
    global repo
    global dispatcher

    repo = context.get_repository()
    dispatcher = context.get_dispatcher(
)
    restp = threading.Thread(target=run,kwargs={'host':'0.0.0.0', 'port':8080,'quiet':True})
    restp.setDaemon(True)
    restp.start()


@route('/')
def index():
    response.content_type = 'application/json' 
    state = context.get_state()
    text="Galicaster REST endpoint plugin\n\n"
    endpoints = {
            "/state" : "show some state values",
            "/repository" : "list mp keys" ,
            "/repository/:id" : "get mp manifest (XML)",
            "/metadata/:id" : "get mp metadata (JSON)",
            "/start" : "starts a manual recording",
            "/stop" :  "stops current recording",
            "/operation/ingest/:id" : "Ingest MP",
            "/operation/sidebyside/:id"  : "Export MP to side-by-side",
            "/operation/exporttozip/:id" : "Export MP to zip",
            "/screen" : "take screenshot"
        }    
    return json.dumps(endpoints)


@route('/state')
def state():
    response.content_type = 'application/json' 
    state = context.get_state()
    return json.dumps(state.get_all())

@route('/repository')
def list():
    global repo
    response.content_type = 'application/json'
    keys = []
    for key,value in repo.iteritems():
        keys.append(key)
    return json.dumps(keys)

@route('/repository/:id')
def get(id):
    global repo
    response.content_type = 'text/xml'
    mp = repo.get(id)
    return set_manifest(mp)

@route('/metadata/:id')
def metadata(id):
    global repo
    response.content_type = 'application/json'
    mp = repo.get(id)
    line = mp.metadata_episode.copy()
    line["duration"] = long(mp.getDuration()/1000)
    line["created"] = mp.getStartDateAsString()
    for key,value in mp.metadata_series.iteritems():
        line["series-"+key] = value
    for key,value in line.iteritems():
        if value in [None,[]]:
            line[key]=''
        json.dumps({key:value})
    return json.dumps(line)

@route('/start')
def start():
    global repo
    global dispatcher
    response.content_type = 'text/xml'
    dispatcher.emit('start-before', None)
    return "Signal to start recording sent"    

@route('/stop')
def stop():
    global repo
    global dispatcher
    response.content_type = 'text/html'
    dispatcher.emit('stop-record', 0)
    return "Signal to stop recording sent"

@route('/operation/:op/:mpid', method='GET')
def operationt(op, mpid):
    response.content_type = 'text/html'
    worker = context.get_worker()
    worker.enqueue_job_by_name(op, mpid)
    return "{0} over {1}".format(op,mpid)


@route('/screen')
def screen():
    global repo
    global dispatcher
    response.content_type = 'image/png'
    
    pb = context.get_mainwindow().get_screenshot()
    
    path="/tmp/screenshot.png"
    
    pb.save(path, "png")    
    pb= open(path, 'r')
    if (pb != None):
        return pb
    else:
        return "Error"
 
