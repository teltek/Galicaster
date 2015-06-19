# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/bins/pulse
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import gobject
import gst
from os import path

from galicaster.recorder import base
from galicaster.recorder import module_register

pipestr = (" pulsesrc name=gc-audio-src ! queue name=gc-min-threshold-time gc-max-size-time gc-max-size-buffers gc-max-size-bytes gc-leaky ! "
           " audioamplify name=gc-audio-amplify amplification=1 ! "
           " tee name=tee-aud  ! queue ! level name=gc-audio-level message=true interval=100000000 ! "
           " volume name=gc-audio-volume ! alsasink sync=false name=gc-audio-preview  "
           " tee-aud. ! queue ! valve drop=false name=gc-audio-valve ! "
           " audioconvert ! gc-audio-enc ! gc-audio-mux ! "
           " queue ! filesink name=gc-audio-sink async=false " )


class GCpulse(gst.Bin, base.Base):
    
    order = ["name", "flavor", "location", "file", 
             "vumeter", "player", "amplification", "audioencoder"]

    gc_parameters = {
        "name": {
            "type": "text",
            "default": "Pulse",
            "description": "Name assigned to the device",
            },
        "flavor": {
            "type": "flavor",
            "default": "presenter",
            "description": "Matterhorn flavor associated to the track",
            },
        "location": {
            "type": "device",
            "default": "default",
            "description": "Device's mount point of output",
            },
        "file": {
            "type": "text",
            "default": "sound.mp3",
            "description": "The file name where the track will be recorded.",
            },
        "vumeter": {
            "type": "boolean",
            "default": "True",
            "description": "Activate Level message",
            },
        "player": {
            "type": "boolean",
            "default": "True",
            "description": "Enable sound play",
            },
        "amplification": {
            "type": "float",
            "default": 1.0,
            "range": (0,10),
            "description": "Audio amplification",
            },
        "delay": {
            "type": "float",
            "default": 1.0,
            "range": (0,10),
            "description": "Audio delay",
            },
        "audioencoder": {
            "type": "text",
            "default": "lamemp3enc target=1 bitrate=192 cbr=true",
            "description": "Gstreamer audio encoder element used in the bin",
            },
        "audiomuxer": {
            "type": "text",
            "default": "",
            "description": "Gstreamer audio encoder element used in the bin",
            },
        }

    is_pausable = True
    has_audio   = True
    has_video   = False
    
    __gstdetails__ = (
        "Galicaster Audio BIN",
        "Generic/Audio",
        "Plugin to capture raw audio via Pulse",
        "Teltek Video Research"
        )

    def __init__(self, options={}): 
        base.Base.__init__(self, options)
        gst.Bin.__init__(self, self.options["name"])

        aux = (pipestr.replace("gc-audio-preview", "sink-" + self.options["name"])
               .replace("gc-audio-enc", self.options["audioencoder"]))
        
        if self.options["audiomuxer"]:
            aux = aux.replace("gc-audio-mux", self.options["audiomuxer"])
        else:
            aux = aux.replace("gc-audio-mux !", "")

        if "delay" in self.options:
            aux = aux.replace('gc-max-size-time', 'max-size-time=0')
            aux = aux.replace('gc-max-size-buffers', 'max-size-buffers=0')
            aux = aux.replace('gc-max-size-bytes', 'max-size-bytes=0')
            aux = aux.replace('gc-leaky', 'leaky=0')
        else:
            aux = aux.replace('gc-max-size-time', '')
            aux = aux.replace('gc-max-size-buffers', '')
            aux = aux.replace('gc-max-size-bytes', '')
            aux = aux.replace('gc-leaky', '')

        #bin = gst.parse_bin_from_description(aux, True)
        bin = gst.parse_launch("( {} )".format(aux))
        self.add(bin)

        if self.options['location'] != "default":
            sink = self.get_by_name("gc-audio-src")
            sink.set_property("device", self.options['location'])


        sink = self.get_by_name("gc-audio-sink")
        sink.set_property('location', path.join(self.options['path'], self.options['file']))

        if "player" in self.options and self.options["player"] == False:
            self.mute = True
            element = self.get_by_name("gc-audio-volume")
            element.set_property("mute", True)
        else:
            self.mute = False

        if "vumeter" in self.options:
            level = self.get_by_name("gc-audio-level")
            if self.options["vumeter"] == False:
                level.set_property("message", False) 
        if "amplification" in self.options:
            ampli = self.get_by_name("gc-audio-amplify")
            ampli.set_property("amplification", float(self.options["amplification"]))
        if "delay" in self.options:
            delay = float(self.options["delay"])
            minttime = self.get_by_name('gc-min-threshold-time')
            minttime.set_property('min-threshold-time', long(delay * 1000000000))

    def changeValve(self, value):
        valve1=self.get_by_name('gc-audio-valve')
        valve1.set_property('drop', value)

    def getVideoSink(self):
        return self.get_by_name("gc-audio-preview")

    def getAudioSink(self):
        return self.get_by_name("gc-audio-preview")

    def getSource(self):
        return self.get_by_name("gc-audio-src")

    def send_event_to_src(self, event):
        src1 = self.get_by_name("gc-audio-src")
        src1.send_event(event)        

    def mute_preview(self, value):
        if not self.mute:
            element = self.get_by_name("gc-audio-volume")
            element.set_property("mute", value)

    
gobject.type_register(GCpulse)
gst.element_register(GCpulse, "gc-pulse-bin")
module_register(GCpulse, 'pulse')
