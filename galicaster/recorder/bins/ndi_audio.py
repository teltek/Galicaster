# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/bins/ndi_audio
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
from galicaster.recorder.utils import get_audiosink

pipestr = (' ndiaudiosrc name=gc-audio-src ! queue ! '
           ' audiorate ! volume name=gc-audio-volumemaster ! audioamplify name=gc-audio-amplify amplification=1 ! decodebin async-handling=true ! '
           ' tee name=tee-aud  ! queue ! '
           ' level name=gc-audio-level message=true interval=100000000 ! '
           ' volume name=gc-audio-volume-prev ! volume name=gc-audio-volume ! queue ! gc-asink '
           ' tee-aud. ! queue ! valve drop=false name=gc-audio-valve ! '
           ' audioconvert ! gc-audio-enc ! '
           ' queue ! filesink name=gc-audio-sink async=false ' )


class GCndi_audio(Gst.Bin, base.Base):

    order = ["name", "flavor", "location", "file",
             "vumeter", "player", "amplification", "audioencoder"]

    gc_parameters = {
        "name": {
            "type": "text",
            "default": "NDI_Audio",
            "description": "Name assigned to the device",
            },
        "flavor": {
            "type": "flavor",
            "default": "presenter",
            "description": "Opencast flavor associated to the track",
            },
        "location": {
            "type": "device",
            "default": None,
            "description": "NDI stream ip or name",
            },
        "file": {
            "type": "text",
            "default": "sound.mp3",
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
        "amplification": {
            "type": "float",
            "default": 1.0,
            "range": (1.0,10),
            "description": "Audio amplification",
            },
        "audioencoder": {
            "type": "text",
            "default": "lamemp3enc target=1 bitrate=192 cbr=true",
            "description": "Gstreamer audio encoder element used in the bin",
            },
        "audiosink" : {
            "type": "select",
            "default": "pulsesink",
            "options": ["autoaudiosink", "alsasink", "pulsesink", "fakesink"],
            "description": "Audio sink",
        },
    }

    is_pausable = False
    has_audio   = True
    has_video   = False

    __gstdetails__ = (
        "Galicaster NDI Audio bin",
        "Generic/Audio",
        "Generic bin to NDI Audio devices",
        "Teltek Video Research"
        )

    def __init__(self, options={}):
        base.Base.__init__(self, options)
        Gst.Bin.__init__(self)

        gcaudiosink = get_audiosink(audiosink=self.options['audiosink'], name='sink-'+self.options['name'])
        aux = (pipestr.replace('gc-asink', gcaudiosink)
               .replace("gc-audio-enc", self.options["audioencoder"])
        )

        bin = Gst.parse_launch("( {} )".format(aux))
        self.add(bin)

        test_ip = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]):[0-9]+$")
        if self.options['location']:
            if test_ip.match(self.options['location']):
                self.set_option_in_pipeline('location', 'gc-audio-src', 'ip')
            else:
                self.set_option_in_pipeline('location', 'gc-audio-src', 'stream-name')


        sink = self.get_by_name("gc-audio-sink")
        sink.set_property('location', path.join(self.options['path'], self.options['file']))

        if "player" in self.options and self.options["player"] == False:
            self.mute = True
            element = self.get_by_name("gc-audio-volumemaster")
            element.set_property("mute", True)
        else:
            self.mute = False

        if "vumeter" in self.options:
            level = self.get_by_name("gc-audio-level")
            if self.options["vumeter"] == False:
                level.set_property("message", False)
        if "amplification" in self.options:
            ampli = self.get_by_name("gc-audio-amplify")
            ampli.set_property("amplification", float(self.options["amplification"]))

    def changeValve(self, value):
        valve1=self.get_by_name('gc-audio-valve')
        valve1.set_property('drop', value)

    def getVideoSink(self):
        return None

    def getAudioSink(self):
        return self.get_by_name('sink-' + self.options['name'])

    def getSource(self):
        return self.get_by_name("gc-audio-src")

    def send_event_to_src(self, event):
        src1 = self.get_by_name("gc-audio-src")
        src1.send_event(event)

    def mute_preview(self, value):
        if not self.mute:
            element = self.get_by_name("gc-audio-volume-prev")
            element.set_property("mute", value)

    def disable_input(self):
        element = self.get_by_name("gc-audio-volumemaster")
        element.set_property("mute", True)

    def enable_input(self):
        element = self.get_by_name("gc-audio-volumemaster")
        element.set_property("mute", False)

    def disable_preview(self):
        element = self.get_by_name("gc-audio-volume")
        element.set_property("mute", True)

    def enable_preview(self):
        element = self.get_by_name("gc-audio-volume")
        element.set_property("mute", False)
