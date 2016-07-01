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
occlient = context.get_occlient()
repo = context.get_repository()

check_published = conf.get_boolean('retryingest', 'check_published')
check_after = conf.get_int('retryingest', 'check_after') or 300
check_nightly = conf.get_boolean('retryingest', 'nightly')
last_checked = time.time()



def init():        
    logger.debug('check_published set to {}'.format(check_published))
    logger.debug('check_after set to {}'.format(str(check_after)))
    logger.debug('check_nightly set to {}'.format(check_nightly))
    
    try:
        dispatcher = context.get_dispatcher()
        dispatcher.connect('timer-short', reingest)        
    except ValueError:
        pass


def is_published(mp_id, mp):
    # check if the mediapackage is published to the search index
    search_result = occlient.search_by_mp_id(mp_id)
    if int(search_result['total']):
        logger.debug('mediapackage {} is already published'.format(mp_id))
        # mediapackage has actually been ingested successfully at some point
        # as it is published in opencast so set the state to "done"
        mp.setOpStatus('ingest', mediapackage.OP_DONE)
        repo.update(mp)
        return True
    logger.debug('mediapackage {} is not published'.format(mp_id))
    return False


def reingest(sender=None):
    global last_checked

    # only run if it is time
    if (last_checked + check_after) >= time.time():
        return

    worker = context.get_worker()
    for mp_id, mp in repo.iteritems():
        logger.debug('reingest checking: {0} status: {1}'.format(mp_id,
                                                                 mediapackage.op_status[mp.getOpStatus('ingest')]))
        # only finished recordings
        if not (mp.status == mediapackage.SCHEDULED or mp.status == mediapackage.RECORDING):
            if mp.getOpStatus('ingest') == mediapackage.OP_FAILED:
                # check mediapackage status on opencast if needed
                if (check_published and not is_published(mp_id, mp)) or not check_published:
                    # postpone the ingest until the 'nightly' ingest time else ingest immediately
                    if check_nightly:
                        logger.info('scheduled nightly reingest of failed mediapackage: {}'.format(mp_id))
                        mp.setOpStatus("ingest", mediapackage.OP_NIGHTLY)
                        repo.update(mp)
                    else:
                        logger.info('Starting reingest of failed mediapackage: {}'.format(mp_id))
                        worker.ingest(mp)
    last_checked = time.time()

