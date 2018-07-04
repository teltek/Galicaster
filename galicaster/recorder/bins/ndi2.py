# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/bins/ndi
#
# Copyright (c) 2018, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

import re
from os import path

from gi.repository import Gst

from galicaster.recorder import base
from galicaster.recorder.utils import get_videosink, get_audiosink

videostr = (' ndivideosrc name=gc-ndi-src ! capsfilter name=gc-ndi-filter ! videobox name=gc-ndi-videobox top=0 bottom=0 ! videorate ! '
           ' tee name=gc-ndi-tee ! caps-preview ! gc-vsink '
           ' gc-ndi-tee. ! queue ! valve drop=false name=gc-ndi-valve ! videoconvert ! queue ! '
           ' gc-ndi-enc ! queue ! gc-ndi-mux ! '
           ' queue ! filesink name=gc-ndi-sink async=false')

audiostr = ( #AUDIO
            ' ndiaudiosrc name=gc-ndi-audiosrc ! queue ! '
            ' audiorate ! volume name=gc-ndi-volumeinput ! audioamplify name=gc-ndi-amplify amplification=1 ! '
            ' tee name=gc-ndi-audiotee ! queue ! '
            ' level name=gc-ndi-level message=true interval=100000000 ! '
            ' volume name=gc-ndi-volume ! queue ! gc-asink '
            # # REC AUDIO
            ' gc-ndi-audiotee. ! queue ! valve drop=false name=gc-ndi-audio-valve ! '
            ' decodebin ! audioconvert ! gc-ndi-audioenc ! queue ! gc-ndi-mux. '
)


class GCndi2(Gst.Bin, base.Base):


    order = ["name","flavor","location","file","caps",
             "videoencoder", "muxer", "caps-preview"]

    gc_parameters = {
        "name": {
            "type": "text",
            "default": "NDI",
            "description": "Name assigned to the device",
            },
        "flavor": {
            "type": "flavor",
            "default": "presenter",
            "description": "Opencast flavor associated to the track",
            },
        "location": {
            "type": "text",
            "default": None,
            "description": "NDI stream ip or name",
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
        "audio": {
            "type": "boolean",
            "default": "False",
            "description": "Activate NDI audio",
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
            "default": "x264enc pass=5 quantizer=22 speed-preset=4",
            "description": "Gstreamer encoder element used in the bin",
            },
        "audioencoder": {
            "type": "text",
            "default": "lamemp3enc target=1 bitrate=192 cbr=true",
            "description": "Gstreamer audio encoder element used in the bin",
        },
        "muxer": {
            "type": "text",
            "default": "avimux",
            "description": "Gstreamer encoder muxer used in the bin",
            },
        "videosink" : {
            "type": "select",
            "default": "xvimagesink",
            "options": ["xvimagesink", "ximagesink", "autovideosink", "fpsdisplaysink","fakesink"],
            "description": "Video sink",
        },
        "audiosink" : {
            "type": "select",
            "default": "pulsesink",
            "options": ["autoaudiosink", "alsasink", "pulsesink", "fakesink"],
            "description": "Audio sink",
        },
        "caps-preview" : {
            "type": "text",
            "default": None,
            "description": "Caps-preview",
        },

    }

    is_pausable = False
    has_audio   = True
    has_video   = True

    __gstdetails__ = (
        "Galicaster NDI Bin",
        "Generic/Video",
        "Generice bin to NDI interface devices",
        "Teltek Video Research",
        )

    def __init__(self, options={}):
        base.Base.__init__(self, options)
        Gst.Bin.__init__(self)

        pipestr = videostr

        gcvideosink = get_videosink(videosink=self.options['videosink'], name='sink-'+self.options['name'])
        gcaudiosink = get_audiosink(audiosink=self.options['audiosink'], name='sink-audio-'+self.options['name'])
        aux = (pipestr.replace('gc-vsink', gcvideosink)
               .replace('gc-ndi-enc', self.options['videoencoder'])
               .replace('gc-ndi-mux', self.options['muxer'] + " name=gc-ndi-mux"))


        # if 'image/jpeg' in self.options['caps']:
        #     aux = aux.replace('gc-ndi-dec !', 'jpegdec max-errors=-1 ! queue !')
        # else:
        #     aux = aux.replace('gc-ndi-dec !', '')

        if  self.options["audio"]:
            self.has_audio = True
            aux += audiostr
            aux = aux.replace('gc-asink', gcaudiosink)
            aux = aux.replace('gc-ndi-audioenc', self.options['audioencoder'])

        else:
            self.has_audio = False

        if self.options["caps-preview"]:
            aux = aux.replace("caps-preview !","videoscale ! videorate ! "+self.options["caps-preview"]+" !")
        else:
            aux = aux.replace("caps-preview !","")

        # aux = (' ndivideosrc stream-name="GC-DEV2 (OBS)" ! capsfilter name=gc-ndi-filter ! videobox name=gc-ndi-videobox top=0 bottom=0 ! videorate !  tee name=gc-ndi-tee !  xvimagesink name=sink-Webcam async=false qos=true force-aspect-ratio=true gc-ndi-tee. ! queue ! valve drop=false name=gc-ndi-valve ! videoconvert ! x264enc pass=5 quantizer=22 speed-preset=4 ! queue ! avimux name=gc-ndi-mux ! queue ! filesink location=/tmp/test.avi async=false ndiaudiosrc ! queue  ! decodebin ! audiorate ! volume name=gc-ndi-volumeinput ! audioamplify name=gc-ndi-amplify amplification=1 !  tee name=gc-ndi-audiotee ! queue ! level name=gc-ndi-level message=true interval=100000000 !  volume name=gc-ndi-volume ! queue ! autoaudiosink async=false qos=true gc-ndi-audiotee. ! queue ! valve drop=false name=gc-ndi-audio-valve !  decodebin ! audioconvert ! lamemp3enc target=1 bitrate=192 cbr=true ! queue ! gc-ndi-mux.')

        print aux
        #bin = Gst.parse_bin_from_description(aux, True)
        bin = Gst.parse_launch("( {} )".format(aux))
        self.add(bin)

        test_ip = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]):[0-9]+$")
        if self.options['location']:
            if test_ip.match(self.options['location']):
                self.set_option_in_pipeline('location', 'gc-ndi-src', 'ip')
                self.set_option_in_pipeline('location', 'gc-ndi-audiosrc', 'ip')
            else:
                self.set_option_in_pipeline('location', 'gc-ndi-src', 'stream-name')
                self.set_option_in_pipeline('location', 'gc-ndi-audiosrc', 'stream-name')

        self.set_value_in_pipeline(path.join(self.options['path'], self.options['file']), 'gc-ndi-sink', 'location')

        # self.set_option_in_pipeline('caps', 'gc-ndi-filter', 'caps', None)

        # Audio properties
        if self.has_audio:
          if "player" in self.options and self.options["player"] == False:
            self.mute = True
            element = self.get_by_name("gc-ndi-volume")
            element.set_property("mute", True)
          else:
            self.mute = False

          if "vumeter" in self.options:
            level = self.get_by_name("gc-ndi-level")
            if self.options["vumeter"] == False:
              level.set_property("message", False)

          if "amplification" in self.options:
            ampli = self.get_by_name("gc-ndi-amplify")
            ampli.set_property("amplification", float(self.options["amplification"]))


    def changeValve(self, value):
        valve1=self.get_by_name('gc-ndi-valve')
        if self.has_audio:
            valve2=self.get_by_name('gc-ndi-audio-valve')
            valve2.set_property('drop', value)
        valve1.set_property('drop', value)

    def getVideoSink(self):
        return self.get_by_name('sink-' + self.options['name'])

    def getAudioSink(self):
        return self.get_by_name('sink-audio-' + self.options['name'])

    def getSource(self):
        return self.get_by_name('gc-ndi-src')

    def mute_preview(self, value):
        if not self.mute:
            element = self.get_by_name("gc-ndi-volume")
            element.set_property("mute", value)
        pass

    def send_event_to_src(self, event):
        src1 = self.get_by_name('gc-ndi-src')
        src1.send_event(event)
        src2 = self.get_by_name('gc-ndi-audiosrc')
        if src2:
            src2.send_event(event)


    def disable_input(self):
        src1 = self.get_by_name('gc-ndi-videobox')
        src1.set_properties(top = -10000, bottom = 10000)
        if self.has_audio:
            element = self.get_by_name("gc-ndi-volumeinput")
            element.set_property("mute", True)

    def enable_input(self):
        src1 = self.get_by_name('gc-ndi-videobox')
        src1.set_property('top',0)
        src1.set_property('bottom',0)
        if self.has_audio:
            element = self.get_by_name("gc-ndi-volumeinput")
            element.set_property("mute", False)

    def disable_preview(self):
        src1 = self.get_by_name('sink-'+self.options['name'])
        src1.set_property('saturation', -1000)
        src1.set_property('contrast', -1000)
        if self.has_audio:
            element = self.get_by_name("gc-ndi-volume")
            element.set_property("mute", True)

    def enable_preview(self):
        src1 = self.get_by_name('sink-'+self.options['name'])
        src1.set_property('saturation',0)
        src1.set_property('contrast',0)
        if self.has_audio:
            element = self.get_by_name("gc-ndi-volume")
            element.set_property("mute", False)
