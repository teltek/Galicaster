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
import threading
import tempfile

from functools import wraps
from flask import Flask
from flask import request, session, Response
from flask import json
from flask import send_file
from flask import jsonify
import gtk

from galicaster.core import context
from galicaster.mediapackage.serializer import set_manifest
from galicaster.utils import readable

"""
Description: Galicaster REST endpoint using flask micro web-framework.
Status: Experimental 
"""

rest = Flask(__name__)
#authDB = FlaskRealmDigestDB('MyAuthRealm')

def init():
	conf = context.get_conf()
	port = conf.get_int('rest', 'port') or 8080
	user = conf.get('rest', 'user')
	pwd = conf.get('rest', 'pwd')
	restp = threading.Thread(target=rest.run,kwargs={'host':'0.0.0.0', 'port':port})
	restp.setDaemon(True)
	restp.start()
	
def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    conf = context.get_conf()
    return username == conf.get('rest', 'user') and password == conf.get('rest', 'pwd')

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@rest.route('/')
@requires_auth
def index():	
    #session['user'] = request.authorization.username
    #response.content_type = 'application/json' 
    #state = context.get_state()
    #text="Galicaster REST endpoint using flask plugin\n\n"
    endpoints = {
            "/state" : "show some state values",
            "/repository" : "list mp keys" ,
            "/repository/<id>" : "get mp manifest (XML)",
            "/metadata/<id>" : "get mp metadata (JSON)",
            "/start" : "starts a manual recording",
            "/stop" :  "stops current recording",
            "/operation/ingest/<id>" : "Ingest MP",
            "/operation/sidebyside/<id>"  : "Export MP to side-by-side",
            "/operation/exporttozip/<id>" : "Export MP to zip",
            "/screen" : "get a screenshoot of the active"
        }    
    return jsonify(**endpoints)


@rest.route('/state')
def state():
    #response.content_type = 'application/json' 
    state = context.get_state()
    return jsonify(state.get_all())

@rest.route('/repository')
def list():
    repo = context.get_repository()
  #  response.content_type = 'application/json'
    keys = []
    for key,value in repo.iteritems():
        keys.append(key)
    return jsonify(keys)

@rest.route('/repository/<id>')
def get(id):
   repo = context.get_repository()
   #response.content_type = 'text/xml'
   mp = repo.get(id)
   return set_manifest(mp)

@rest.route('/metadata/<id>')
@requires_auth
def metadata(id):
    #response.content_type = 'application/json'
    mp = context.get_repository().get(id)
    line = mp.metadata_episode.copy()
    line["duration"] = long(mp.getDuration()/1000)
    line["created"] = mp.getStartDateAsString()
    for key,value in mp.metadata_series.iteritems():
        line["series-"+key] = value
    for key,value in line.iteritems():
        if value in [None,[]]:
            line[key]=''
        jsonify({key:value})
    return jsonify(**line)

@rest.route('/start')
@requires_auth
def start():
    #response.content_type = 'text/xml'
    context.get_dispatcher().emit('start-before', None)
    return "Signal to start recording sent"    

@rest.route('/stop')
@requires_auth
def stop():
    #response.content_type = 'text/html'
    context.get_dispatcher().emit('stop-record', 0)
    return "Signal to stop recording sent"

@rest.route('/operation/<op>/<mpid>', methods=['GET'])
@requires_auth
def operationt(op, mpid):
#    #response.content_type = 'text/html'
    worker = context.get_worker()
    worker.enqueue_job_by_name(op, mpid)
    return "{0} over {1}".format(op,mpid)
 
def get_screenshot():
    """makes screenshot of the current root window, yields gtk.Pixbuf"""
    window = gtk.gdk.get_default_root_window()
    size = window.get_size()         
    pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, size[0], size[1])        
    return pixbuf.get_from_drawable(window, window.get_colormap(), 
                                    0, 0, 0, 0, size[0], size[1])

@rest.route('/screen')
@requires_auth
def screen():
    #response.content_type = 'image/png'
    pb = get_screenshot()    
    ifile = tempfile.NamedTemporaryFile(suffix='.png')
    pb.save(ifile.name, "png")
    return send_file(ifile.name, mimetype='image/png')
 
