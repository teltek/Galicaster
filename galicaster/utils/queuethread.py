# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/queuethread
#
# Copyright (c) 2016, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import threading
from galicaster.core import context

class T(threading.Thread):

    def __init__(self, queue):
        """
        Initializes a Thread with a queue of jobs to be done concurrently with other Galicaster tasks.
        Args:
                queue (Queue): queue of jobs.
        Attributes:
            queue (Queue): queue of jobs.
        """
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        """Runs and removes a job from the queue.
        Marks the job as done.
        """
        logger = context.get_logger()
        while True:
            job, params = self.queue.get()
            try:
                job(*params)
            except Exception as exc:
                logger.error(exc)
            self.queue.task_done()
