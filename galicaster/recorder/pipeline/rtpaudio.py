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

from galicaster.recorder import base
from galicaster.recorder import module_register

log = logging.getLogger()

# default pipestr, override in conf.ini
pipestr = ("rtspsrc debug=false name=gc-rtp-audio-src ! "
           "identity single-segment=true ! "
           "rtpmp4gdepay ! faad ! tee name=tee-aud ! queue leaky=1 ! "
           "level name=gc-rtp-audio-level message=true interval=100000000 ! "
           "volume name=gc-rtp-audio-volume ! fakesink name=gc-rtp-audio-preview "
           "tee-aud. ! queue ! valve drop=false name=gc-rtp-audio-valve ! "
           "audioconvert ! audioamplify name=gc-rtp-audio-amplify amplification=1 ! "
           "faac ! mp4mux ! "
           "filesink name=gc-rtp-audio-sink async=false ")

class GCrtpaudio(gst.Bin, base.Base):

    order = ["name", "flavor", "location", "file", 
             "vumeter", "player","amplification",
             "volume", "pattern", "frequency",
             ]
    
    gc_parameters = {
        # http://gstreamer.freedesktop.org/data/doc/gstreamer/head/gst-plugins-good-plugins/html/gst-plugins-good-plugins-rtspsrc.html
        "name": {
            "type": "text",
            "default": "IP-audio",
            "description": "Name assigned to the device",
            },
        "flavor": {
            "type": "flavor",
            "default": "presenter",
            "description": "Matterhorn flavor associated to the track",
            },
        "location": {
            "type": "device",
            "default": "rtsp://viewer:opencastZen@129.177.9.29:554/axis-media/media.amp?resolution=160x120",
            "description": "Device's mount point of the MPEG output",
            },
        "file": {
            "type": "text",
            "default": "sound.mp3",
            "description": "The file name where the track will be recorded.",
            },
        "vumeter": {
            "type": "boolean",
            "default": True,
            "description": "Activate Level message",
            },
        "player": {
            "type": "boolean",
            "default": True,
            "description": "Enable sound play",
            },
        "amplification": {
            "type": "float",
            "default": 1.0,
            "range": (0,10),
            "description": "Audio amplification",
            },
        "volume": {
            "type": "float",
            "default": 0.5,
            "range": (0,1),
            "description": "Audio volume",
            },
        "pattern": {
            "type": "select",
            "default": "pink-noise",
            "options": ["sine", "square", "saw", "triangle",
                        "white-noise", "pink-noise", "sine-table"
                        "ticks", "gaussian-noise", "red-noise"
                        "blue-noise", "violet-noise"
                        ],                                  
            "description" : "Premade samples to test audio",
            },                      
        "frequency":  {
            "type": "integer",
            "default" : 440,
            "range" : (0, 20000),
            "description": "Reference frequency of the sample, 0-20000 Hz"
            },
        }

    __gstdetails__ = (
        "Galicaster RTP BIN",
        "Generic/Audio",
        "Add descripcion",
        "UiB"
        )
    is_pausable = True
    has_audio = True
    has_video = False

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

        aux = pipestr.replace("gc-rtp-audio-preview", "sink-" + self.options['name'])

        bin = gst.parse_bin_from_description(aux, False)
        self.add(bin)

        self.set_value_in_pipeline(self.options['location'], 'gc-rtp-audio-src', 'location')
        self.set_value_in_pipeline(path.join(self.options['path'], self.options['file']), 'gc-rtp-audio-sink', 'location')
        
        for opt in ['debug', 'protocols', 'retry', 'timeout', 'latency', 'tcp-timeout', 'connection-speed', 'nat-method', 'do-rtcp', 'proxy', 'rtp-blocksize', 'user-id', 'user-pw', 'buffer-mode', 'port-range', 'udp-buffer-size']:
            if opt in options:
                self.set_value_in_pipeline(self.options[opt], 'gc-rtp-audio-src', opt)

        if "vumeter" in self.options and self.options["vumeter"] == "False":
            self.get_by_name("gc-rtp-audio-level").set_property("message", False) 

        if "amplification" in self.options:
            self.get_by_name("gc-rtp-audio-amplify").set_property("amplification", float(self.options["amplification"]))
    
    def changeValve(self, value):
        self.get_by_name('gc-rtp-audio-valve').set_property('drop', value)

    def getValve(self):
        return self.get_by_name("gc-rtp-audio-valve")

    def getVideoSink(self):
        return self.get_by_name("gc-rtp-audio-preview")
       

    def send_event_to_src(self, event):
        self.get_by_name("gc-rtp-audio-src").send_event(event)        

    def mute_preview(self, value):
        self.get_by_name("gc-rtp-audio-volume").set_property("mute", value)

gobject.type_register(GCrtpaudio)
gst.element_register(GCrtpaudio, "gc-rtp-audio-bin")
module_register(GCrtpaudio, 'rtpaudio')