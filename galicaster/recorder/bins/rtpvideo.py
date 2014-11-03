# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/bins/rtpvideo
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.
# 
# TODO:
#  - Change mux. Dont use flvmux
#  - In cameratype mpeg4 dont use decodebin2
#

from gi.repository import GObject
from gi.repository import Gst
import re

from os import path

from galicaster.recorder import base
from galicaster.recorder import module_register

raise Exception("Not implemented. Using gst 0.10")

pipe_config = {'mpeg4':
                   {'depay': 'rtpmp4vdepay', 'videoparse': 'mpeg4videoparse', 'dec': 'decodebin2'},
               'h264':
                   {'depay': 'rtph264depay', 'videoparse': 'h264parse', 'dec': 'ffdec_h264'}} 

pipestr = (' rtspsrc name=gc-rtpvideo-src ! gc-rtpvideo-depay ! gc-rtpvideo-videoparse ! '
           ' tee name=gc-rtpvideo-tee  ! queue ! gc-rtpvideo-dec  ! xvimagesink async=false sync=false qos=false name=gc-rtpvideo-preview'
           ' gc-rtpvideo-tee. ! queue ! valve drop=false name=gc-rtpvideo-valve ! '
           ' queue ! gc-rtpvideo-mux ! filesink name=gc-rtpvideo-sink async=false')


class GCrtpvideo(Gst.Bin, base.Base):


    order = ["name", "flavor", "location", "file", "videomux", "cameratype"]
    gc_parameters = {
        "name": {
            "type": "text",
            "default": "Webcam",
            "description": "Name assigned to the device",
            },
        "flavor": {
            "type": "flavor",
            "default": "presenter",
            "description": "Matterhorn flavor associated to the track",
            },
        "location": {
            "type": "text",  #TODO add URL
            "default": "rtsp://127.0.0.1/mpeg4/media.amp",
            "description": "Location of the RTSP url to read",
            },
        "file": {
            "type": "text",
            "default": "CAMERA.avi",
            "description": "The file name where the track will be recorded.",
            },
        "videomux": {
            "type": "text",
            "default": "flvmux",
            "description": "The file name where the track will be recorded.",
            },
        "cameratype": {
            "type": "select",
            "default": "h264",
            "options": [
                "h264", "mpeg4"
                ],
            "description": "Camera type",
            }
        }
    
    is_pausable = False
    has_audio   = False
    has_video   = True

    __gstdetails__ = (
        "Galicaster RTPVIDEO Bin",
        "Generic/Video",
        "Generice bin to rtpvideo interface devices",
        "Teltek Video Research",
        )

    def __init__(self, options={}):
        base.Base.__init__(self, options)
        Gst.Bin.__init__(self, self.options['name'])

        aux = (pipestr.replace('gc-rtpvideo-preview', 'sink-' + self.options['name'])
               .replace('gc-rtpvideo-depay', pipe_config[self.options['cameratype']]['depay'])
               .replace('gc-rtpvideo-videoparse', pipe_config[self.options['cameratype']]['videoparse'])
               .replace('gc-rtpvideo-dec', pipe_config[self.options['cameratype']]['dec'])
               .replace('gc-rtpvideo-mux', self.options['videomux']))

        bin = Gst.parse_bin_from_description(aux, False)
        self.add(bin)

        self.set_option_in_pipeline('location', 'gc-rtpvideo-src', 'location')

        self.set_value_in_pipeline(path.join(self.options['path'], self.options['file']), 'gc-rtpvideo-sink', 'location')

    def changeValve(self, value):
        valve1=self.get_by_name('gc-rtpvideo-valve')
        valve1.set_property('drop', value)

    def getVideoSink(self):
        return self.get_by_name('gc-rtpvideo-preview')
    
    def getSource(self):
        return self.get_by_name('gc-rtpvideo-src') 

    def send_event_to_src(self, event):
        src1 = self.get_by_name('gc-rtpvideo-src')
        src1.send_event(event)


GObject.type_register(GCrtpvideo)
Gst.element_register(GCrtpvideo, 'gc-rtpvideo-bin')
module_register(GCrtpvideo, 'rtpvideo')
