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

"""
The 'oldblackmagic' bin is preserved to keep the support to Blackmagic capture cards with the Ubuntu version 10.10. For new versions, please use the 'blackmagic' bin.
"""
from gi.repository import Gst

from os import path

from galicaster.recorder import base
from galicaster.recorder.utils import get_videosink

pipestr = ( ' decklinksrc input=sdi input-mode=12 name=gc-blackmagic-src ! capsfilter name=gc-blackmagic-filter ! '
            ' videorate ! capsfilter name=gc-blackmagic-vrate ! videocrop name=gc-blackmagic-crop ! '
            ' tee name=tee-cam2  ! queue ! gc-vsink '
            ' tee-cam2. ! queue ! valve drop=false name=gc-blackmagic-valve ! ffmpegcolorspace ! queue ! '
            #' xvidenc bitrate=50000000 ! queue ! avimux ! '
            ' x264enc quantizer=22 speed-preset=2 profile=1 ! queue ! avimux ! '
            #' ffenc_mpeg2video quantizer=4 gop-size=1 bitrate=10000000 ! queue ! avimux ! '
            ' queue ! filesink name=gc-blackmagic-sink async=false' )

class GColdblackmagic(Gst.Bin, base.Base):

  order = ["name","flavor","location","file","input","input-mode"]

  gc_parameters = {
        "name": {
            "type": "text",
            "default": "Blackmagic",
            "description": "Name assigned to the device",
            },
        "flavor": {
            "type": "flavor",
            "default": "presenter",
            "description": "Opencast flavor associated to the track",
            },
        "location": {
            "type": "device",
            "default": "/dev/blackmagic/card0",
            "description": "Device's mount point of the MPEG output",
            },
        "file": {
            "type": "text",
            "default": "CAMERA.mpg",
            "description": "The file name where the track will be recorded.",
            },
        "caps": {
            "type": "caps",
            "default": "", #??????
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
            "default": "0",
            "range": (0,200),
            "description": "Left  Cropping",
            },
        "videocrop-top": {
            "type": "integer",
            "default": "0",
            "range": (0,200),
            "description": "Top  Cropping",
            },
        "videocrop-bottom": {
            "type": "integer",
            "default": "0",
            "range": (0,200),
            "description": "Bottom  Cropping",
            },
        "input" : {
            "type": "select",
            "default": "sdi",
            "options": [
        "sdi", "hdmi", "opticalsdi",
        "component", "composite", "svideo"
        ],
            "description": "Video input to capture from",
            },
        "input-mode" : {
            "type": "select",
            "default": "1080p25",
            "options": [
        "ntsc","ntsc2398", "pal", "720p50", "720p5994",
        "720p60", "1080p2398", "1080p24", "1080p25", 
        "1080p2997", "1080p30", "1080i50", "1080i5994", 
        "1080i60", "1080p50", "1080p5994", "1080p60", 
        "2k2398", "2k24", "2k25"],

#            "options": {
#                "1": "ntsc", "2": "ntsc2398", "3": "pal", "4": "720p50", "5": "720p5994",
#                "6": "720p60", "7": "1080p2398", "8": "1080p24", "9": "1080p25", "10": "1080p2997",
#                "11": "1080p30", "12": "1080i50", "13": "1080i5994", "14": "1080i60", "15": "1080p50",
#                "16": "1080p5994", "17": "1080p60", "18": "2k2398", "19": "2k24", "20": "2k25",
#                },
            "description": "Video input mode (resolution and frame rate)",
            },
    "videosink" : {
      "type": "select",
      "default": "xvimagesink",
      "options": ["xvimagesink", "ximagesink", "autovideosink", "fpsdisplaysink","fakesink"],
      "description": "Video sink",
    },
  }
  
    
  is_pausable = True
  has_audio    = False
  has_video    = True
    
  __gstdetails__ = (
        "Galicaster blackmagic Bin",
        "Generic/Video",
        "Add descripcion",
        "University of Helsinki & Teltek Video Research",
        )

  def __init__(self, options={}):
        raise Exception("Not implemented. Using gst 0.10")

        base.Base.__init__(self, options)
        Gst.Bin.__init__(self, self.options['name'])

        gcvideosink = get_videosink(videosink=self.options['videosink'], name='sink-'+self.options['name'])
        aux = pipestr.replace('gc-vsink', gcvideosink)
        bin = Gst.parse_bin_from_description(aux, True)
        # replace identity
        self.add(bin)

        element = self.get_by_name('gc-blackmagic-sink')
        element.set_property('location', path.join(self.options['path'], self.options['file']))
        
        element = self.get_by_name('gc-blackmagic-src')
        try:
            value = int(self.options['input'])
        except ValueError:
            value = self.options['input']                                
        element.set_property('input', value)

        element = self.get_by_name('gc-blackmagic-src')
        try:
            mode = int(self.options['input-mode'])
        except ValueError:
            mode = self.options['input-mode']                                
        element.set_property('input-mode', mode)

        for pos in ['right','left','top','bottom']:
            element = self.get_by_name('gc-blackmagic-crop')
            element.set_property(pos, int(self.options['videocrop-' + pos]))

  def changeValve(self, value):
    valve1=self.get_by_name('gc-blackmagic-valve')
    valve1.set_property('drop', value)

  def getVideoSink(self):
    return self.get_by_name('sink-' + self.options['name'])

  def getSource(self):
    return self.get_by_name('gc-blackmagic-src')

  def send_event_to_src(self, event):
    src1 = self.get_by_name('gc-blackmagic-src')
    src1.send_event(event)

