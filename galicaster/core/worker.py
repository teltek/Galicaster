# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/core/worker
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import sys

import os
import logging
import threading
import tempfile
import Queue
from datetime import datetime

from galicaster.mediapackage import serializer
from galicaster.mediapackage import mediapackage
from galicaster.utils import sidebyside

logger = logging.getLogger()

INGEST = 'Ingest'
ZIPPING = 'Export to Zip'
SBS = 'Side by Side'
INGEST_CODE = 'ingest'
ZIPPING_CODE = 'exporttozip'
SBS_CODE = 'sidebyside'

JOBS = { INGEST: INGEST_CODE, 
         ZIPPING: ZIPPING_CODE, 
         SBS:  SBS_CODE}

class Worker(object):

    class T(threading.Thread):

        def __init__(self, queue):
            threading.Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True: 
                job, params = self.queue.get()
                job(*params)
                self.queue.task_done()
    

    def __init__(self, dispatcher, repo, mh_client=None, export_path=None, tmp_path=None):
        """
        Arguments:

        dispacher -- the galicaster event-dispatcher to emit signals
        repo -- the galicaster mediapackage repository
        mh_client -- matterhorn HTTP client
        export_path -- path where galicaster exports zip and sidebyside
        tmp_path -- temporal path (need if /tmp partition is small)
        """
        self.repo = repo
        self.mh_client = mh_client
        self.export_path = export_path or os.path.expanduser('~')
        self.tmp_path = tmp_path or tempfile.gettempdir()
        self.dispatcher = dispatcher
        
        for dir_path in (self.export_path, self.tmp_path):
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)

        self.jobs = Queue.Queue()
        
        self.t = self.T(self.jobs)
        self.t.setDaemon(True)
        self.t.start()

        self.dispatcher.connect('galicaster-notify-nightly', self.exec_nightly)

    def get_all_job_types(self):
        nn = ' Nightly'
        return [INGEST, ZIPPING, SBS, INGEST+nn, ZIPPING+nn, SBS+nn]

    def get_all_job_types_by_mp(self, mp):
        nn = ' Nightly'
        cc = 'Cancel '
        jobs = []
        jobs_night = []

        for key,value in JOBS.iteritems():
            if key==INGEST and not self.mh_client:
                continue
            if mp.getOpStatus(value) not in [mediapackage.OP_PENDING, mediapackage.OP_PROCESSING]:
                jobs.append(key)
                night = cc+key+nn if mp.getOpStatus(value) == mediapackage.OP_NIGHTLY else key+nn
                jobs_night.append(night)            

        return jobs,jobs_night
    
    def do_job_by_name(self, name, mp_id):
        f_operation = {
            INGEST_CODE: self._ingest,
            ZIPPING_CODE: self._export_to_zip,
            SBS_CODE: self._side_by_side}
        try:
            mp = self.repo[mp_id]
            f = f_operation[name]
        except:
            logger.error("Fail get MP with id {0} or operation with name {1}".format(mp_id, name))
            return False
        f(mp)

    def do_job(self, name, mp, nigthly=False):     
        f = getattr(self, name)
        f(mp)

    def do_job_nightly(self, name, mp):
        name=name.replace('nightly','')
        if name.count('cancel'):
            self.cancel_nightly(mp, name.replace('cancel',''))
        else:
            self.operation_nightly(mp, name)      

    def ingest_nightly(self, mp):
        self.operation_nightly(mp, INGEST_CODE)

    def ingest(self, mp):
        logger.info('Creating Ingest Job for MP {0}'.format(mp.getIdentifier()))
        mp.setOpStatus('ingest',mediapackage.OP_PENDING)
        self.jobs.put((self._ingest, (mp,)))

    def _ingest(self, mp):
        if not self.mh_client:
            mp.setOpStatus('ingest', mediapackage.OP_FAILED)
            self.dispatcher.emit('stop-operation', 'ingest', mp, False)
            self.repo.update(mp)
            return
            
        logger.info('Executing Ingest for MP {0}'.format(mp.getIdentifier()))
        mp.setOpStatus('ingest',mediapackage.OP_PROCESSING)
        self.repo.update(mp)

        self.dispatcher.emit('start-operation', 'ingest', mp)
        self.dispatcher.emit('refresh-row', mp.identifier)

        ifile = tempfile.NamedTemporaryFile(dir=self.tmp_path, suffix='.zip')
        self._export_to_zip(mp, ifile, False)

        if mp.manual:
            try:
                self.mh_client.ingest(ifile.name)
                logger.info("Finalized Ingest for MP {0}".format(mp.getIdentifier()))
                mp.setOpStatus('ingest',mediapackage.OP_DONE)
                self.dispatcher.emit('stop-operation', 'ingest', mp, True)
            except:
                logger.error("Failed Ingest for MP {0}".format(mp.getIdentifier()))
                mp.setOpStatus("ingest",mediapackage.OP_FAILED)
                self.dispatcher.emit('stop-operation', 'ingest', mp, False)
        else:
            properties = mp.getOCCaptureAgentProperties()

            try:
                workflow = properties['org.opencastproject.workflow.definition']
            except:
                workflow = None

            workflow_parameters = {}
            for k, v in properties.iteritems():
                if k[0:36] == 'org.opencastproject.workflow.config.':
                    workflow_parameters[k[36:]] = v
            try:
                self.mh_client.ingest(ifile.name, workflow, mp.properties['workflow_id'], workflow_parameters)
                logger.info("Finalized Ingest for MP {0}".format(mp.getIdentifier()))
                mp.setOpStatus("ingest",mediapackage.OP_DONE)
                self.dispatcher.emit('stop-operation', 'ingest', mp, True)
            except:
                logger.error("Failed Ingest for MP {0}".format(mp.getIdentifier()))
                mp.setOpStatus("ingest",mediapackage.OP_FAILED)
                self.dispatcher.emit('stop-operation', 'ingest', mp, False)
            
        ifile.close()
        self.repo.update(mp)
            
        self.dispatcher.emit('refresh-row', mp.identifier)


    def export_to_zip(self, mp, location=None):
        logger.info('Creating ExportToZIP Job for MP {0}'.format(mp.getIdentifier()))
        mp.setOpStatus('exporttozip',mediapackage.OP_PENDING)
        self.jobs.put((self._export_to_zip, (mp, location)))


    def _export_to_zip(self, mp, location=None, is_action=True):
        if not location:
            name = datetime.now().replace(microsecond=0).isoformat()
            location = location or os.path.join(self.export_path, name + '.zip')
        if is_action:
            logger.info("Executing ExportToZIP for MP {0}".format(mp.getIdentifier()))
            mp.setOpStatus('exporttozip',mediapackage.OP_PROCESSING)
            self.dispatcher.emit('start-operation', 'exporttozip', mp)
            self.repo.update(mp)
        else:
            logger.info("Zipping MP {0}".format(mp.getIdentifier()))
        if True: #try:
            serializer.save_in_zip(mp, location)
            if is_action:
                mp.setOpStatus('exporttozip',mediapackage.OP_DONE)
                self.dispatcher.emit('stop-operation', 'exporttozip', mp, True)
        
        else: #except:
            if is_action:
                logger.error("Zip failed for MP {0}".format(mp.identifier))
                mp.setOpStatus('exporttozip',mediapackage.OP_FAILED)
                self.dispatcher.emit('stop-operation', 'exporttozip', mp, False)
            else:
                pass
        self.repo.update(mp)


    def side_by_side(self, mp, location=None):
        logger.info('Creating SideBySide Job for MP {0}'.format(mp.getIdentifier()))
        mp.setOpStatus('sidebyside',mediapackage.OP_PENDING)
        self.jobs.put((self._side_by_side, (mp, location)))


    def _side_by_side(self, mp, location=None):
        logger.info('Executing SideBySide for MP {0}'.format(mp.getIdentifier()))
        mp.setOpStatus('sidebyside',mediapackage.OP_PROCESSING)
        if not location:
            name = datetime.now().replace(microsecond=0).isoformat()
            location = location or os.path.join(self.export_path, name + '.mp4')
        self.repo.update(mp)
        self.dispatcher.emit('start-operation', 'sidebyside', mp)

        audio = None  #'camera'
        camera = screen = None
        for track in mp.getTracks():
            if track.getMimeType()[0:5] == 'audio':
                 audio = track.getURI()
            else:
                if track.getFlavor()[0:9] == 'presenter' :
                    camera = track.getURI()
                if track.getFlavor()[0:12] == 'presentation':
                    screen = track.getURI()
        try:
            sidebyside.create_sbs(location, screen, camera, audio)
            mp.setOpStatus('sidebyside',mediapackage.OP_DONE)
            self.dispatcher.emit('stop-operation', 'sidebyside', mp, True)
        except:
            logger.error("Failed SideBySide for MP {0}".format(mp.getIdentifier()))
            mp.setOpStatus('sidebyside', mediapackage.OP_FAILED)
            self.dispatcher.emit('stop-operation', 'sidebyside', mp, False)
        self.repo.update(mp)


    def operation_nightly(self, mp, operation):
        mp.setOpStatus(operation,mediapackage.OP_NIGHTLY)
        self.repo.update(mp)
        self.dispatcher.emit('refresh_row', mp.identifier)


    def cancel_nightly(self, mp, operation):
        mp.setOpStatus(operation,mediapackage.OP_IDLE)
        self.repo.update(mp)
        self.dispatcher.emit('refresh_row', mp.identifier)
    

    def exec_nightly(self, sender=None): 
        logger.info('Executing nightly process')
        for mp in self.repo.values():
            for (op_name, op_status) in mp.operation.iteritems():
                if op_status == mediapackage.OP_NIGHTLY:
                    if op_name == INGEST_CODE:
                        self.ingest(mp)
                    elif op_name == ZIPPING_CODE:
                        self.export_to_zip(mp)
                    elif op_name == SBS_CODE:
                        self.side_by_side(mp)
                    
        
