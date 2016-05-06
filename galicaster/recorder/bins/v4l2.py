# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/bins/v4l2
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

from os import path
import re

from gi.repository import GObject, Gst
#Gst.init(None)

from galicaster.recorder import base
from galicaster.recorder import module_register

from galicaster.recorder.utils import get_videosink

pipestr = (' v4l2src name=gc-v4l2-src ! capsfilter name=gc-v4l2-filter ! queue ! gc-v4l2-dec '
           ' videorate ! videoconvert ! capsfilter name=gc-v4l2-vrate ! videocrop name=gc-v4l2-crop ! gc-videofilter ! '
           ' tee name=gc-v4l2-tee  ! queue ! gc-vsink '
           ' gc-v4l2-tee. ! queue ! valve drop=false name=gc-v4l2-valve ! videoconvert ! queue ! '
           ' gc-v4l2-enc ! queue ! gc-v4l2-mux ! '
           ' queue ! filesink name=gc-v4l2-sink async=false')


class GCv4l2(Gst.Bin, base.Base):


    order = ["name","flavor","location","file","caps", 
             "videoencoder", "muxer"]
    
    gc_parameters = {
        "name": {
            "type": "text",
            "default": "Webcam",
            "description": "Name assigned to the device",
            },
        "flavor": {
            "type": "flavor",
            "default": "presenter",
            "description": "Opencast flavor associated to the track",
            },
        "location": {
            "type": "device",
            "default": '/dev/video0',
            "description": "Device's mount point of the output",
            },
        "file": {
            "type": "text",
            "default": "CAMERA.avi",
            "description": "The file name where the track will be recorded.",
            },
        "caps": {
            "type": "caps",
            "default": "video/x-raw,framerate=20/1,width=640,height=480", 
            # image/jpeg,framerate=10/1,width=640,height=480", 
            "description": "Forced capabilities",
            },
        "videocrop-right": {
            "type": "integer",
            "default": 0,
            "range": (0,200),
            "description": "Right  Cropping",
            },
        "videocrop-left": {
            "type": "integer",
            "default": 0,
            "range": (0,200),
            "description": "Left  Cropping",
            },
        "videocrop-top": {
            "type": "integer",
            "default": 0,
            "range": (0,200),
            "description": "Top  Cropping",
            },
        "videocrop-bottom": {
            "type": "integer",
            "default": 0,
            "range": (0,200),
            "description": "Bottom  Cropping",
            },
        "videoencoder": {
            "type": "text",
            "default": "x264enc pass=5 quantizer=22 speed-preset=4",
            "description": "Gstreamer encoder element used in the bin",
            },
        "muxer": {
            "type": "text",
            "default": "avimux",
            "description": "Gstreamer encoder muxer used in the bin",
            },
        "videofilter": {
            "type": "text",
            "default": "",
            "description": "Videofilter elements (like: videoflip method=rotate-180)",
            },
        "videosink" : {
            "type": "select",
            "default": "xvimagesink",
            "options": ["xvimagesink", "ximagesink", "autovideosink", "fpsdisplaysink","fakesink"],
            "description": "Video sink",
        },
    }
    
    is_pausable = True
    has_audio   = False
    has_video   = True

    __gstdetails__ = (
        "Galicaster V4L2 Bin",
        "Generic/Video",
        "Generice bin to v4l2 interface devices",
        "Teltek Video Research",
        )

    def __init__(self, options={}):
        base.Base.__init__(self, options)
        Gst.Bin.__init__(self)

        gcvideosink = get_videosink(videosink=self.options['videosink'], name='sink-'+self.options['name'])
        aux = (pipestr.replace('gc-vsink', gcvideosink)
               .replace('gc-v4l2-enc', self.options['videoencoder'])
               .replace('gc-v4l2-mux', self.options['muxer']))
    
        if self.options['videofilter']:
            aux = aux.replace('gc-videofilter', self.options['videofilter'])
        else:
            aux = aux.replace('gc-videofilter !', '')
            

        if 'image/jpeg' in self.options['caps']:
            aux = aux.replace('gc-v4l2-dec', 'jpegdec max-errors=-1 ! queue !')
        else:
            aux = aux.replace('gc-v4l2-dec', '')

        #bin = Gst.parse_bin_from_description(aux, True)
        bin = Gst.parse_launch("( {} )".format(aux))
        self.add(bin)

        if self.options['location']:
            self.set_option_in_pipeline('location', 'gc-v4l2-src', 'device')

        self.set_value_in_pipeline(path.join(self.options['path'], self.options['file']), 'gc-v4l2-sink', 'location')

        self.set_option_in_pipeline('caps', 'gc-v4l2-filter', 'caps', None)


    def changeValve(self, value):
        valve1=self.get_by_name('gc-v4l2-valve')
        valve1.set_property('drop', value)

    def getVideoSink(self):
        return self.get_by_name('sink-' + self.options['name'])
    
    def getSource(self):
        return self.get_by_name('gc-v4l2-src') 

    def send_event_to_src(self, event):
        src1 = self.get_by_name('gc-v4l2-src')
        src1.send_event(event)


#GObject.type_register(GCv4l2)
#Gst.element_register(GCv4l2, 'gc-v4l2-bin')
#module_register(GCv4l2, 'v4l2')

#GCv4l2Type = GObject.type_register(GCv4l2)
#Gst.Element.register(GCv4l2, 'gc-v4l2-bin', 0, GCv4l2Type)
