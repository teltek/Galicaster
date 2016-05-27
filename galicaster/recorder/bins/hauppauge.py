# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/bins/hauppauge
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

from galicaster.recorder import base
from galicaster.recorder.utils import get_videosink, get_audiosink

pipestr = ( " filesrc name=gc-hauppauge-file-src ! valve drop=false name=gc-hauppauge-valve !  filesink  name=gc-hauppauge-sink async=false "
            " v4l2src name=gc-hauppauge-device-src ! video/x-raw,format=YV12,framerate=25/1,width=720,height=576,pixel-aspect-ratio=1/1 ! "
            " queue name=queue-hauprevideo ! videoconvert ! gc-vsink " 
            " filesrc name= gc-hauppauge-audio-src ! "
            " audio/x-raw, rate=48000, channels=2, endianness=1234, width=16, depth=16, signed=true ! queue ! "
            " level name=gc-hauppauge-level message=true interval=100000000 ! "
            " volume name=gc-hauppauge-volume ! gc-asink" )

class GChauppauge(Gst.Bin, base.Base):

    order = ["name","flavor","location","locprevideo","locpreaudio","file", 
             "vumeter", "player"]

    gc_parameters = {
        "name": {
            "type": "text",
            "default": "Hauppauge",
            "description": "Name assigned to the device",
            },
        "flavor": {
            "type": "flavor",
            "default": "presenter",
            "description": "Opencast flavor associated to the track",
            },
        "location": {
            "type": "device",
            "default": "/dev/haucamera",
            "description": "Device's mount point of the MPEG output",
            },
        "locprevideo": {
            "type": "device",
            "default": "/dev/hauprevideo",
            "description": " Device's mount point of the RAW output",
            },
        "locpreaudio": {
            "type": "device",
            "default": "/dev/haupreaudio",
            "description": "Device's mount point of the PCM output",
            },
        "file": {
            "type": "text",
            "default": "CAMERA.mpg",
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
        "input" : {
            "type": "select",
            "default": "Composite 3",
            "options": [ # use index for parameter
                "Tuner 1", "S-Video 1", "Composite 1", 
                "S-Video 2", "Composite 2", "Composite 3",
                ],
            "description": "Select video input",
            },
        "standard" : {
            "type": "select",
            "default": "PAL",
            "options": [
                "NTSC", "NTSC-M", "NTSC-M-JP", "NTSC-M-KR", "NTSC-443", 
                "PAL", "PAL-BG", "PAL-H", "PAL-I", "PAL-DK", "PAL-M", 
                "PAL-N", "PAL-Nc", "PAL-60", "SECAM", "SECAM-B", "SECAM-G", 
                "SECAM-H", "SECAM-DK", "SECAM-L", "SECAM-Lc"
                ],
            "description": "Select video standard",
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
    
    options = {
        "0": "NTSC", "1": "NTSC-M", "2": "NTSC-M-JP", "3": "NTSC-M-KR", 
        "4": "NTSC-443", "5": "PAL", "6": "PAL-BG", "7": "PAL-H", 
        "8": "PAL-I", "9": "PAL-DK", "10": "PAL-M", "11": "PAL-N", 
        "12": "PAL-Nc", "13": "PAL-60", "14": "SECAM", "15": "SECAM-B", 
        "16": "SECAM-G", "17": "SECAM-H", "18": "SECAM-DK", "19": "SECAM-L", 
        "20": "SECAM-Lc"
        }

    options2 = {
                "0": "Tuner 1", "1": "S-Video 1", "2": "Composite 1",
                "3": "S-Video 2", "4": "Composite 2", "5": "Composite 3",
                },

    is_pausable = False
    has_audio   = True
    has_video   = True
    
    __gstdetails__ = (
        "Galicaster Hauppauge BIN",
        "Generic/Video",
        "Add descripcion",
        "Teltek Video Research"
        )

    def __init__(self, options={}): 
        raise Exception("Not implemented. Using gst 0.10")

        base.Base.__init__(self, options)
        Gst.Bin.__init__(self)

        gcvideosink = get_videosink(videosink=self.options['videosink'], name='sink-'+self.options['name'])
        gcaudiosink = get_audiosink(audiosink=self.options['audiosink'], name='sink-audio-'+self.options['name'])
        aux = (pipestr.replace('gc-vsink', gcvideosink)
               .replace('gc-asink', gcaudiosink))

        #bin = Gst.parse_bin_from_description(aux, True)
        bin = Gst.parse_launch("( {} )".format(aux))
        self.add(bin)

        sink = self.get_by_name("gc-hauppauge-device-src")
        sink.set_property("device", self.options["locprevideo"])       

        sink = self.get_by_name("gc-hauppauge-file-src")
        sink.set_property("location", self.options["location"])


        sink = self.get_by_name("gc-hauppauge-audio-src") 
        sink.set_property("location", self.options["locpreaudio"])

        if self.options["player"] == False:
            self.mute = True
            element = self.get_by_name("gc-hauppauge-volume")
            element.set_property("mute", True)
        else:
            self.mute = False

        sink = self.get_by_name("gc-hauppauge-sink")
        sink.set_property('location', path.join(self.options['path'], self.options['file']))

        if self.options["vumeter"] == False:
            level = self.get_by_name("gc-hauppauge-level")
            level.set_property("message", False) 

    def changeValve(self, value):
        valve1=self.get_by_name('gc-hauppauge-valve')
        valve1.set_property('drop', value)

    def getVideoSink(self):
        return self.get_by_name('sink-' + self.options['name'])

    def getAudioSink(self):
        return self.get_by_name('sink-audio-' + self.options['name'])

    def getSource(self):
        return self.get_by_name("gc-hauppauge-file-src")
  
    def send_event_to_src(self,event): # IDEA made a common for all our bins
        src1 = self.get_by_name("gc-hauppauge-device-src")
        src2 = self.get_by_name("gc-hauppauge-file-src")
        src3 = self.get_by_name("gc-hauppauge-audio-src")
        src1.send_event(event)
        src2.send_event(event)
        src3.send_event(event)

    def mute_preview(self, value):
        if not self.mute:
            element = self.get_by_name("gc-hauppauge-volume")
            element.set_property("mute", value)

    def configure(self):
        ## 
        # v4l2-ctl -d self.options["location"] -s self.options["standard"]
        # v4l2-ctl -d self.options["location"] -i self.options["input"]
        pass
     

