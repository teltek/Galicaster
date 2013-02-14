# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
# galicaster/recorder/pipeline/rtp
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

import logging

import gobject
import gst
from os import path

from galicaster.recorder import base
from galicaster.recorder import module_register

log = logging.getLogger()

# default pipestr, override in conf.ini
pipestr = ("rtspsrc debug=false name=gc-rtp-src ! "
           "identity single-segment=true ! "
           "rtph264depay ! ffdec_h264 ! ffmpegcolorspace ! "
           "tee name=gc-rtp-tee ! queue leaky=1 ! "
           "xvimagesink async=false sync=false qos=false name=gc-rtp-preview "
           "gc-rtp-tee. ! queue ! valve drop=false name=gc-rtp-valve ! "
           "videorate skip-to-first=true ! "
           "x264enc quantizer=22 speed-preset=2 profile=1 ! queue ! avimux ! "
           "filesink name=gc-rtp-sink async=false ")

class GCrtpvideo(gst.Bin, base.Base):

    gc_parameters = {
        # http://gstreamer.freedesktop.org/data/doc/gstreamer/head/gst-plugins-good-plugins/html/gst-plugins-good-plugins-rtspsrc.html
        }

    __gstdetails__ = (
        "Galicaster RTP BIN",
        "Generic/Video",
        "Add descripcion",
        "UiB"
        )

    is_pausable = True
    has_audio = False
    has_video = True

    def __init__(self, options={}):
        base.Base.__init__(self, options)
        gst.Bin.__init__(self, self.options['name'])
        
        global pipestr

        if self.options['name'] == None:
            self.options['name'] = "rtp"

        # 2/3-2012 edpck@uib.no use pipestr from conf.ini if it exists
        if "pipestr" in self.options:
           pipestr = self.options["pipestr"].replace("\n", " ")
        
        gst.Bin.__init__(self, self.options['name'])

        aux = pipestr.replace("gc-rtp-preview", "sink-" + self.options['name'])

        bin = gst.parse_bin_from_description(aux, False)
        self.add(bin)
      
        self.set_value_in_pipeline(self.options['location'], 'gc-rtp-src', 'location')
        self.set_value_in_pipeline(path.join(self.options['path'], self.options['file']), 'gc-rtp-sink', 'location')

        for opt in ['debug', 'protocols', 'retry', 'timeout', 'latency', 'tcp-timeout', 'connection-speed', 'nat-method', 'do-rtcp', 'proxy', 'rtp-blocksize', 'user-id', 'user-pw', 'buffer-mode', 'port-range', 'udp-buffer-size']:
            if opt in options:
                self.set_value_in_pipeline(self.options[opt], 'gc-rtp-src', opt)

    def changeValve(self, value):
        valve1=self.get_by_name('gc-rtp-valve')
        valve1.set_property('drop', value)

    def getValve(self):
        return self.get_by_name("gc-rtp-valve")

    def getVideoSink(self):
        return self.get_by_name("gc-rtp-preview")

    def send_event_to_src(self,event): # IDEA made a common for all our bins
        src = self.get_by_name('gc-rtp-src')
        src.send_event(event)

gobject.type_register(GCrtpvideo)
gst.element_register(GCrtpvideo, "gc-rtp-bin")
module_register(GCrtpvideo, "rtpvideo")
