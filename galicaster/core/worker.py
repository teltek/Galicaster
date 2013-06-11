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

import os
import threading
import tempfile
import Queue
from galicaster.mediapackage import mediapackage

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
    

    def __init__(self, dispatcher, repo, logger, mh_client=None, export_path=None, tmp_path=None, 
                 use_namespace=True, sbs_layout='sbs'):
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
        self.use_namespace = use_namespace
        self.sbs_layout = sbs_layout
        self.dispatcher = dispatcher
        self.logger = logger
        
        for dir_path in (self.export_path, self.tmp_path):
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)

        self.jobs = Queue.Queue()
        self.nightJobs = []
        
        self.t = self.T(self.jobs)
        self.t.setDaemon(True)
        self.t.start()

        self.dispatcher.connect('galicaster-notify-nightly', self.exec_nightly)


    def enqueueJob(self, operation, package):        
        operation.setCreationTime()
        self.jobs.put( (operation.perform,(package,)) ) # TODO log

    def enqueueJobNightly(self, operation, package):        
        operation.logNightly(package)
        self.nightJobs.append( (operation, package) )
        
    def exec_nightly(self, origin):
        while len(self.nightJobs)>0:
            op, package = self.nightJobs.pop(0)
            self.enqueueJob( op, package )
        return True
                                   


        #self.jobs.put( (operation.perform,(package,)) ) # TODO log
        
    # TODO enqueue nightly
    # save subtype, date and options to rebuild operations
