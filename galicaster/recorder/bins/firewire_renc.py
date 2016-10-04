# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/bins/firewire_renc
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

"""
Experimental bin to re-encode the dv video and audio with Galicaster on the fly.
"""

from os import path

from gi.repository import Gst

from galicaster.recorder import base
from galicaster.recorder.utils import get_videosink, get_audiosink

pipestr = (' dv1394src name=gc-firewire_renc-src ! queue ! '
           ' dvdemux name=gc-firewire_renc-demuxer ! '
           '    level name=gc-firewire_renc-level message=true interval=100000000 ! volume name=gc-firewire_renc-volumeinput !'
           '    tee name=gc-firewire_renc-audiotee ! '
           '       queue ! volume name=gc-firewire_renc-volume ! gc-asink '
           '    gc-firewire_renc-audiotee. ! queue ! valve drop=false name=gc-firewire_renc-audio-valve ! audio/x-raw ! '
           '       gc-firewire_renc-audioenc ! gc-firewire_renc-muxer ! '
           '       queue ! filesink name=gc-firewire_renc-sink async=false '
           ' gc-firewire_renc-demuxer. ! queue ! avdec_dvvideo ! videoconvert ! queue ! videobox name=gc-firewire_renc-videobox top=0 bottom=0 ! '
           '    tee name=gc-firewire_renc-videotee ! caps-preview ! gc-vsink '
           '    gc-firewire_renc-videotee. ! queue ! valve drop=false name=gc-firewire_renc-video-valve ! '
           '       videorate skip-to-first=true ! videoscale ! gc-firewire_renc-capsfilter ! gc-firewire_renc-videoenc ! gc-firewire_renc-mux. '
           )

class GCfirewire_renc(Gst.Bin, base.Base):
    gc_parameters = {
        "name": {
            "type": "text",
            "default": "Firewire_renc",
            "description": "Name assigned to the device",
            },
        "flavor": {
            "type": "flavor",
            "default": "presenter",
            "description": "Opencast flavor associated to the track",
            },
        "location": {
            "type": "device",
            "default": "/dev/fw1",
            "description": "Device's mount point of the firewire module",
            },

        "file": {
            "type": "text",
            "default": "CAMERA.avi",
            "description": "The file name where the track will be recorded.",
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
        "format" : {
            "type": "select",
            "default": "dv",
            "options": {
                "dv" : "dv1394src",
                "hdv" : "hdv1394src",
                "iidc" : "dc1394src",
                },
            "description": "Select video format",
            },
        "caps": {
            "type": "caps",
            "default": "video/x-raw,width=720,height=576,framerate=25/1",
            "description": "Forced capabilities",
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
        "Galicaster Firewire_renc BIN",
        "Generic/Video",
        "Add descripcion",
        "Teltek Video Research"
        )

    def __init__(self, options={}):
        base.Base.__init__(self, options)
        Gst.Bin.__init__(self)

        gcvideosink = get_videosink(videosink=self.options['videosink'], name='sink-'+self.options['name'])
        gcaudiosink = get_audiosink(audiosink=self.options['audiosink'], name='sink-audio-'+self.options['name'])
        aux = (pipestr.replace('gc-vsink', gcvideosink)
               .replace('gc-asink', gcaudiosink)
               .replace('gc-firewire_renc-videoenc', self.options['videoencoder'])
               .replace('gc-firewire_renc-muxer', self.options['muxer']+' name=gc-firewire_renc-mux')
               .replace('gc-firewire_renc-audioenc', self.options['audioencoder'])
               .replace('gc-firewire_renc-capsfilter', self.options['caps'])
              )

        if self.options["caps-preview"]:
            aux = aux.replace("caps-preview !","videoscale ! videorate ! "+self.options["caps-preview"]+" !")
        else:
            aux = aux.replace("caps-preview !","")

        #bin = Gst.parse_bin_from_description(aux, False)
        bin = Gst.parse_launch("( {} )".format(aux))

        self.add(bin)

        sink = self.get_by_name("gc-firewire_renc-sink")
        sink.set_property('location', path.join(self.options['path'], self.options['file']))

        if self.options["vumeter"] == False:
            level = self.get_by_name("gc-firewire_renc-level")
            level.set_property("message", False)

        if self.options["player"] == False:
            self.mute = True
            element = self.get_by_name("gc-firewire_renc-volume")
            element.set_property("mute", True)
        else:
            self.mute = False

    def changeValve(self, value):
        valve1=self.get_by_name('gc-firewire_renc-video-valve')
        valve2=self.get_by_name('gc-firewire_renc-audio-valve')
        valve1.set_property('drop', value)
        valve2.set_property('drop', value)

    def getVideoSink(self):
        return self.get_by_name('sink-' + self.options['name'])

    def getAudioSink(self):
        return self.get_by_name('sink-audio-' + self.options['name'])

    def getSource(self):
        return self.get_by_name("gc-firewire_renc-src")

    def send_event_to_src(self,event):
        src1 = self.get_by_name("gc-firewire_renc-src")
        src1.send_event(event)

    def mute_preview(self, value):
        if not self.mute:
            element = self.get_by_name("gc-firewire_renc-volume")
            element.set_property("mute", value)

    def configure(self):
        ##
        # v4l2-ctl -d self.options["location"] -s self.options["standard"]
        # v4l2-ctl -d self.options["location"] -i self.options["input"]
        pass

    def disable_input(self):
        src1 = self.get_by_name('gc-firewire_renc-videobox')
        src1.set_properties(top = -10000, bottom = 10000)
        element = self.get_by_name("gc-firewire_renc-volumeinput")
        element.set_property("mute", True)

    def enable_input(self):
        src1 = self.get_by_name('gc-firewire_renc-videobox')
        src1.set_property('top',0)
        src1.set_property('bottom',0)
        element = self.get_by_name("gc-firewire_renc-volumeinput")
        element.set_property("mute", False)

    def disable_preview(self):
        src1 = self.get_by_name('sink-'+self.options['name'])
        src1.set_property('saturation', -1000)
        src1.set_property('contrast', -1000)
        element = self.get_by_name("gc-firewire_renc-volume")
        element.set_property("mute", True)

    def enable_preview(self):
        src1 = self.get_by_name('sink-'+self.options['name'])
        src1.set_property('saturation',0)
        src1.set_property('contrast',0)
        element = self.get_by_name("gc-firewire_renc-volume")
        element.set_property("mute", False)
