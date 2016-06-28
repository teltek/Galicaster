# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/pushpic
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
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

import requests
import json
import os

retry = False

def init():
    global repo, logger
    dispatcher = context.get_dispatcher()
    logger = context.get_logger()
    repo = context.get_repository()
    try:
        uuids =json.load(repo.get_attach("uuid1.json"))
    except Exception as exc:
        logger.warning("{}".format(exc))
        uuids = {}

    handshake(uuids)
    dispatcher.connect('timer-short', push_pic,uuids)
    dispatcher.connect('timer-short', push_status,uuids)

def handshake(uuids, force=False):
    global repo, logger

    if not 'current' in uuids:
        r = requests.get('http://localhost:5001/gcfm_uuid')
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
    return
def get_screenshot():
    """makes screenshot of the current root window, yields Gtk.Pixbuf"""
    pixbuf = get_screenshot_as_pixbuffer()
    b = StringIO()
    b = pixbuf.save_to_bufferv('png',[],[])
    return b

def push_pic(sender,uuids):
    global retry
    try:
        current_uuid = uuids['current']
        r = requests.post('http://localhost:5001/pushpic',params={'id':current_uuid}, files={'screenshot.png': get_screenshot()[1]})
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
    global logger
#    payload = {"hue":"huehuehue"}
    recorder = context.get_recorder()
    repo = context.get_repository()
    #Get free space
    space = repo.get_free_space()
    #Get total space
    #TODO: Maybe move to repo
    space_info = os.statvfs(repo.get_rectemp_path())
    total_bytes = space_info.f_bsize * space_info.f_blocks
    payload = {"is-recording":recorder.is_recording(),"recorder-status":str(recorder.status),"storage-space":space,"total-space" : total_bytes}
    logger.info("sending data {}".format(payload))
    try:
        current_uuid = uuids['current']
        r = requests.post('http://localhost:5001/gccommunity/state',params={'id':current_uuid}, json=payload)
    except Exception as exc:
        print exc
