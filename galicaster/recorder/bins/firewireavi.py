# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/bins/firewireavi
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
Experimental bin which re-multiplexes the DV video to an AVI container so that it can be used in Windows operating systems.
"""

import gobject
import gst

from os import path

from galicaster.recorder import base

pipestr = (' dv1394src name=gc-firewireavi-src ! '
           ' queue ! dvdemux name=gc-firewireavi-demuxer ! '
           ' level name=gc-firewireavi-level message=true interval=100000000 ! '
           ' tee name=gc-firewireavi-audiotee ! '
           ' queue ! volume name=gc-firewireavi-volume ! alsasink sync=false name=gc-firewireavi-audio-sink '
           ' gc-firewireavi-demuxer. ! queue ! tee name=gc-firewireavi-videotee ! '
           ' queue ! ffdec_dvvideo ! ffmpegcolorspace ! xvimagesink qos=false async=false sync=false name=gc-firewireavi-preview '
           ' gc-firewireavi-audiotee. ! queue ! valve drop=false name=gc-firewireavi-audio-valve ! audio/x-raw-int ! avimux name=gc-firewireavi-mux ! '
           ' queue ! filesink name=gc-firewireavi-sink async=false '
           ' gc-firewireavi-videotee. ! queue ! valve drop=false name=gc-firewireavi-video-valve ! video/x-dv ! gc-firewireavi-mux.  '
           )

class GCfirewireavi(gst.Bin, base.Base):
    gc_parameters = {
        "name": {
            "type": "text",
            "default": "Firewireavi",
            "description": "Name assigned to the device",
            },
        "flavor": {
            "type": "flavor",
            "default": "presenter",
            "description": "Matterhorn flavor associated to the track",
            },
        "location": {
            "type": "device",
            "default": "/dev/fw1",
            "description": "Device's mount point of the firewire module",
            },
            
        "file": {
            "type": "text",
            "default": "CAMERA.dv",
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

        "format" : {
            "type": "select",
            "default": "dv",
            "options": {
                "dv" : "dv1394src",
                "hdv" : "hdv1394src",
                "iidc" : "dc1394src",
                },
            "description": "Select video format",
            },
        
        }
    is_pausable = False
    has_audio   = True
    has_video   = True
    
    __gstdetails__ = (
        "Galicaster Firewireavi BIN",
        "Generic/Video",
        "Add descripcion",
        "Teltek Video Research"
        )

    def __init__(self, options={}): 
        base.Base.__init__(self, options)
        gst.Bin.__init__(self, self.options["name"])

        aux = pipestr.replace("gc-firewireavi-preview", "sink-" + self.options["name"])
        #bin = gst.parse_bin_from_description(aux, False)
        bin = gst.parse_launch("( {} )".format(aux))

        self.add(bin)

        sink = self.get_by_name("gc-firewireavi-sink")
        sink.set_property('location', path.join(self.options['path'], self.options['file']))

        if self.options["vumeter"] == False:
            level = self.get_by_name("gc-firewireavi-level")
            level.set_property("message", False) 

        if self.options["player"] == False:
            self.mute = True
            element = self.get_by_name("gc-firewireavi-volume")
            element.set_property("mute", True)        
        else:
            self.mute = False

    def changeValve(self, value):
        valve1=self.get_by_name('gc-firewireavi-video-valve')
        valve2=self.get_by_name('gc-firewireavi-audio-valve')
        valve1.set_property('drop', value)
        valve2.set_property('drop', value)

    def getVideoSink(self):
        return self.get_by_name("gc-firewireavi-preview")

    def getSource(self):
        return self.get_by_name("gc-firewireavi-src")
  
    def send_event_to_src(self,event):
        src1 = self.get_by_name("gc-firewireavi-src")
        src1.send_event(event)

    def mute_preview(self, value):
        if not self.mute:
            element = self.get_by_name("gc-firewireavi-volume")
            element.set_property("mute", value)

    def configure(self):
        ## 
        # v4l2-ctl -d self.options["location"] -s self.options["standard"]
        # v4l2-ctl -d self.options["location"] -i self.options["input"]
        pass
     

gobject.type_register(GCfirewireavi)
gst.element_register(GCfirewireavi, "gc-firewireavi-bin")
