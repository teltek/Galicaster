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

from gi.repository import Gst
#Gst.init(None)

from galicaster.recorder import base
from galicaster.recorder.utils import get_videosink, get_audiosink

videostr = ( ' decklinkvideosrc connection=hdmi mode=720p60 name=gc-blackmagic-src ! videoconvert ! queue ! '
             ' videorate ! gc-blackmagic-capsfilter !'
             ' queue ! videocrop name=gc-blackmagic-crop ! '
             ' tee name=gc-blackmagic-tee  ! queue ! videoconvert ! gc-vsink '
             #REC VIDEO
             ' gc-blackmagic-tee. ! queue ! valve drop=false name=gc-blackmagic-valve ! videoconvert ! '
             ' gc-blackmagic-enc ! queue ! gc-blackmagic-muxer ! '
             ' queue ! filesink name=gc-blackmagic-sink async=false' 
             )
audiostr= (
            #AUDIO
            ' decklinkaudiosrc device-number=0 connection=auto name=gc-blackmagic-audiosrc ! queue ! '
            ' audiorate ! audioamplify name=gc-blackmagic-amplify amplification=1 ! '
            ' tee name=gc-blackmagic-audiotee ! queue ! '
            ' level name=gc-blackmagic-level message=true interval=100000000 ! '
            ' volume name=gc-blackmagic-volume ! queue ! gc-asink '
            # REC AUDIO
            ' gc-blackmagic-audiotee. ! queue ! valve drop=false name=gc-blackmagic-audio-valve ! '
            ' audioconvert ! gc-blackmagic-audioenc ! queue ! gc-blackmagic-muxer. '
            )


FRAMERATE = dict(zip(
    ["ntsc","ntsc2398", "pal", "ntsc-p","pal-p", "1800p2398", "1080p24", "1080p25", "1080p2997", "1080p30", "1080i50", "1080i5994", "1080i60", "1080p50", "1080p5994", "1080p60", "720p50", "720p5994","720p60"],
    ["30000/1001","24000/1001", "25/1", "30000/1001","25/1", "24000/1001", "24/1", "25/1", "30000/1001", "30/1", "25/1", "30000/1001", "30/1", "50/1", "60000/1001", "60/1", "50/1", "60000/1001","60/1"]
    ))


class GCblackmagic(Gst.Bin, base.Base):

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
      "description": "Opencast flavor associated to the track",
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
        "auto", "embedded", "aes","analog", "analog-xlr", "analog-rca", "none"
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
      "range": (1.0,10),
      "description": "Audio amplification",
      },
    "videoencoder": {
      "type": "text",
      "default": "x264enc quantizer=22 speed-preset=2",
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
    "videosink" : {
      "type": "select",
      "default": "xvimagesink",
      "options": ["xvimagesink", "ximagesink", "autovideosink", "fpsdisplaysink","fakesink"],
      "description": "Video sink",
    },
    "audiosink" : {
      "type": "select",
      "default": "alsasink",
      "options": ["autoaudiosink", "alsasink", "pulsesink", "fakesink"],
      "description": "Audio sink",
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
        Gst.Bin.__init__(self)

        pipestr = videostr

        if self.options['framerate'] == "auto":
          self.options['framerate'] = FRAMERATE[self.options["input-mode"]]

        gcvideosink = get_videosink(videosink=self.options['videosink'], name='sink-'+self.options['name'])
        gcaudiosink = get_audiosink(audiosink=self.options['audiosink'], name='sink-audio-'+self.options['name'])
        aux = (pipestr.replace('gc-vsink', gcvideosink)
               .replace('gc-blackmagic-enc', self.options['videoencoder'])
               .replace('gc-blackmagic-muxer', self.options['muxer']+" name=gc-blackmagic-muxer")
               .replace('gc-blackmagic-capsfilter', "video/x-raw,framerate={0}".format(self.options['framerate']))
               )

        if self.options["audio-input"] == "none":
          self.has_audio = False
        else:
          self.has_audio = True  
          aux += audiostr
          aux = aux.replace('gc-asink', gcaudiosink)
          aux = aux.replace('gc-blackmagic-audioenc', self.options['audioencoder'])

        #bin = Gst.parse_bin_from_description(aux, False)
        bin = Gst.parse_launch("( {} )".format(aux))
        self.add(bin)

        sink = self.get_by_name('gc-blackmagic-sink')
        sink.set_property('location', path.join(self.options['path'], self.options['file']))
        
        # Video properties
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

        try:
          subdevice = int(self.options['subdevice'])
        except ValueError:
          subdevice = self.options['subdevice']                                
        element.set_property('device-number', subdevice)

        # Video cropping
        for pos in ['right','left','top','bottom']:
            element = self.get_by_name('gc-blackmagic-crop')
            element.set_property(pos, int(self.options['videocrop-' + pos]))

        # Audio properties
        element_audio = self.get_by_name('gc-blackmagic-src')
        element_audio.set_property('device-number', subdevice)
        if self.has_audio:
          try:
            audio = int(self.options['audio-input'])
          except ValueError:
            audio = self.options['audio-input']                                
          element_audio.set_property('connection', audio)

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


  def changeValve(self, value):
    valve1=self.get_by_name('gc-blackmagic-valve')
    if self.has_audio:
      valve2=self.get_by_name('gc-blackmagic-audio-valve')
      valve2.set_property('drop', value)
    valve1.set_property('drop', value)

  def getVideoSink(self):
    return self.get_by_name('sink-' + self.options['name'])

  def getAudioSink(self):
    return self.get_by_name('sink-audio-' + self.options['name'])

  def getSource(self):
    return self.get_by_name('gc-blackmagic-src')

  def mute_preview(self, value):
    if not self.mute:
      element = self.get_by_name("gc-blackmagic-volume")
      element.set_property("mute", value)

  def send_event_to_src(self, event):
    src = self.get_by_name('gc-blackmagic-src')
    src.send_event(event)
    src2 = self.get_by_name('gc-blackmagic-audiosrc')
    if src2:
      src2.send_event(event)
    
