# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/pipeline/pulse
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


pipestr = (" pulsesrc name=gc-audio-src  !  tee name=tee-aud  ! queue ! "
           " level name=gc-audio-level message=true interval=100000000 ! "
           " volume name=gc-audio-volume ! alsasink name=gc-audio-preview  "
           " tee-aud. ! queue ! valve drop=false name=gc-audio-valve ! "
           " audioconvert ! audioamplify name=gc-audio-amplify amplification=1 ! "
           " lamemp3enc target=1 bitrate=192 cbr=true !  queue ! filesink name=gc-audio-sink async=false ")


class GCpulse(gst.Bin):
    
    gc_parameters = {
        "vumeter": "Activate Level message",
        "player": "Enable sound play",
        # "interval": "frequency of level messages"
        # "codification": "Not implemented yet"
        # "compression": "Not implemented yet"
        "amplification": "Audio amplification",
        # "filter": "Not implemented yet"
        }

    is_pausable = True
    
    __gstdetails__ = (
        "Galicaster Audio BIN",
        "Generic/Audio",
        "Add descripcion",
        "Teltek Video Research"
        )

    def __init__(self, name = None, devicesrc = None, filesink = None, options = {}): 
        if name == None:
            name = "audio"

        gst.Bin.__init__(self, name)
        # Para usar con el gtk.DrawingArea
        bin = gst.parse_bin_from_description(pipestr.replace("gc-audio-preview", "sink-" + name), True)

        self.add(bin)

        if devicesrc != None and devicesrc != "default":
            sink = self.get_by_name("gc-audio-src")
            sink.set_property("device", devicesrc)

        if filesink != None:
            sink = self.get_by_name("gc-audio-sink")
            sink.set_property("location", filesink)

        if "player" in options and options["player"] == "False":
            self.mute = True
            element = self.get_by_name("gc-audio-volume")
            element.set_property("mute", True)
        else:
            self.mute = False

        if "vumeter" in options:
            level = self.get_by_name("gc-audio-level")
            if options["vumeter"] == "False":
                level.set_property("message", False) 
        if "amplification" in options:
            ampli = self.get_by_name("gc-audio-amplify")
            ampli.set_property("amplification", float(options["amplification"]))

    def getValve(self):
        return self.get_by_name("gc-audio-valve")

    def getVideoSink(self):
        return self.get_by_name("gc-audio-preview")

    def send_event_to_src(self, event):
        src1 = self.get_by_name("gc-audio-src")
        src1.send_event(event)        

    def mute_preview(self, value):
        if not self.mute:
            element = self.get_by_name("gc-audio-volume")
            element.set_property("mute", value)

    
gobject.type_register(GCpulse)
gst.element_register(GCpulse, "gc-pulse-bin")
