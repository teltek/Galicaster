# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/bins/screen
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

from gi.repository import Gst

from os import path

from galicaster.recorder import base
from galicaster.recorder.utils import get_videosink

pipestr = (' ximagesrc startx=gc-startx starty=gc-starty endx=gc-endx endy=gc-endy xid=gc-xid xname=gc-xname name=gc-screen-src use-damage=0 ! queue ! '
           ' videorate ! videoconvert ! capsfilter name=gc-v4l2-vrate ! videocrop name=gc-v4l2-crop ! '
           ' tee name=gc-screen-tee  ! queue !  videoconvert  ! gc-vsink '
           ' gc-screen-tee. ! queue ! valve drop=false name=gc-screen-valve ! videoconvert ! capsfilter name=gc-v4l2-filter ! queue ! videoconvert ! '
           ' gc-screen-enc ! queue ! gc-screen-mux ! '
           ' queue ! filesink name=gc-screen-sink async=false')


class GCscreen(Gst.Bin, base.Base):

    order = ["name","flavor","location","file","caps", 
             "muxer", "endx"
             ]
 
    gc_parameters = {
        "name": {
            "type": "text",
            "default": "ScreenCapture",
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
            "description": "Device's mount point of the output",
            },
        "file": {
            "type": "text",
            "default": "CAMERA.avi",
            "description": "The file name where the track will be recorded.",
             },
        "caps": {
            "type": "caps",
            "default": "video/x-raw,framerate=5/1", 
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
        "startx":{
            "type": "integer",
            "default": 0,
            "range": (0,10000),
            "description": "top left. Must be odd (since we start at 0)",
        },
        "starty":{
            "type": "integer",
            "default": 0,
            "range": (0,10000),
            "description": "top left.  Must be odd (since we start at 0)",
        },    
        "endx":{
            "type": "integer",
            "default": 0,
            "range": (0,10000),
            "description": "bottom right. Must be odd (since we start at 0)",
        },
        "endy":{
            "type": "integer",
            "default": 0,
            "range": (0,10000),
            "description": "bottom right.  Must be odd (since we start at 0)",
        },           
        "xid":{
            "type": "hexadecimal",
            "default": 0,
            "description": "Window XID to capture from (xwininfo -tree -root)",
        },           
        "xname":{
            "type": "text",
            "default": "null",
            "description": "Window name to capture from",
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
        "Galicaster Video Test Bin",
        "Generic/Video",
        "Bin to capture screen for screencast",
        "University of Bergen",
        )


    def __init__(self, options={}):
        base.Base.__init__(self, options)
        Gst.Bin.__init__(self)

        gcvideosink = get_videosink(videosink=self.options['videosink'], name='sink-'+self.options['name'])
        aux = (pipestr.replace('gc-vsink', gcvideosink)
                      .replace('gc-screen-enc', self.options['videoencoder'])
                      .replace('gc-screen-mux', self.options['muxer'])
                      .replace('gc-startx', str(self.options['startx']))
                      .replace('gc-starty', str(self.options['starty']))
                      .replace('gc-endx', str(self.options['endx']))
                      .replace('gc-endy', str(self.options['endy']))
                      .replace('gc-xid', str(self.options['xid']))
                      .replace('gc-xname', str(self.options['xname'])))

        bin = Gst.parse_launch("( {} )".format(aux))
        self.add(bin)

        self.get_by_name('gc-screen-sink').set_property('location', path.join(self.options['path'], self.options['file']))

        self.set_option_in_pipeline('caps', 'gc-v4l2-filter', 'caps', None)

     
    def changeValve(self, value):
        valve1=self.get_by_name('gc-screen-valve')
        valve1.set_property('drop', value)

    def getVideoSink(self):
        return self.get_by_name('sink-' + self.options['name'])

    def getSource(self):
        return self.get_by_name('gc-screen-src')

    def send_event_to_src(self, event):
        src1 = self.get_by_name('gc-screen-src')
        src1.send_event(event)


