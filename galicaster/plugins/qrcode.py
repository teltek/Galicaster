# The MIT License (MIT)
#
# Copyright (c) 2014 The University of Manchester
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re
from threading import Timer
from os import path, utime, remove
from gi.repository import Gst
Gst.init(None)

from galicaster.core import context

# options:
# pause_mode = [hold|start_stop] (hold)
# hold_code = <string> (hold)
# start_code = <string> (start)
# stop_code = <string> (stop)
# rescale = <WidthxHeight> (source)
# hold_timeout = <secs> (1)
# mp_add_edits = <boolean> (False)
# mp_force_trimhold = <boolean> (False)
# mp_add_smil = <boolean> (False)
# drop_frames = <boolean> (False)
# buffers = <integer> (200)

# NOTE: the timestamps are for the duration that the pipeline has been running
# ie in preview/recording not just recording
ZBAR_MESSAGE_PATTERN = ("timestamp=\(guint64\)(?P<timestamp>[0-9]+), "
                        "type=\(string\)(?P<type>.+), "
                        "symbol=\(string\)(?P<symbol>.+), "
                        "quality=\(int\)(?P<quality>[0-9]+)")

NANO2SEC = 1000000000.0
SEC2NANO = 1000000000
WORKFLOW_CONFIG = 'org.opencastproject.workflow.config'


def init():
    try:
        conf = context.get_conf()
        mode = conf.get('qrcode', 'pause_mode') or 'hold'  # or 'start_stop'
        symbols = {}
        symbols['start'] = conf.get('qrcode', 'start_code') or 'start'
        symbols['stop'] = conf.get('qrcode', 'stop_code') or 'stop'
        symbols['hold'] = conf.get('qrcode', 'hold_code') or 'hold'
        rescale = conf.get('qrcode', 'rescale') or 'source'
        drop_frames = conf.get_boolean('qrcode', 'drop_frames') or False
        buffers = conf.get_int('qrcode', 'buffers') or 200
        hold_timeout = conf.get_int('qrcode', 'hold_timeout') or 1  # secs
        ignore_bins = conf.get('qrcode', 'ignore_track_name') or None
        qr = QRCodeScanner(mode, symbols, hold_timeout, rescale, drop_frames, buffers, ignore_bins, context.get_logger())

        dispatcher = context.get_dispatcher()
        dispatcher.connect('recorder-ready', qr.qrcode_add_pipeline)
        # only process sync-messages when recording to reduce overhead
        dispatcher.connect('recorder-started', qr.qrcode_connect_to_sync_message)
        dispatcher.connect('recorder-stopped', qr.qrcode_disconnect_to_sync_message)
        qr.set_add_edits(conf.get_boolean('qrcode', 'mp_add_edits') or False)
        qr.set_trimhold(conf.get_boolean('qrcode', 'mp_force_trimhold') or False)
        qr.set_add_smil(conf.get_boolean('qrcode', 'mp_add_smil') or False)
        dispatcher.connect('recorder-stopped', qr.qrcode_update_mediapackage)

    except ValueError:
        pass


class QRCodeScanner():
    def __init__(self, mode, symbols, hold_timeout, rescale, drop_frames, buffers, ignore_bins, logger=None):
        self.symbol_start = symbols['start']
        self.symbol_stop = symbols['stop']
        self.symbol_hold = symbols['hold']
        self.mode = mode
        self.rescale = rescale
        self.drop_frames = drop_frames
        self.queue_buffers = buffers
        if ignore_bins:
            self.ignore_bins_list = ignore_bins.split(',')
        else:
            self.ignore_bins_list = []
        self.hold_timeout = hold_timeout  # secs
        self.hold_timeout_ns = hold_timeout * SEC2NANO  # nano secs
        self.hold_timestamp = 0
        self.hold_timer = None
        self.hold_timer_timestamp = 0
        self.logger = logger
        self.pipeline = None
        self.bins = None
        self.recording_paused = False
        self.pause_state_file = path.join(context.get_repository().get_rectemp_path(), "paused")
        # self.logger.debug(self.pause_state_file)
        self.sync_msg_handler = None
        self.msg_pattern = re.compile(ZBAR_MESSAGE_PATTERN)
        # mediapackage modifiers
        self.trimhold = False
        self.add_smil = False
        self.add_edits = False
        self.recorder = context.get_recorder()
        self.dispatcher = context.get_dispatcher()

    # set additional parameters
    def set_trimhold(self, v):
        self.trimhold = v

    def set_add_smil(self, v):
        self.add_smil = v

    def set_add_edits(self, v):
        self.add_edits = v

    # signal handlers
    def qrcode_connect_to_sync_message(self, sender, mpid):
        # self.logger.debug("Connecting to sync messages")
        # NOTE This callback runs just before the recording actually starts
        #      Therefore recording_start_timestamp is a bit early

        # clock = recorderui.recorder.pipeline.get_clock()
        # self.recording_start_timestamp = clock.get_time() - recorderui.recorder.pipeline.get_base_time()
        self.recording_start_timestamp = self.recorder.recorder.get_recording_start_time()
        self.total_pause_duration = 0
        self.last_pause_timestamp = 0
        self.editpoints = []
        self.sync_msg_handler = self.dispatcher.connect('recorder-message-element', self.qrcode_on_sync_message)

    def qrcode_disconnect_to_sync_message(self, sender, mpurl):
        # self.logger.debug("Disconnecting from sync messages")
        self.dispatcher.disconnect(self.sync_msg_handler)

        # for e in self.editpoints:
        #    self.logger.debug(e)

    def qrcode_on_sync_message(self, sender, message): #, bus, message
        if message.get_name() == "barcode":
            # Message fields are:
            # name, timestamp, type, symbol, quality
            # but there is no get_value function!
            fieldstr = message.to_string()

            m = re.search(self.msg_pattern, fieldstr)
            timestamp = int(m.group('timestamp'))
            type = m.group('type')
            symbol = m.group('symbol')
            quality = int(m.group('quality'))

            # ignore non qrcodes
            if type == 'QR-Code':
                self.handle_symbol(symbol, timestamp)

    def handle_symbol(self, symbol, timestamp):
        gst_status = self.recorder.recorder.get_status()[1]
        if self.recorder.is_recording and gst_status == Gst.State.PLAYING:
            if self.mode == 'hold':
                if self.symbol_hold == symbol:
                    # pause
                    if not self.recording_paused:
                        # self.logger.debug('PAUSING')
                        self.recorder.pause()
                        self.write_pause_state(True)
                        # set UI state so that MP duration is calculated correctly
                        self.recorder.pause()
                        self.logger.info('Paused recording at {}'.format((timestamp) / NANO2SEC))
                        self.recording_paused = True
                        self.hold_timestamp = 0
                        self.hold_timer = None
                        self.hold_timer_timestamp = 0
                        # store editpoints
                        self.editpoints.append(
                            (timestamp - self.total_pause_duration - self.recording_start_timestamp) / NANO2SEC)
                        self.logger.info('Editpoint @ {}'.format(self.editpoints[len(self.editpoints) - 1]))
                        self.last_pause_timestamp = timestamp

                    # setup restart
                    # every hold_timeout create a timer call 2x hold_timeout in the future
                    # max delay in resume is 2x hold_timeout
                    if not self.hold_timer or ((timestamp - self.hold_timer_timestamp) >= self.hold_timeout_ns):
                        # self.logger.debug("Creating timer...{} {}".format(timestamp, self.hold_timer_timestamp)
                        self.hold_timer = Timer(self.hold_timeout * 2, self.has_hold_timed_out, [self.recorder, timestamp])
                        self.hold_timer.start()
                        self.hold_timer_timestamp = timestamp

                    # temporary store this TS
                    self.hold_timestamp = timestamp

            else:  # mode == start_stop
                if symbol == self.symbol_stop and not self.recording_paused:
                    # self.logger.debug('PAUSING')
                    self.logger.info('Paused recording at {}'.format(timestamp))
                    self.recording_paused = True
                    self.recorder.pause()

                if symbol == self.symbol_start and self.recording_paused:
                    # self.logger.debug('RESUMING')
                    self.logger.info('Resumed recording at {}'.format(timestamp))
                    self.recording_paused = False
                    self.recorder.resume()

    def has_hold_timed_out(self, recorder, timestamp):
        # self.logger.debug( '...timer testing {} {} {}'.format(timestamp, self.hold_timestamp, self.hold_timestamp-timestamp)
        # how old is self.hold_timestamp?
        if (self.hold_timestamp - timestamp) < self.hold_timeout_ns:
            # self.logger.debug( 'RESUMING {} {}'.format(timestamp, self.hold_timestamp)
            self.recording_paused = False
            self.write_pause_state(False)
            # Check if the 'recording' has been ended
            if self.recorder.is_recording:
                self.recorder.resume()
                # old way for getting recording start time
                # clock = recorder.pipeline.get_clock()
                # gstimestamp = clock.get_time() - recorder.pipeline.get_base_time()
                gstimestamp = self.recorder.get_recorded_time()
                self.logger.info('Resumed recording at {}'.format(gstimestamp / NANO2SEC))
                self.logger.info('Paused for {}'.format((gstimestamp - self.last_pause_timestamp) / NANO2SEC))
                self.total_pause_duration += gstimestamp - self.last_pause_timestamp
                self.hold_timer = None

    def qrcode_add_pipeline(self, signal=None):
        """
        find the video device with the configured flavour and add the zbar pipe to that

        Create the following subpipe:
        queue name=zbar-queue ! valve name=zbar-valve drop=False ! videoscale ! capsfilter name=zbar-filter
        ! zbar name=zbar message=True ! fakesink'

        """
        pipeline = self.recorder.recorder.pipeline
        bins = self.recorder.recorder.bins
        for name, bin in bins.iteritems():
            if name in self.ignore_bins_list:
                self.logger.info('qrcode disabled on track with name: {}'.format(name))
                pass
            else:
                if bin.has_video:
                    device = bin.options['device']

                    zbar_queue = Gst.ElementFactory.make("queue", "zbar-{}-queue".format(device))
                    zbar_valve = Gst.ElementFactory.make("valve", "zbar-{}-valve".format(device))
                    zbar_videoscale = Gst.ElementFactory.make("videoscale")
                    zbar_filter = Gst.ElementFactory.make("capsfilter", "zbar-{}-filter".format(device))
                    zbar_zbar = Gst.ElementFactory.make("zbar", "zbar-{}-zbar".format(device))
                    zbar_fakesink = Gst.ElementFactory.make("fakesink")

                    if self.drop_frames:
                        zbar_queue.set_property('leaky', 2)
                    zbar_queue.set_property('max-size-buffers', self.queue_buffers)

                    expr = '[0-9]+[\,x\:][0-9]+'  # Parse custom size
                    if self.rescale != 'source' and re.match(expr, self.rescale):
                        wh = [int(a) for a in self.rescale.split(re.search('[,x:]', self.rescale).group())]
                        zbar_caps = Gst.caps_from_string("video/x-raw, format=YUV width={}, height={}".format(wh[0], wh[1]))
                        zbar_filter.set_property("caps", zbar_caps)
                    else:
                        zbar_caps = Gst.caps_from_string("video/x-raw, format=YUV")

                    zbar_filter.set_property("caps", zbar_caps)

                    tee_name = 'gc-' + device + '-tee'
                    tee = bin.get_by_name(tee_name)

                    bin.add(zbar_queue)
                    bin.add(zbar_valve)
                    bin.add(zbar_videoscale)
                    bin.add(zbar_filter)
                    bin.add(zbar_zbar)
                    bin.add(zbar_fakesink)

                    tee.link(zbar_queue)
                    zbar_queue.link(zbar_valve)
                    zbar_valve.link(zbar_videoscale)
                    zbar_videoscale.link(zbar_filter)
                    zbar_filter.link(zbar_zbar)
                    zbar_zbar.link(zbar_fakesink)

        self.pipeline = pipeline
        self.bins = bins

    def qrcode_update_mediapackage(self, sender, mpURI):
        """
        Optional updating of Mediapackage 'org.opencastproject.capture.agent.properties' file with QR code edit points.
        May be used it later processing by Opencast workflow.

        """
        if (self.add_edits or self.trimhold or self.add_smil):
            mp = self.recorder.current_mediapackage
            occap = mp.getOCCaptureAgentProperties()

            if len(self.editpoints):
                if self.add_edits:
                    # self.logger.debug('Adding WF Edit parameters')
                    # flag that we want the workflow to edit our mediapackage
                    occap[WORKFLOW_CONFIG + '.editor'] = 'true'

                    editpoints_str = ','.join(map(str, self.editpoints))
                    occap[WORKFLOW_CONFIG + '.qrcEditpoints'] = editpoints_str
                    occap[WORKFLOW_CONFIG + '.qrcNEditpoints'] = len(self.editpoints)

                if self.trimhold:
                    # self.logger.debug('Forcing WF trimHold')
                    occap[WORKFLOW_CONFIG + '.trimHold'] = 'true'

                if self.add_smil:
                    self.create_smil(mp, occap)

            occap_list = []
            for prpt, value in occap.items():
                occap_list.append(prpt + '=' + str(value))

            prpts_str = '\n'.join(occap_list)

            mp.addAttachmentAsString(prpts_str, 'org.opencastproject.capture.agent.properties', False,
                                     'org.opencastproject.capture.agent.properties')
            # FIXME: add to WF props for manual recordings too

    def create_smil(self, mp, occap):
        # TODO: call smil service
        self.logger.info('Create SMIL - disabled')

    def write_pause_state(self, state):
        if state:
            if path.exists(self.pause_state_file):
                utime(self.pause_state_file, None)
            else:
                open(self.pause_state_file, 'a').close()
        else:
            remove(self.pause_state_file)

