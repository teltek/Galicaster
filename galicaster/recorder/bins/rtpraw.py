# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/bins/rtpraw
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.
# 

from gi.repository import Gst

from os import path

from galicaster.recorder import base
from galicaster.recorder.utils import get_videosink

pipe_config = {'mpeg4':
                   {'depay': 'rtpmp4vdepay', 'parse': 'mpeg4videoparse', 'dec': 'avdec_mpeg4'},
               'h264':
                   {'depay': 'rtph264depay', 'parse': 'h264parse', 'dec': 'avdec_h264'}} 


pipestr = (' rtspsrc name=gc-rtpraw-src ! gc-rtpraw-depay ! gc-rtpraw-videoparse ! queue ! '
           ' gc-rtpraw-dec ! videoscale ! capsfilter name=gc-rtpraw-filter ! '
           ' tee name=gc-rtpraw-tee  ! queue ! gc-vsink '
           ' gc-rtpraw-tee. ! queue ! valve drop=false name=gc-rtpraw-valve ! videoconvert ! '
           ' queue ! gc-rtpraw-enc ! queue ! gc-rtpraw-muxer name=gc-rtpraw-mux ! queue ! filesink name=gc-rtpraw-sink async=false')
 


class GCrtpraw(Gst.Bin, base.Base):


    order = ["name", "flavor", "location", "file", "videoencoder", "muxer", "cameratype"]
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
            "type": "text",
            "default": "rtsp://127.0.0.1/mpeg4/media.amp",
            "description": "Location of the RTSP url to read",
            },
        "caps": {
            "type": "caps",
            "default": "video/x-raw-yuv,framerate=25/1", 
            "description": "Forced capabilities",
            },
        "file": {
            "type": "text",
            "default": "CAMERA.avi",
            "description": "The file name where the track will be recorded.",
            },
        "videoencoder": {
            "type": "text",
            "default": "x264enc pass=5 quantizer=22 speed-preset=4",
            # "ffenc_mpeg2video quantizer=4 gop-size=1 bitrate=10000000",
            # "xvidenc bitrate=5000000"
            "description": "Gstreamer encoder element used in the bin",
            },
        "muxer": {
            "type": "text",
            "default": "mpegpsmux",
            "description": "The file name where the track will be recorded.",
            },
        "cameratype": {
            "type": "select",
            "default": "h264",
            "options": [
                "h264", "mpeg4"
                ],
            "description": "RTP Camera encoding type",
            },
        "videosink" : {
            "type": "select",
            "default": "xvimagesink",
            "options": ["xvimagesink", "ximagesink", "autovideosink", "fpsdisplaysink","fakesink"],
            "description": "Video sink",
        },    
    }
    
    is_pausable = False
    has_audio   = False
    has_video   = True

    __gstdetails__ = (
        "Galicaster RTP Bin",
        "Generic/Video",
        "Generice bin to rtpraw interface devices",
        "Teltek Video Research",
        )

    def __init__(self, options={}):
        base.Base.__init__(self, options)
        Gst.Bin.__init__(self)

        gcvideosink = get_videosink(videosink=self.options['videosink'], name='sink-'+self.options['name'])
        aux = (pipestr.replace('gc-vsink', gcvideosink)
               .replace('gc-rtpraw-depay', pipe_config[self.options['cameratype']]['depay'])
               .replace('gc-rtpraw-videoparse', pipe_config[self.options['cameratype']]['parse'])
               .replace('gc-rtpraw-dec', pipe_config[self.options['cameratype']]['dec'])
               .replace('gc-rtpraw-enc', self.options['videoencoder'])
               .replace('gc-rtpraw-muxer', self.options['muxer']))

        bin = Gst.parse_launch("( {} )".format(aux))
        self.add(bin)

        self.set_option_in_pipeline('caps', 'gc-rtpraw-filter', 'caps', Gst.Caps)
        self.set_option_in_pipeline('location', 'gc-rtpraw-src', 'location')
        self.set_value_in_pipeline(path.join(self.options['path'], self.options['file']), 'gc-rtpraw-sink', 'location')


    def changeValve(self, value):
        valve1=self.get_by_name('gc-rtpraw-valve')
        valve1.set_property('drop', value)

    def getVideoSink(self):
        return self.get_by_name('sink-' + self.options['name'])
    
    def getSource(self):
        return self.get_by_name('gc-rtpraw-src') 

    def send_event_to_src(self, event):
        src1 = self.get_by_name('gc-rtpraw-src')
        src1.send_event(event)

