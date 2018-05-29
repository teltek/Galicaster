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

from os import path

from gi.repository import Gst

from galicaster.recorder import base
from galicaster.recorder.utils import get_videosink

pipestr = (' ndisrc name=gc-ndi-src ! capsfilter name=gc-ndi-filter ! videobox name=gc-ndi-videobox top=0 bottom=0 ! '
           ' tee name=gc-ndi-tee ! caps-preview ! gc-vsink '
           ' gc-ndi-tee. ! queue ! valve drop=false name=gc-ndi-valve ! videoconvert ! queue ! '
           ' gc-ndi-enc ! queue ! gc-ndi-mux ! '
           ' queue ! filesink name=gc-ndi-sink async=false')

class GCndi(Gst.Bin, base.Base):


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
            "description": "NDI stream name",
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

    is_pausable = False
    has_audio   = False
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

        gcvideosink = get_videosink(videosink=self.options['videosink'], name='sink-'+self.options['name'])

        aux = (pipestr.replace('gc-vsink', gcvideosink)
               .replace('gc-ndi-enc', self.options['videoencoder'])
               .replace('gc-ndi-mux', self.options['muxer']))


        # if 'image/jpeg' in self.options['caps']:
        #     aux = aux.replace('gc-ndi-dec !', 'jpegdec max-errors=-1 ! queue !')
        # else:
        #     aux = aux.replace('gc-ndi-dec !', '')

        if self.options["caps-preview"]:
            aux = aux.replace("caps-preview !","videoscale ! videorate ! "+self.options["caps-preview"]+" !")
        else:
            aux = aux.replace("caps-preview !","")


        #bin = Gst.parse_bin_from_description(aux, True)
        bin = Gst.parse_launch("( {} )".format(aux))
        self.add(bin)

        if self.options['location']:
            self.set_option_in_pipeline('location', 'gc-ndi-src', 'stream-name')

        self.set_value_in_pipeline(path.join(self.options['path'], self.options['file']), 'gc-ndi-sink', 'location')

        self.set_option_in_pipeline('caps', 'gc-ndi-filter', 'caps', None)

    def changeValve(self, value):
        valve1=self.get_by_name('gc-ndi-valve')
        valve1.set_property('drop', value)

    def getVideoSink(self):
        return self.get_by_name('sink-' + self.options['name'])

    def getSource(self):
        return self.get_by_name('gc-ndi-src')

    def send_event_to_src(self, event):
        src1 = self.get_by_name('gc-ndi-src')
        src1.send_event(event)

    def disable_input(self):
        src1 = self.get_by_name('gc-ndi-videobox')
        src1.set_properties(top = -10000, bottom = 10000)

    def enable_input(self):
        src1 = self.get_by_name('gc-ndi-videobox')
        src1.set_property('top',0)
        src1.set_property('bottom',0)

    def disable_preview(self):
        src1 = self.get_by_name('sink-'+self.options['name'])
        src1.set_property('saturation', -1000)
        src1.set_property('contrast', -1000)

    def enable_preview(self):
        src1 = self.get_by_name('sink-'+self.options['name'])
        src1.set_property('saturation',0)
        src1.set_property('contrast',0)
