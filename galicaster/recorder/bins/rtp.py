# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/bins/rtp
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

from gi.repository import Gst

from os import path

from galicaster.recorder import base
from galicaster.recorder.utils import get_videosink, get_audiosink

pipe_config = {'mpeg4':
                   {'depay': 'rtpmp4vdepay', 'parse': 'mpeg4videoparse', 'dec': 'avdec_mpeg4'},
               'h264':
                   {'depay': 'rtph264depay', 'parse': 'h264parse', 'dec': 'avdec_h264'}} 

pipe_config_audio = {'mp3':
                         {'depay': 'rtpmpadepay', 'parse': 'mpegaudioparse', 'dec': 'flump3dec'},
                     'aac':
                         {'depay': 'rtpmp4gdepay', 'parse': 'aacparse', 'dec': 'faad'}}

pipestr = (' rtspsrc name=gc-rtp-src ! gc-rtp-depay ! gc-rtp-videoparse ! queue !'
           ' tee name=gc-rtp-tee  ! queue ! gc-rtp-dec  ! gc-vsink '
           ' gc-rtp-tee. ! queue ! valve drop=false name=gc-rtp-valve ! '
           ' queue ! gc-rtp-muxer name=gc-rtp-mux ! queue ! filesink name=gc-rtp-sink async=false')

audiostr = (' gc-rtp-src. ! gc-rtp-audio-depay ! gc-rtp-audioparse ! queue !'
           ' tee name=gc-rtp-audio-tee ! queue ! valve drop=false name=gc-rtp-audio-valve ! '
           ' queue ! gc-rtp-mux. '
           ' gc-rtp-audio-tee. ! queue ! gc-rtp-audio-dec ! '
           ' level name=gc-rtp-level message=true interval=100000000 ! '
           ' volume name=gc-rtp-volume ! gc-asink ')
 


class GCrtp(Gst.Bin, base.Base):


    order = ["name", "flavor", "location", "file", "muxer", 
             "cameratype", "audio", "audiotype", "vumeter", "player"]
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
        "file": {
            "type": "text",
            "default": "CAMERA.avi",
            "description": "The file name where the track will be recorded.",
            },
        "muxer": {
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
            "description": "RTP Camera encoding type",
            },
        "audio": {
            "type": "boolean",
            "default": "False",
            "description": "Activate RTP audio",
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
        "audiotype": {
            "type": "select",
            "default": "mp3",
            "options": [
                "mp3", "aac"
                ],
            "description": "RTP Audio encoding type",
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
    
    is_pausable = False
    has_audio   = True
    has_video   = True

    __gstdetails__ = (
        "Galicaster RTP Bin",
        "Generic/Video",
        "Generice bin to rtp interface devices",
        "Teltek Video Research",
        )

    def __init__(self, options={}):
        base.Base.__init__(self, options)
        Gst.Bin.__init__(self)

        gcvideosink = get_videosink(videosink=self.options['videosink'], name='sink-'+self.options['name'])
        gcaudiosink = get_audiosink(audiosink=self.options['audiosink'], name='sink-audio-'+self.options['name'])
        aux = (pipestr.replace('gc-vsink', gcvideosink)
               .replace('gc-rtp-depay', pipe_config[self.options['cameratype']]['depay'])
               .replace('gc-rtp-videoparse', pipe_config[self.options['cameratype']]['parse'])
               .replace('gc-rtp-dec', pipe_config[self.options['cameratype']]['dec'])
               .replace('gc-rtp-muxer', self.options['muxer']))

        if self.options["audio"]:
            self.has_audio = True
            aux += (audiostr.replace("gc-rtp-audio-depay", pipe_config_audio[self.options['audiotype']]['depay'])
                    .replace('gc-asink', gcaudiosink)
                    .replace("gc-rtp-audioparse", pipe_config_audio[self.options['audiotype']]['parse'])
                    .replace("gc-rtp-audio-dec", pipe_config_audio[self.options['audiotype']]['dec']))
        else:
            self.has_audio = False

        bin = Gst.parse_launch("( {} )".format(aux))
        self.add(bin)

        self.set_option_in_pipeline('location', 'gc-rtp-src', 'location')
        self.set_value_in_pipeline(path.join(self.options['path'], self.options['file']), 'gc-rtp-sink', 'location')
        if self.has_audio:
          if "player" in self.options and self.options["player"] == False:
            self.mute = True
            element = self.get_by_name("gc-rtp-volume")
            element.set_property("mute", True)
          else:
            self.mute = False

          if "vumeter" in self.options:
            level = self.get_by_name("gc-rtp-level")
            if self.options["vumeter"] == False:
              level.set_property("message", False)


    def changeValve(self, value):
        valve1=self.get_by_name('gc-rtp-valve')
        if self.has_audio:
            valve2=self.get_by_name('gc-rtp-audio-valve')
            valve2.set_property('drop', value)
        valve1.set_property('drop', value)

    def getVideoSink(self):
        return self.get_by_name('sink-' + self.options['name'])

    def getAudioSink(self):
        return self.get_by_name('sink-audio-'+self.options['name'])

    def getSource(self):
        return self.get_by_name('gc-rtp-src') 

    def mute_preview(self, value):
        if not self.mute:
            element = self.get_by_name("gc-rtp-volume")
            element.set_property("mute", value)

    def send_event_to_src(self, event):
        src1 = self.get_by_name('gc-rtp-src')
        src1.send_event(event)

