# retryingest galicaster plugin
#
# Copyright 2014 University of Sussex
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import time

from galicaster.core import context
from galicaster.mediapackage import mediapackage

logger = context.get_logger()
conf = context.get_conf()

check_after = conf.get_int('retryingest', 'check_after') or 300
last_checked = 0

logger.debug('check_after set to %i', check_after)

def init():        
    try:
        dispatcher = context.get_dispatcher()
        dispatcher.connect('galicaster-notify-timer-short', reingest)        
    except ValueError:
        pass

def reingest(sender=None):
    global last_checked

    # only run if it is time
    if (last_checked + check_after) >= time.time():
        return

    repo = context.get_repository()
    worker = context.get_worker()

    for mp_id, mp in repo.iteritems():
        logger.debug('reingest checking: %s status: %s', 
                     mp_id, mediapackage.op_status[mp.getOpStatus('ingest')])
        if mp.getOpStatus('ingest') == mediapackage.OP_FAILED:
            logger.info('Starting reingest of failed mediapackage: %s', mp_id)
            worker.ingest(mp)

    last_checked = time.time()
