# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/gcfm
#
# Copyright (c) 2016, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

from StringIO import StringIO

from galicaster.core import context

from galicaster.utils.miscellaneous import get_screenshot_as_pixbuffer
from galicaster.utils import readable
from galicaster.utils import systemcalls

import requests
import json
import os
import subprocess

retry = False

def init():
    global repo, logger, dispatcher, conf
    dispatcher = context.get_dispatcher()
    logger = context.get_logger()
    repo = context.get_repository()
    conf = context.get_conf()
    try:
        uuids =json.load(repo.get_attach("uuid1.json"))
    except Exception as exc:
        logger.warning("{}".format(exc))
        uuids = {}

    handshake(uuids)
    dispatcher.connect('timer-short', push_pic,uuids)
    dispatcher.connect('timer-short', push_status,uuids)
    dispatcher.connect('quit',close_vnc)

def handshake(uuids, force=False):
    global repo, logger,conf
    url_gcfm = conf.get_url('gcfm','url_gcfm')
    if not 'current' in uuids:
        r = requests.get(url_gcfm+'/gcfm_uuid')
        gcfm_uuid = r.json()
        if ('uuids' in uuids) and  (gcfm_uuid['gcfm_uuid'] in uuids['uuids']) and not force:
            uuids['current'] = uuids['uuids'][gcfm_uuid['gcfm_uuid']]
            repo.save_attach('uuid1.json',json.dumps(uuids))
            logger.debug("GCFM_UUID in system, current UUID: "+uuids['current'])
    
        else:
            r = requests.get('http://localhost:5001/uuid_community')
            uuid = r.json()
            if not 'uuids' in uuids:
                uuids['uuids']=''
            data = {gcfm_uuid['gcfm_uuid'] : uuid['uuid']}
            uuids['uuids'] = data
            uuids['current'] = uuid['uuid']
            repo.save_attach('uuid1.json',json.dumps(uuids))
            logger.debug("New UUDI: {} from GCFM_UDDI: {}".format(uuid['uuid'],gcfm_uuid['gcfm_uuid']))
            
    start_vnc(uuids['current'])
    return
def get_screenshot():
    """makes screenshot of the current root window, yields Gtk.Pixbuf"""
    pixbuf = get_screenshot_as_pixbuffer()
    b = StringIO()
    b = pixbuf.save_to_bufferv('png',[],[])
    return b

def push_pic(sender,uuids):
    global retry,conf
    url_gcfm = conf.get_url('gcfm','url_gcfm')
    try:
        current_uuid = uuids['current']
        r = requests.post(url_gcfm+'/pushpic',params={'id':current_uuid}, files={'screenshot.png': get_screenshot()[1]})
        if r.status_code == 403:
            if not retry:
                retry = True
            else:
                retry = False
            del uuids['current']
            handshake(uuids,force=(not retry))
            logger.debug("Retry handshake")
    except IOError:
        # This endpoint return 204, not 200.
        pass

def push_status(sender,uuids):
    global logger, conf
    recorder = context.get_recorder()
    repo = context.get_repository()
    url_gcfm = conf.get_url('gcfm','url_gcfm')
    #Get free space
    space = repo.get_free_space()
    #Get total space
    #TODO: Maybe move to repo
    space_info = os.statvfs(repo.get_rectemp_path())
    total_bytes = space_info.f_bsize * space_info.f_blocks

    four_gb = 4000000000.0
    hours = int(space/four_gb)

    payload = {"is-recording":recorder.is_recording(),"recorder-status":str(recorder.status),"storage-space":space,"total-space" : total_bytes,"hours-left":hours}
    host = url_gcfm+"/gccommunity/state"
    logger.info("Sending data {} to host: {}".format(payload, host))
    try:
        current_uuid = uuids['current']
        hostname = conf.get_hostname()
        r = requests.post(host,params={'id':current_uuid,'hostname':hostname}, json=payload)
    except Exception as exc:
        print exc

def start_vnc(uuid):
    global logger,dispatcher,conf
    url_repeater = conf.get_url('gcfm','url_repeater')
    command = ["which","x11vnc"]
    if not systemcalls.execute(command):
       logger.error("x11vnc not installed")
       return

    else:
        if not systemcalls.is_running("x11vnc"):
            command = ["x11vnc","-loop","-shared","-coe",url_repeater+"+ID:"+uuid]
            systemcalls.execute_without_check(command)
            logger.info("VNC server started")
        else:
            logger.info("VNC server already running")

def close_vnc(element=None):
    global logger
    command = ["killall", "-9", "x11vnc"]
    systemcalls.execute(command)
    logger.info("VNC server stopped")
