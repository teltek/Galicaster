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

import gobject
import gst
import re


from os import path

from galicaster.recorder import base
from galicaster.recorder import module_register

pipestr = (' v4l2src name=gc-v4l2-src ! capsfilter name=gc-v4l2-filter ! gc-v4l2-dec '
           ' videorate ! capsfilter name=gc-v4l2-vrate ! videocrop name=gc-v4l2-crop ! '
           ' tee name=tee-cam2  ! queue !  xvimagesink async=false qos=false name=gc-v4l2-preview'
           ' tee-cam2. ! queue ! valve drop=false name=gc-v4l2-valve ! queue ! '
           #' xvidenc bitrate=50000000 ! queue ! avimux ! '
           ' x264enc pass=5 quantizer=4 speed-preset=4 profile=1 ! queue ! avimux ! '
           #' x264enc quantizer=4 ! queue ! mp4mux ! '
           ' filesink name=gc-v4l2-sink async=false')


class GCv4l2(gst.Bin, base.Base):


    order = ["name","flavor","location","file","caps", 
             "videocrop-left","videocrop-right", "videocrop-top", "videocrop-bottom"
             "encoder", "muxer"]
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
            "type": "device",
            "default": "/dev/webcam",
            "description": "Device's mount point of the MPEG output",
            },
        "file": {
            "type": "text",
            "default": "CAMERA.avi",
            "description": "The file name where the track will be recorded.",
            },
        "caps": {
            "type": "caps",
            "default": "image/jpeg,framerate=10/1,width=640,height=480", 
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
        "encoder": {
            "type": "text",
            "default": "ffenc_mpeg2video quantizer=4 gop-size=1 bitrate=10000000",
            #Other examples: "xvidenc bitrate=50000000" or "x264enc pass=5 quantizer=22 speed-preset=4 profile=1"
            "description": "Gstreamer encoder element used in the bin",
            },
        "muxer": {
            "type": "text",
            "default": "avimux",
            "description": "Gstreamer encoder muxer used in the bin",
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
        gst.Bin.__init__(self, self.options['name'])

        aux = (pipestr.replace('gc-v4l2-preview', 'sink-' + self.options['name'])
                      .replace('gc-v4l2-enc', self.options['encoder'])
                      .replace('gc-v4l2-mux', self.options['muxer']))

        if 'image/jpeg' in self.options['caps']:
            aux = aux.replace('gc-v4l2-dec', 'jpegdec ! queue !')
        else:
            aux = aux.replace('gc-v4l2-dec', '')

        bin = gst.parse_bin_from_description(aux, True)
        self.add(bin)

        self.set_option_in_pipeline('location', 'gc-v4l2-src', 'device')
        #element = self.get_by_name('gc-v4l2-src')
        #element.set_property('device', self.options['location'])

        self.set_value_in_pipeline(path.join(self.options['path'], self.options['file']), 'gc-v4l2-sink', 'location')
        #element = self.get_by_name('gc-v4l2-sink')
        #element.set_property('location', path.join(self.options['path'], self.options['file']))

        self.set_option_in_pipeline('caps', 'gc-v4l2-filter', 'caps', gst.Caps)
        #element = self.get_by_name('gc-v4l2-filter')
        #element.set_property('caps', gst.Caps(self.options['caps']))
        fr = re.findall("framerate *= *[0-9]+/[0-9]+", self.options['caps'])
        if fr:
            newcaps = 'video/x-raw-yuv,' + fr[0]
            self.set_value_in_pipeline(newcaps, 'gc-v4l2-vrate', 'caps', gst.Caps)
            #element2 = self.get_by_name('gc-v4l2-vrate')
            #element2.set_property('caps', gst.Caps(newcaps))

        for pos in ['right','left','top','bottom']:
            self.set_option_in_pipeline('videocrop-'+pos, 'gc-v4l2-crop', pos, int)
            #element = self.get_by_name('gc-v4l2-crop')
            #element.set_property(pos, int(self.options['videocrop-' + pos]))

    def changeValve(self, value):
        valve1=self.get_by_name('gc-v4l2-valve')
        valve1.set_property('drop', value)

    def getVideoSink(self):
        return self.get_by_name('gc-v4l2-preview')
    
    def getSource(self):
        return self.get_by_name('gc-v4l2-src') 

    def send_event_to_src(self, event):
        src1 = self.get_by_name('gc-v4l2-src')
        src1.send_event(event)


gobject.type_register(GCv4l2)
gst.element_register(GCv4l2, 'gc-v4l2-bin')
module_register(GCv4l2, 'v4l2')
