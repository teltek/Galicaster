# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/bins/firewireraw
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
Experimental bin to re-encode the dv video and audio with Galicaster on the fly.
"""

import gobject
import gst

from os import path

from galicaster.recorder import base

pipestr = (' dv1394src name=gc-firewireraw-src ! '
           ' queue ! dvdemux name=gc-firewireraw-demuxer ! '
           ' level name=gc-firewireraw-level message=true interval=100000000 ! '
           ' tee name=gc-firewireraw-audiotee ! '
           ' queue ! volume name=gc-firewireraw-volume ! alsasink sync=false name=gc-firewireraw-audio-sink '
           ' gc-firewireraw-demuxer. ! queue ! ffdec_dvvideo ! ffmpegcolorspace ! queue ! tee name=gc-firewireraw-videotee ! '
           ' xvimagesink qos=false async=false sync=false name=gc-firewireraw-preview '
           ' gc-firewireraw-audiotee. ! queue ! valve drop=false name=gc-firewireraw-audio-valve ! audio/x-raw-int ! ' 
           ' gc-firewireraw-audioenc ! gc-firewireraw-muxer ! '
           ' queue ! filesink name=gc-firewireraw-sink async=false '
           ' gc-firewireraw-videotee. ! queue ! valve drop=false name=gc-firewireraw-video-valve ! '
           ' videorate skip-to-first=true ! videoscale ! gc-firewireraw-capsfilter ! gc-firewireraw-videoenc ! gc-firewireraw-mux. '
           )

class GCfirewireraw(gst.Bin, base.Base):
    gc_parameters = {
        "name": {
            "type": "text",
            "default": "Firewireraw",
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
            "default": "CAMERA.avi",
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
        "caps": {
            "type": "caps",
            "default": "video/x-raw-yuv,width=720,height=576,framerate=25/1",
            "description": "Forced capabilities",
            },
        "videoencoder": {
            "type": "text",
            "default": "x264enc quantizer=22 speed-preset=2 profile=1",
            #Other examples: "xvidenc bitrate=50000000" or "ffenc_mpeg2video quantizer=4 gop-size=1 bitrate=10000000"
            "description": "Gstreamer video encoder element used in the bin",
            },
        "audioencoder": {
            "type": "text",
            "default": "lamemp3enc target=1 bitrate=192 cbr=true",
            "description": "Gstreamer audio encoder element used in the bin",
            },
        "muxer": {
            "type": "text",
            "default": "avimux",
            "description": "Gstreamer muxer element used in the bin, NOT USE NAME ATTR",
            },
        
        }
    is_pausable = False
    has_audio   = True
    has_video   = True
    
    __gstdetails__ = (
        "Galicaster Firewireraw BIN",
        "Generic/Video",
        "Add descripcion",
        "Teltek Video Research"
        )

    def __init__(self, options={}): 
        base.Base.__init__(self, options)
        gst.Bin.__init__(self, self.options["name"])

        aux = (pipestr.replace("gc-firewireraw-preview", "sink-" + self.options["name"])
               .replace('gc-firewireraw-videoenc', self.options['videoencoder'])
               .replace('gc-firewireraw-muxer', self.options['muxer']+' name=gc-firewireraw-mux')
               .replace('gc-firewireraw-audioenc', self.options['audioencoder'])
               .replace('gc-firewireraw-capsfilter', self.options['caps'])
              )
        #bin = gst.parse_bin_from_description(aux, False)
        bin = gst.parse_launch("( {} )".format(aux))

        self.add(bin)

        sink = self.get_by_name("gc-firewireraw-sink")
        sink.set_property('location', path.join(self.options['path'], self.options['file']))

        if self.options["vumeter"] == False:
            level = self.get_by_name("gc-firewireraw-level")
            level.set_property("message", False) 

        if self.options["player"] == False:
            self.mute = True
            element = self.get_by_name("gc-firewireraw-volume")
            element.set_property("mute", True)        
        else:
            self.mute = False

    def changeValve(self, value):
        valve1=self.get_by_name('gc-firewireraw-video-valve')
        valve2=self.get_by_name('gc-firewireraw-audio-valve')
        valve1.set_property('drop', value)
        valve2.set_property('drop', value)

    def getVideoSink(self):
        return self.get_by_name("gc-firewireraw-preview")

    def getSource(self):
        return self.get_by_name("gc-firewireraw-src")
  
    def send_event_to_src(self,event):
        src1 = self.get_by_name("gc-firewireraw-src")
        src1.send_event(event)

    def mute_preview(self, value):
        if not self.mute:
            element = self.get_by_name("gc-firewireraw-volume")
            element.set_property("mute", value)

    def configure(self):
        ## 
        # v4l2-ctl -d self.options["location"] -s self.options["standard"]
        # v4l2-ctl -d self.options["location"] -i self.options["input"]
        pass
     

gobject.type_register(GCfirewireraw)
gst.element_register(GCfirewireraw, "gc-firewireraw-bin")
