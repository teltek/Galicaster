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
from bottle import route, run, response, abort, request, install, HTTPError
from gi.repository import GObject, Gdk, GLib

from galicaster.core import context
from galicaster.mediapackage.serializer import set_manifest
from galicaster.opencast import series
from galicaster.utils import readable
from galicaster.utils import ical
from galicaster.utils.miscellaneous import get_screenshot_as_pixbuffer

"""
Description: Galicaster REST endpoint using bottle micro web-framework.
Status: Experimental
"""

def error_handler(func):
    def wrapper(*args,**kwargs):
        try:
            return func(*args,**kwargs)
        except HTTPError as e:
            raise e
        except Exception as e:
            logger = context.get_logger()
            error_txt = str(e)
            logger.error("Error in function '{}': {}".format(func.__name__, error_txt))

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
        "/enable_input" : "enable inputs",
        "/disable_input" : "disable inputs",
        "/enable_preview" : "enable preview",
        "/disable_preview" : "disable preview",
        "/recording/set_property": "Adds a new property to the current recording",
        "/recording/set_series": "Sets the series for the current recording",
    }
    endpoints.update(text)
    return json.dumps(endpoints)


@route('/state')
def state():
    response.content_type = 'application/json'
    #TODO: Complete!
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
    for key,value in list(repo.items()):
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
    line["duration"] = int(mp.getDuration()/1000)
    line["created"] = mp.getStartDateAsString()
    for key,value in list(mp.metadata_series.items()):
        line["series-"+key] = value
    for key,value in list(line.items()):
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
        Gdk.threads_add_idle(GLib.PRIORITY_HIGH, recorder.stop)
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
    recorder.enable_input(list(preview.values())[0])
    logger.info("Input enabled")

@route('/disable_input', method='POST')
def disable_input():
    logger = context.get_logger()
    recorder = context.get_recorder()
    preview = request.json
    recorder.disable_input(list(preview.values())[0])
    logger.info("Input disabled")

@route('/enable_preview', method='POST')
def enable_preview():
    logger = context.get_logger()
    recorder = context.get_recorder()
    preview = request.json
    recorder.enable_preview(list(preview.values())[0])
    logger.info("Preview enabled")

@route('/disable_preview', method='POST')
def disable_preview():
    logger = context.get_logger()
    recorder = context.get_recorder()
    preview = request.json
    recorder.disable_preview(list(preview.values())[0])
    logger.info("Preview disabled")

@route('/recording/get_property', method='GET')
def get_property():
    logger = context.get_logger()
    recorder = context.get_recorder()
    if not recorder.current_mediapackage:
        error_message = "[{}] No current_mediapackage available. Recording should be started before calling the endpoint.".format(request.fullpath)
        logger.error(error_message)
        abort(400, error_message)

    mp = recorder.current_mediapackage
    try:
        property_name = request.query['name']
    except KeyError as exc:
        error_message = "[{}] The request does not have the required field {}".format(request.fullpath, exc)
        logger.error(error_message)
        abort(400, error_message)

    property = mp.getProperty(property_name)
    logger.info("Called {} api for property {} of mp {}: {}".format(request.fullpath, property_name,  mp.getIdentifier(), property))
    return json.dumps(property)

@route('/recording/set_property', method='POST')
def set_property():
    logger = context.get_logger()
    recorder = context.get_recorder()
    if not recorder.current_mediapackage:
        error_message = "[{}] No current_mediapackage available. Recording should be started before calling the endpoint.".format(request.fullpath)
        logger.error(error_message)
        abort(400, error_message)

    mp = recorder.current_mediapackage
    try:
        property_name = request.forms['name']
    except KeyError as exc:
        error_message = "[{}] The request does not have the required field {}".format(request.fullpath, exc)
        logger.error(error_message)
        abort(400, error_message)

    if mp.getProperty(property_name):
        error_message = "[{}] The mp already has the property {}, we do not overwrite it.".format(request.fullpath, property_name)
        logger.error(error_message)
        abort(400, error_message)

    try:
        property_value = request.forms['value']
    except KeyError as exc:
        error_message = "[{}] The request does not have the required field {}".format(request.fullpath, exc)
        logger.error(error_message)
        abort(400, error_message)

    mp.setProperty(property_name, property_value)
    logger.info("Setting property {} with value {} for the mediapackage {}".format(property_name, property_value, mp.getIdentifier()))

@route('/recording/get_series', method='GET')
def get_series():
    logger = context.get_logger()
    recorder = context.get_recorder()

    if not recorder.current_mediapackage:
        error_message = "[{}] No current_mediapackage available. Recording should be started before calling the endpoint.".format(request.fullpath)
        logger.error(error_message)
        abort(400, error_message)

    mp = recorder.current_mediapackage
    series = mp.getSeries()
    logger.info("Called {} api. Returned series of mp {} as {}".format(request.fullpath, mp.getIdentifier(), series))
    return json.dumps(series);

@route('/recording/set_series', method='POST')
def set_series():
    logger = context.get_logger()
    recorder = context.get_recorder()

    if not recorder.current_mediapackage:
        error_message = "[{}] No current_mediapackage available. Recording should be started before calling the endpoint.".format(request.fullpath)
        logger.error(error_message)
        abort(400, error_message)

    mp = recorder.current_mediapackage
    if mp.getSeriesIdentifier() != None:
        error_message = "[{}] The mp {} already has an Opencast series {} we do not overwrite it.".format(request.fullpath, mp.getIdentifier(), mp.getSeries())
        logger.error(error_message)
        abort(400, error_message)

    try:
        series_id = request.forms['id']
    except KeyError as exc:
        error_message = "[{}] The request does not have the required field {}".format(request.fullpath, exc)
        logger.error(error_message)
        abort(400, error_message)
        return

    series_title = request.forms.get('title', None)
    opencastSeries = series.getSeriesbyId(series_id)
    if opencastSeries != None:
        series_title = opencastSeries['name']
        logger.info("Series with id {} found. Using stored title: {}".format(series_id, series_title))

    mp.setSeries(
        catalog = {
            'identifier': series_id,
            'title': series_title
        }
    )
    logger.info("Set series of mp {} to {}".format(mp.getIdentifier(), mp.getSeries()))
