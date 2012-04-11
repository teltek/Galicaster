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

import threading
import tempfile
import Queue

from galicaster.mediapackage import serializer
from galicaster.mediapackage import mediapackage


class Worker(object):
    """
    """

    class T(threading.Thread):

        def __init__(self, queue):
            threading.Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True: 
                job, params = self.queue.get()
                job(*params)
                self.queue.task_done()
    

    def __init__(self, repo, mh_client, dispatcher=None):
        self.repo = repo
        self.mh_client = mh_client
        self.dispatcher = dispatcher

        self.jobs = Queue.Queue()
        
        self.t = self.T(self.jobs)
        self.t.setDaemon(True)
        self.t.start()



    def ingest(self, mp):
        self.jobs.put((self._ingest, (mp,)))


    def _ingest(self, mp):
        mp.status = mediapackage.INGESTING
        self.repo.update(mp)
        ifile = tempfile.NamedTemporaryFile()
        self._export_to_zip(mp, ifile)


        if mp.manual:
            try:
                self.mh_client.ingest(ifile.name)
                mp.status = mediapackage.INGESTED
            except:
                mp.status = mediapackage.INGEST_FAILED
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
                self.mh_client.ingest(ifile.name, workflow, mp.getIdentifier(), workflow_parameters)
                mp.status = mediapackage.INGESTED
            except:
                mp.status = mediapackage.INGEST_FAILED
            
        ifile.close()
        self.repo.update(mp)
            
        if self.dispatcher:
            self.dispatcher.emit('refresh-row', mp.identifier)


    def export_to_zip(self, mp, location):
        self.jobs.put((self._export_to_zip, (mp, location)))


    def _export_to_zip(self, mp, location):
        serializer.save_in_zip(mp, location)


