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

videostr = ( ' decklinksrc connection=sdi mode=12 name=gc-blackmagic-src ! '
             ' identity name=gc-blackmagic-idvideo ! videorate ! gc-blackmagic-capsfilter !'
             ' queue ! videocrop name=gc-blackmagic-crop ! '
             ' tee name=gc-blackmagic-tee  ! queue ! ffmpegcolorspace ! xvimagesink async=false sync=false name=gc-blackmagic-preview'
             #REC VIDEO
             ' gc-blackmagic-tee. ! queue ! valve drop=false name=gc-blackmagic-valve ! ffmpegcolorspace ! '
             ' gc-blackmagic-enc ! queue ! gc-blackmagic-muxer ! '
             ' queue ! identity name=gc-blackmagic-idend ! filesink name=gc-blackmagic-sink async=false' 
             )
audiostr= (
            #AUDIO
            ' gc-blackmagic-src.audiosrc ! identity name=gc-blackmagic-idaudio ! queue ! '
            ' audiorate ! audioamplify name=gc-blackmagic-amplify amplification=1 ! '
            ' tee name=gc-blackmagic-audiotee ! queue ! '
            ' level name=gc-blackmagic-level message=true interval=100000000 ! '
            ' volume name=gc-blackmagic-volume ! queue ! alsasink sync=false name=gc-blackmagic-audio-preview '
            # REC AUDIO
            ' gc-blackmagic-audiotee. ! queue ! valve drop=false name=gc-blackmagic-audio-valve ! '
            ' audioconvert ! gc-blackmagic-audioenc ! queue ! gc-blackmagic-muxer. '
            )

FRAMERATE = dict(zip(
    ["ntsc","ntsc2398", "pal", "ntsc-p","pal-p", "1800p2398", "1080p24", "1080p25", "1080p2997", "1080p30", "1080i50", "1080i5994", "1080i60", "1080p50", "1080p5994", "1080p60", "720p50", "720p5994","720p60"],
    ["30000/1001","24000/1001", "25/1", "30000/1001","25/1", "24000/1001", "24/1", "25/1", "30000/1001", "30/1", "25/1", "30000/1001", "30/1", "50/1", "60000/1001", "60/1", "50/1", "60000/1001","60/1"]
    ))


class GCblackmagic(gst.Bin, base.Base):

  order = ["name","flavor","location","file",
           "input-mode","input","audio-input","subdevice",
           "vumeter", "player", "amplification", 
           "videoencoder", "audioencoder", "muxer"]

  gc_parameters = {
    "name": {
      "type": "text",
      "default": "Blackmagic",
      "description": "Name assigned to the device",
      },
    "flavor": {
      "type": "flavor",
      "default": "presenter",
      "description": "Matterhorn flavor associated to the track",
      },
    "location": {
      "type": "device",
      "default": "/dev/blackmagic0",
      "description": "Device's mount point of the output",
      },
    "file": {
      "type": "text",
      "default": "CAMERA.avi",
      "description": "The file name where the track will be recorded.",
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
        "sdi", "hdmi", "optical-sdi",
        "component", "composite", "svideo"
        ],
      "description": "Type of connection for the video input to capture from",
      },
    "input-mode" : {
      "type": "select",
      "default": "1080p25",
      "options": [
        "ntsc","ntsc2398", "pal", "ntsc-p","pal-p",        
        "1080p2398", "1080p24", "1080p25", "1080p2997", "1080p30", 
        "1080i50", "1080i5994", "1080i60", 
        "1080p50", "1080p5994", "1080p60", 
        "720p50", "720p5994","720p60", 
        ],
      "description": "Video input mode (resolution and frame rate)",
      },
    "audio-input" : {
      "type": "select",
      "default": "auto",
      "options": [
        "auto", "embedded", "aes","analog", "none"
        ],
      "description": "Audio  input mode",
      },
    "framerate" : {
      "type": "select",
      "default": "auto",
      "options": ["auto", "24/1", "25/1","30/1"],
      "description": "Output framerate",
      },
    "subdevice" : {
      "type": "select",
      "default": "0",
      "options": [
        "0", "1", "2","3" 
        ],
      "description": "Select a Blackmagic card from a maximum of 4 devices",
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
      "range": (0,10),
      "description": "Audio amplification",
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
    
    
  is_pausable  = False
  has_audio    = True
  has_video    = True
    
  __gstdetails__ = (
        "Galicaster blackmagic Bin",
        "Generic/Video",
        "Blackmagic plugin for decklinksrc on gstreamer-plugins-uggly",
        "Teltek Video Research",
        )

  def __init__(self, options={}):
        base.Base.__init__(self, options)
        gst.Bin.__init__(self, self.options['name'])

        pipestr = videostr

        if self.options['framerate'] == "auto":
          self.options['framerate'] = FRAMERATE[self.options["input-mode"]]
          
        aux = (pipestr.replace('gc-blackmagic-preview', 'sink-' + self.options['name'])
               .replace('gc-blackmagic-enc', self.options['videoencoder'])
               .replace('gc-blackmagic-muxer', self.options['muxer']+" name=gc-blackmagic-muxer")
               .replace('gc-blackmagic-capsfilter', "video/x-raw-yuv,framerate={0}".format(self.options['framerate']))
               )

        if self.options["audio-input"] == "none":
          self.has_audio = False
        else:
          self.has_audio = True  
          aux += audiostr
          aux = aux.replace('gc-blackmagic-audioenc', self.options['audioencoder'])

        #bin = gst.parse_bin_from_description(aux, False)
        bin = gst.parse_launch("( {} )".format(aux))
        self.add(bin)

        sink = self.get_by_name('gc-blackmagic-sink')
        sink.set_property('location', path.join(self.options['path'], self.options['file']))
        
        element = self.get_by_name('gc-blackmagic-src')
        try:
            value = int(self.options['input'])
        except ValueError:
            value = self.options['input']                                
        element.set_property('connection', value)

        try:
            mode = int(self.options['input-mode'])
        except ValueError:
            mode = self.options['input-mode']                                
        element.set_property('mode', mode)

        if self.has_audio:
          try:
            audio = int(self.options['audio-input'])
          except ValueError:
            audio = self.options['audio-input']                                
          element.set_property('audio-input', audio)
        else:
          element.set_property('audio-input', "auto")
          
        try:
          subdevice = int(self.options['subdevice'])
        except ValueError:
          subdevice = self.options['subdevice']                                
        element.set_property('subdevice', subdevice)

        if self.has_audio:
          if "player" in self.options and self.options["player"] == False:
            self.mute = True
            element = self.get_by_name("gc-blackmagic-volume")
            element.set_property("mute", True)
          else:
            self.mute = False

          if "vumeter" in self.options:
            level = self.get_by_name("gc-blackmagic-level")
            if self.options["vumeter"] == False:
              level.set_property("message", False)

          if "amplification" in self.options:
            ampli = self.get_by_name("gc-blackmagic-amplify")
            ampli.set_property("amplification", float(self.options["amplification"]))

        for pos in ['right','left','top','bottom']:
            element = self.get_by_name('gc-blackmagic-crop')
            element.set_property(pos, int(self.options['videocrop-' + pos]))

  def changeValve(self, value):
    valve1=self.get_by_name('gc-blackmagic-valve')
    if self.has_audio:
      valve2=self.get_by_name('gc-blackmagic-audio-valve')
      valve2.set_property('drop', value)
    valve1.set_property('drop', value)

  def getVideoSink(self):
    return self.get_by_name('gc-blackmagic-preview')

  def getSource(self):
    return self.get_by_name('gc-blackmagic-src')

  def getAudioSink(self):
    return self.get_by_name('gc-blackmagic-audio-preview')

  def mute_preview(self, value):
    if not self.mute:
      element = self.get_by_name("gc-blackmagic-volume")
      element.set_property("mute", value)

  def send_event_to_src(self, event):
    src = self.get_by_name('gc-blackmagic-src')
    src.set_state(gst.STATE_NULL)
    src.get_state()

    src_video = self.get_by_name('gc-blackmagic-idvideo')
    if self.has_audio:
      src_audio = self.get_by_name('gc-blackmagic-idaudio')
      src_audio.send_event(event)
    src_video.send_event(event)
    


gobject.type_register(GCblackmagic)
gst.element_register(GCblackmagic, 'gc-blackmagic-bin')
module_register(GCblackmagic, 'blackmagic')
