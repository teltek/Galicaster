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
        
        self.context = (logger, dispatcher, repo)
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

        self.rebuildQueues()
        
        self.t = self.T(self.jobs)
        self.t.setDaemon(True)
        self.t.start()

        self.dispatcher.connect('galicaster-notify-nightly', self.exec_nightly)
        #self.dispatcher.connect('galicaster-cancel-nightly', self.cancel_nightly_operations)
        #self.dispatcher.connect('galicaster-do_now-nightly', self.do_now_nightly_operations)

    def rebuildQueues(self):
        for identifier,mp in self.repo.iteritems():
            change = False
            for (op_name, op_values) in mp.operation.iteritems():
                op_value, op_time = op_values
                if op_value is mediapackage.OP_PROCESSING:
                    mp.setOpStatus(op_name, mediapackage.OP_FAILED)
                    change = True
                elif op_value is mediapackage.OP_PENDING:
                    mp.setOpStatus(op_name, mediapackage.OP_FAILED)
                    change = True
                elif op_value is mediapackage.OP_NIGHTLY:
                    op = None
                    if op:
                        self.enqueueJobNightly(op,mp)
                    else:
                        mp.setOpStatus(op_name, mediapackage.OP_IDLE)
                        change = True
            if change:
                self.repo.update(mp)        

    def enqueueJob(self, operation, package):        
        operation.logCreation(package)
        self.jobs.put( (operation.perform,(package,)) )

    def enqueueJobNightly(self, operation, package):        
        operation.logNightly(package)
        self.nightJobs.append( (operation, package) )
        
    def exec_nightly(self, origin):
        while len(self.nightJobs)>0:
            op, package = self.nightJobs.pop(0)
            self.enqueueJob( op, package )
        return True

    def cancel_nightly_operations(self, op, mps):
        pop = []
        for mp in mps:
            for operation, package in self.nightJobs:
                if mp.getIdentifier() == package.getIdentifier() and op==operation.name:
                    pop += [(operation, package)]
        for popped in pop:
            self.nightJobs.pop( self.nightJobs.index(popped) )
            popped[0].logCancelNightly( popped[1] )
                
    def do_now_nightly_operations(self, op, mps):
        pop = []
        for mp in mps:
            for operation, package in self.nightJobs:
                if mp.getIdentifier() == package.getIdentifier() and op==operation.name:
                    pop += [ (operation, package) ]
        for popped in pop:
            self.nightJobs.pop( self.nightJobs.index(popped) )
            self.enqueueJob(popped[0], popped[1])

    def enqueue_operations(self, operation, packages):
        for package in packages: # TODO perform them in order
            bound = operation[0]
            subtype = operation[1].get('shortname')
            defined = bound( subtype, operation[1], self.context )
            defined.configure( operation[2] )
            if defined.schedule.lower() == defined.IMMEDIATE:
                self.enqueueJob(defined, package)
            else:
                self.enqueueJobNightly(defined, package)
