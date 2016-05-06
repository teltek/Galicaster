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

from os import path

from gi.repository import GObject, Gst

from galicaster.recorder import base
#from galicaster.recorder import module_register
from galicaster.recorder.utils import get_audiosink

pipestr = (" pulsesrc name=gc-audio-src  ! queue ! audioamplify name=gc-audio-amplify amplification=1 ! "
           " audioconvert ! audio/x-raw,channels=gc-audio-channels ! "
           " tee name=tee-aud  ! queue ! level name=gc-audio-level message=true interval=100000000 ! "
           " volume name=gc-audio-volume ! gc-asink "
           " tee-aud. ! queue ! valve drop=false name=gc-audio-valve ! "
           " audioconvert ! gc-audio-enc ! gc-audio-mux ! "
           " queue ! filesink name=gc-audio-sink async=false " )


class GCpulse(Gst.Bin, base.Base):
    
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
            "description": "Opencast flavor associated to the track",
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
            "range": (1.0,10),
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
        "channels": {
            "type": "integer",
            "default": 2,
            "range": (1,16),
            "description": "Number of audio channels",
            },
        "audiosink" : {
            "type": "select",
            "default": "autoaudiosink",
            "options": ["autoaudiosink", "alsasink", "pulsesink", "fakesink"],
            "description": "Audio sink",
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
        Gst.Bin.__init__(self)

        gcaudiosink = get_audiosink(audiosink=self.options['audiosink'], name='sink-'+self.options['name'])
        aux = (pipestr.replace('gc-asink', gcaudiosink)
               .replace("gc-audio-enc", self.options["audioencoder"])
               .replace("gc-audio-channels", str(self.options["channels"])))
        
        if self.options["audiomuxer"]:
            aux = aux.replace("gc-audio-mux", self.options["audiomuxer"])
        else:
            aux = aux.replace("gc-audio-mux !", "")

        #bin = Gst.parse_bin_from_description(aux, True)
        bin = Gst.parse_launch("( {} )".format(aux))
        self.add(bin)

        if self.options['location'] != "default":
            sink = self.get_by_name("gc-audio-src")
            sink.set_porperty("device", self.options['location'])


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


    def changeValve(self, value):
        valve1=self.get_by_name('gc-audio-valve')
        valve1.set_property('drop', value)

    def getVideoSink(self):
        return None

    def getAudioSink(self):
        return self.get_by_name('sink-' + self.options['name'])

    def getSource(self):
        return self.get_by_name("gc-audio-src")

    def send_event_to_src(self, event):
        src1 = self.get_by_name("gc-audio-src")
        src1.send_event(event)        

    def mute_preview(self, value):
        if not self.mute:
            element = self.get_by_name("gc-audio-volume")
            element.set_property("mute", value)

    
#GObject.type_register(GCpulse)
#Gst.element_register(GCpulse, "gc-pulse-bin")
#module_register(GCpulse, 'pulse')

#GCpulseType = GObject.type_register(GCpulse)
#Gst.Element.register(GCpulse, 'gc-pulse-bin', 0, GCpulseType)
