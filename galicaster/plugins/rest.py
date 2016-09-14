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
from gi.repository import GObject

from galicaster.core import context
from galicaster.mediapackage.serializer import set_manifest
from galicaster.utils import readable
from galicaster.utils import ical
from galicaster.utils.miscellaneous import get_screenshot_as_pixbuffer
from galicaster.core.core import PAGES

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
    builder = context.get_mainwindow().nbox.get_nth_page(PAGES['REC']).gui
    return json.dumps({"is-recording" : context.get_recorder().is_recording(),
                       "hostname" : context.get_conf().get_hostname(),
                       "net" : context.get_ocservice().net if context.get_ocservice() else None,
                       "recorder-status" : str(context.get_recorder().status),
                       "current-profile" : context.get_conf().get_current_profile().name,
                       "current-mediapackage" : context.get_recorder().current_mediapackage.getIdentifier() if context.get_recorder().current_mediapackage else None
})


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


@route('/screen')
def screen():
    response.content_type = 'image/png'
    pb = get_screenshot_as_pixbuffer()
    ifile = tempfile.NamedTemporaryFile(suffix='.png')
    pb.savev(ifile.name, "png", [], ["100"])
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


@route('/scheduler/calendar', method='POST')
def post_calendar():
    # DEBUG purposes
    # TODO: be able to receive an icalendar using a post field

    conf = context.get_conf()
    if conf.get_boolean('ingest', 'active'):
        abort(503, "The Opencast service is enabled, so ingoring this command to avoid inconsisten behaviour")

    repo = context.get_repository()
    scheduler = context.get_scheduler()
    logger = context.get_logger()

    repo.delete_next_mediapackages()
    ical_data = repo.get_attach('calendar.ical').read()
    ical.handle_ical(ical_data, None, repo, scheduler, logger)

    return "OK"


@route('/quit', method='POST')
def quit():
    logger = context.get_logger()
    recorder = context.get_recorder()
    main_window = context.get_mainwindow()

    force = request.forms.get('force')

    if not recorder.is_recording() or readable.str2bool(force):
        logger.info("Quit Galicaster through API rest")

        GObject.idle_add(main_window.do_quit)
    else:
        abort(401, "Sorry, there is a current recording")

#JSON format: {"input":[]} or {"preview":[]} to enable or disable al bins
# {"input":["Pulse","Webcam"]} to enable or disable specific bins
@route('/enable_input', method='POST')
def enable_input():
    logger = context.get_logger()
    recorder = context.get_recorder()
    preview = request.json
    recorder.enable_input(preview.values()[0])
    logger.info("Input enabled")

@route('/disable_input', method='POST')
def disable_input():
    logger = context.get_logger()
    recorder = context.get_recorder()
    preview = request.json
    recorder.disable_input(preview.values()[0])
    logger.info("Input disabled")

@route('/enable_preview', method='POST')
def enable_preview():
    logger = context.get_logger()
    recorder = context.get_recorder()
    preview = request.json
    recorder.enable_preview(preview.values()[0])
    logger.info("Preview enabled")

@route('/disable_preview', method='POST')
def disable_preview():
    logger = context.get_logger()
    recorder = context.get_recorder()
    preview = request.json
    recorder.disable_preview(preview.values()[0])
    logger.info("Preview disabled")
