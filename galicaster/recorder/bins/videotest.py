# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/bins/videotest
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

# import re
from os import path

from gi.repository import GObject, Gst

from galicaster.recorder import base
from galicaster.recorder.utils import get_videosink

pipestr = (' videotestsrc name=gc-videotest-src pattern=0 is-live=true ! capsfilter name=gc-videotest-filter ! videobox name=gc-videotest-videobox top=0 bottom=0 !'
           ' queue ! videoconvert ! video/x-raw,format=YUY2 ! tee name=tee-vt  ! '
           ' queue ! caps-preview ! gc-vsink '
           ' tee-vt. ! queue ! valve drop=false name=gc-videotest-valve ! videoconvert ! queue ! '
           ' gc-videotest-enc ! queue ! gc-videotest-mux ! '
           ' queue ! filesink name=gc-videotest-sink async=false')


class GCvideotest(Gst.Bin, base.Base):

    order = ["name","flavor","location","file","caps",
             "pattern","color1","color2", "videoencoder", "muxer", "caps-preview"
             ]

    gc_parameters = {
        "name": {
            "type": "text",
            "default": "VideoTest",
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
            "type": "text",
            "default": "video/x-raw,framerate=10/1,width=640,height=480",
            "description": "Forced capabilities",
            },
        "pattern": {
            "type": "integer",
            "default": 0,
            "range": (0,20),
            "description": "Background pattern",
            },
        "color1": {
            "type": "integer",
            "default": 4294967295,
            "range": (0,4294967495),
            "description": "Foreground color on some patterns, big-endian ARGB",
            },
        "color2": {
            "type": "integer",
            "default": 4278190080,
            "range": (0,4294967495),
            "description": "Background color on some patterns",
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
        "videosink" : {
            "type": "select",
            "default": "xvimagesink",
            "options": ["xvimagesink", "ximagesink", "autovideosink", "fpsdisplaysink","fakesink"],
            "description": "Video sink",
        },
        "caps-preview" : {
            "type": "text",
            "default": None,
            "description": "Caps-preview",
        },

    }

    is_pausable = True
    has_audio   = False
    has_video   = True

    __gstdetails__ = (
        "Galicaster Video Test Bin",
        "Generic/Video",
        "Videotest bin to use self-made patterns",
        "Teltek Video Research",
        )


    def __init__(self, options={}):
        base.Base.__init__(self, options)
        Gst.Bin.__init__(self)

        gcvideosink = get_videosink(videosink=self.options['videosink'], name='sink-'+self.options['name'])
        aux = (pipestr.replace('gc-vsink', gcvideosink)
                      .replace('gc-videotest-enc', self.options['videoencoder'])
                      .replace('gc-videotest-mux', self.options['muxer']))

        if self.options["caps-preview"]:
            aux = aux.replace("caps-preview !","videoscale ! videorate ! "+self.options["caps-preview"]+" !")
        else:
            aux = aux.replace("caps-preview !","")


        #bin = Gst.parse_bin_from_description(aux, False)
        bin = Gst.parse_launch("( {} )".format(aux))
        self.add(bin)

        self.get_by_name('gc-videotest-sink').set_property('location', path.join(self.options['path'], self.options['file']))

        #self.get_by_name('gc-videotest-filter').set_property('caps', Gst.Caps(self.options['caps']))
        #fr = re.findall("framerate *= *[0-9]+/[0-9]+", self.options['caps'])
        #if fr:
        #    newcaps = 'video/x-raw,' + fr[0]
            #self.get_by_name('gc-videotest-vrate').set_property('caps', Gst.Caps(newcaps))

        source = self.get_by_name('gc-videotest-src')
        source.set_property('pattern', int(self.options['pattern']))
        coloured = False
        for properties in GObject.list_properties(source):
            if properties.name == 'foreground-color':
                coloured = True

        if self.options["color1"] and coloured:
            source.set_property('foreground-color', int(self.options['color1']))
        #if self.options["color2"]:
        #    source.set_property('background-color', int(self.options['color2']))

    def changeValve(self, value):
        valve1=self.get_by_name('gc-videotest-valve')
        valve1.set_property('drop', value)

    def getVideoSink(self):
        return self.get_by_name('sink-' + self.options['name'])

    def getSource(self):
        return self.get_by_name('gc-videotest-src')

    def send_event_to_src(self, event):
        src1 = self.get_by_name('gc-videotest-src')
        src1.send_event(event)

    def disable_input(self):
        src1 = self.get_by_name('gc-videotest-videobox')
        src1.set_properties(top = -10000, bottom = 10000)

    def enable_input(self):
        src1 = self.get_by_name('gc-videotest-videobox')
        src1.set_property('top',0)
        src1.set_property('bottom',0)

    def disable_preview(self):
        src1 = self.get_by_name('sink-'+self.options['name'])
        print src1
        src1.set_property('saturation', -1000)
        src1.set_property('contrast', -1000)

    def enable_preview(self):
        src1 = self.get_by_name('sink-'+self.options['name'])
        src1.set_property('saturation',0)
        src1.set_property('contrast',0)
