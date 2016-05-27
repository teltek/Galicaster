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

import os
import time
import json
import math
import threading
import tempfile
from bottle import route, run, response, abort, request, install
from gi.repository import Gtk, Gdk, GdkPixbuf

from galicaster.core import context
from galicaster.mediapackage.serializer import set_manifest
from galicaster.utils import readable

"""
Description: Galicaster REST endpoint using bottle micro web-framework.
Status: Experimental
"""

def error_handler(func):
    def wrapper(*args,**kwargs):
        try:
            return func(*args,**kwargs)
        except Exception as e:
            logger = context.get_logger()
            error_txt = str(e)
            logger.error("Error in function '{}': {}".format(func.func_name, error_txt))

            abort(503, error_txt)
    return wrapper


def init():
    conf = context.get_conf()
    host = conf.get('rest', 'host')
    port = conf.get_int('rest', 'port')

    install(error_handler)
    
    restp = threading.Thread(target=run,kwargs={'host': host, 'port': port, 'quiet': True})
    restp.setDaemon(True)
    restp.start()


@route('/')
def index():
    response.content_type = 'application/json'
    text = {"description" : "Galicaster REST endpoint plugin\n\n"}
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
            "/screen" : "get a screenshoot of the active",
            "/logstale" : "check if log is stale (threads crashed)",
            "/quit" : "Quit Galicaster",
        }
    endpoints.update(text)
    return json.dumps(endpoints)


@route('/state')
def state():
    response.content_type = 'application/json' 
    #TODO: Complete!
    return json.dumps({"is-recording": context.get_recorder().is_recording()})

@route('/repository')
def list():
    repo = context.get_repository()
    response.content_type = 'application/json'
    keys = []
    for key,value in repo.iteritems():
        keys.append(key)
    return json.dumps(keys)

@route('/repository/:id')
def get(id):
    repo = context.get_repository()
    response.content_type = 'text/xml'
    mp = repo.get(id)
    return set_manifest(mp)

@route('/metadata/:id')
def metadata(id):
    response.content_type = 'application/json'
    mp = context.get_repository().get(id)
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
    response.content_type = 'text/xml'
    recorder = context.get_recorder()
    if recorder.is_recording():
        abort(500, "couldn't start capture")
    else:
        recorder.record(None)
    return "Signal to start recording sent"
    

@route('/stop')
def stop():
    response.content_type = 'text/html'
    recorder = context.get_recorder()

    if recorder.is_recording():
        recorder.stop()
    else:
        abort(500, "failed to stop the capture, or no current active capture")
        
    return "Signal to stop recording sent"
    

@route('/operation/:op/:mpid', method='GET')
def operationt(op, mpid):
    response.content_type = 'text/html'
    worker = context.get_worker()
    worker.enqueue_job_by_name(op, mpid)
    return "{0} over {1}".format(op,mpid)
 
def get_screenshot():
    """makes screenshot of the current root window, yields Gtk.Pixbuf"""
    window = Gdk.get_default_root_window()
    size = window.get_size()         
    pixbuf = GdkPixbuf.Pixbuf(GdkPixbuf.Colorspace.RGB, False, 8, size[0], size[1])        
    return pixbuf.get_from_drawable(window, window.get_colormap(), 
                                    0, 0, 0, 0, size[0], size[1])
@route('/screen')
def screen():
    response.content_type = 'image/png'
    pb = get_screenshot()    
    ifile = tempfile.NamedTemporaryFile(suffix='.png')
    pb.save(ifile.name, "png")
    pb= open(ifile.name, 'r') 
    if pb:
        return pb
    else:
        return "Error" 

@route('/logstale')
def logstale():
    conf = context.get_conf()
    logger = context.get_logger()
    
    filename = logger.get_path()
    stale = conf.get('logger', 'stale') or 300 # 5 minutes

    info = {}
    
    if not logger:
        abort(503, "The logger service is not available")

    age = int (math.ceil( (time.time() - os.path.getmtime(filename)) ))
    info['filename'] = filename
    info['stale'] = False
    info['age'] = age

    if age > stale:
        info['stale'] = True        

    return json.dumps(info)


@route('/quit', method='POST')
def quit():    
    logger = context.get_logger()
    recorder = context.get_recorder()

    force = request.forms.get('force')
    
    if not recorder.is_recording() or readable.str2bool(force):
        logger.info("Quit Galicaster through API rest")
        # Emit quit signal and exit
        dispatcher = context.get_dispatcher()
        dispatcher.emit('quit')
        
        Gdk.threads_enter()
        Gtk.main_quit()
        Gdk.threads_leave()
    else:
        abort(401, "Sorry, there is a current recording")
