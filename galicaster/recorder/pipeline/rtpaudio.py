# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/pipeline/rtp
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
import galicaster

log = logging.getLogger()

# default pipestr, override in conf.ini
pipestr = (" rtspsrc name=gc-rtp-audio-src ! "
           " decodebin2 ! tee name=tee-aud ! queue leaky=1 ! " 
           " level name=gc-rtp-audio-level message=true interval=100000000 ! "
           " volume name=gc-rtp-audio-volume ! fakesink name=gc-rtp-audio-preview "
           " tee-aud. ! queue ! valve drop=false name=gc-rtp-audio-valve ! "
           " audioconvert ! audioamplify name=gc-rtp-audio-amplify amplification=1 ! "
           " lamemp3enc target=bitrate cbr=true bitrate=192 ! "
           " filesink name=gc-rtp-audio-sink async=false ")

class GCrtpaudio(gst.Bin):

    gc_parameters = {
        # http://gstreamer.freedesktop.org/data/doc/gstreamer/head/gst-plugins-good-plugins/html/gst-plugins-good-plugins-rtspsrc.html
        }

    __gstdetails__ = (
        "Galicaster RTP BIN",
        "Generic/Audio",
        "Add descripcion",
        "UiB"
        )

    def __init__(self, name = None, devicesrc = None, filesink = None, options = {}): 
        global pipestr

        if name == None:
            name = "rtp-audio"

        # 2/3-2012 edpck@uib.no use pipestr from conf.ini if it exists
        if "pipestr" in options:
            pipestr = options["pipestr"].replace("\n", " ")

        gst.Bin.__init__(self, name)

        bin = gst.parse_bin_from_description(pipestr.replace("gc-rtp-audio-preview", "sink-" + name), False)
        self.add(bin)

        if devicesrc != None:
            sink = self.get_by_name('gc-rtp-audio-src')
            sink.set_property('location', devicesrc)

            for opt in ['debug', 'protocols', 'retry', 'timeout', 'latency', 'tcp-timeout', 'connection-speed', 'nat-method', 'do-rtcp', 'proxy', 'rtp-blocksize', 'user-id', 'user-pw', 'buffer-mode', 'port-range', 'udp-buffer-size']:
                if opt in options:
                    sink.set_property(opt, options[opt])

        if filesink != None:
            sink = self.get_by_name("gc-rtp-audio-sink")
            sink.set_property("location", filesink)

        if "vumeter" in options:
            level = self.get_by_name("gc-rtp-audio-level")
            if options["vumeter"] == "False":
                level.set_property("message", False ) 

        if "amplification" in options:
            ampli = self.get_by_name("gc-rtp-audio-amplify")
            ampli.set_property("amplification", float(options["amplification"]))

    def getValve(self):
        return self.get_by_name("gc-rtp-audio-valve")

    def getVideoSink(self):
        return self.get_by_name("gc-rtp-audio-preview")

    def send_event_to_src(self, event):
        src = self.get_by_name("gc-rtp-audio-src")
        src.send_event(event)        

    def mute_preview(self, value):
        element = self.get_by_name("gc-rtp-audio-volume")
        element.set_property("mute", value)

gobject.type_register(GCrtpaudio)
gst.element_register(GCrtpaudio, "gc-rtp-audio-bin")
