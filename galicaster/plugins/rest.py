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
from bottle import route, run, response

from galicaster.core import context
from galicaster.mediapackage.serializer import set_manifest

"""
Description: Galicaster REST endpoint using bottle micro web-framework.
Status: Experimental 
"""

repo = None


def init():
    global repo
    repo = context.get_repository()
    restp = threading.Thread(target=run, kwargs={'host':'0.0.0.0', 'port':8080})
    restp.setDaemon(True)
    restp.start()


@route('/')
def index():
    return "Galicaster REST endpoint plugin"


@route('/list')
def list():
    global repo
    response.content_type = 'application/json'
    keys = []
    for key,value in repo.iteritems():
        keys.append(key)
        
    return json.dumps(keys)
    

@route('/get/:id')
def get(id):
    global repo
    response.content_type = 'text/xml'
    mp = repo.get(id)
    return set_manifest(mp)        
