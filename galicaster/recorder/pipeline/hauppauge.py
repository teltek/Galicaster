# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/pipeline/hauppauge
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

pipestr = ( " filesrc name=gc-hauppauge-file-src ! valve drop=false name=gc-hauppauge-valve !  filesink  name=gc-hauppauge-sink async=false "
            " v4l2src name=gc-hauppauge-device-src ! queue name=queue33 ! ffmpegcolorspace ! xvimagesink qos=false async=false name=gc-hauppauge-preview " 
            " filesrc name= gc-hauppauge-audio-src ! audio/x-raw-int, rate=48000, channels=2, endianness=1234, width=16, depth=16, signed=true ! "
            " level name=gc-hauppauge-level message=true interval=100000000 ! "
            " volume name=gc-hauppauge-volume ! alsasink name=gc-hauppauge-audio-sink" )
            #" audiotestsrc ! level name=gc-hauppauge-level message=True interval=1000000000 ! audioconvert ! audioresample ! fakesink silent=true name=gc-hauppauge-audiosink " )
            #" gc-hauppauge-audio. ! queue ! mpegdemux name=demuxer "
            #" { demuxer.audio_00 ! queue ! decodebin2 ! level peak-falloff=1000 ! fakesink silent=True } " )

class GChau(gst.Bin):

    gc_parameters = {
        "vumeter": "Activate Level message",
        "player": "Enable sound play",
        # "codification": "Not implemented yet",
        }

    is_pausable = False
    
    __gstdetails__ = (
        "Galicaster Hauppauge BIN",
        "Generic/Video",
        "Add descripcion",
        "Teltek Video Research"
        )

    def __init__(self, name = None, devicesrc = {}, filesink = None, options = {}): 
        if not isinstance(devicesrc, dict):
            raise TypeError()

        for key in ("device", "file", "audio"):
            if not path.exists(devicesrc[key]):
                raise SystemError("Device error in hauppauge bin: path %s not exists" % (devicesrc[key],) )

        if name == None:
            name = "v4l2"

        gst.Bin.__init__(self, name)
        # Para usar con el gtk.DrawingArea
        bin = gst.parse_bin_from_description(pipestr.replace("gc-hauppauge-preview", "sink-" + name), True)
        # bin = gst.parse_bin_from_description(pipestr.replace("gc-hauppauge-preview", "sink-" + name), True)

        self.add(bin)

        sink = self.get_by_name("gc-hauppauge-device-src")
        sink.set_property("device", devicesrc["device"])

        sink = self.get_by_name("gc-hauppauge-file-src")
        sink.set_property("location", devicesrc["file"])

        sink = self.get_by_name("gc-hauppauge-audio-src") 
        sink.set_property("location", devicesrc["audio"])

        if "player" in options and options["player"] == "False":
            self.mute = True
            element = self.get_by_name("gc-hauppauge-volume")
            element.set_property("mute", True)
        else:
            self.mute = False

        if filesink != None:
            sink = self.get_by_name("gc-hauppauge-sink")
            sink.set_property("location", filesink)

        if "vumeter" in options:
            level = self.get_by_name("gc-hauppauge-level")
            if options["vumeter"] == "False":
                level.set_property("message", False) 


    def getValve(self):
        return self.get_by_name("gc-hauppauge-valve")

    def getVideoSink(self):
        return self.get_by_name("gc-hauppauge-preview")
  
    def send_event_to_src(self,event): # IDEA made a common for all our bins
        src1 = self.get_by_name("gc-hauppauge-device-src")
        src2 = self.get_by_name("gc-hauppauge-file-src")
        src3 = self.get_by_name("gc-hauppauge-audio-src")
        src1.send_event(event)
        src2.send_event(event)
        src3.send_event(event)

    def mute_preview(self, value):
        if not self.mute:
            element = self.get_by_name("gc-hauppauge-volume")
            element.set_property("mute", value)

gobject.type_register(GChau)
gst.element_register(GChau, "gc-hauppauge-bin")
