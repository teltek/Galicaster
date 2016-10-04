# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/bins/epiphan
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

# from os import path
# import re

# from gi.repository import Gst

# import galicaster
from galicaster.core import context
# from galicaster.recorder.utils import Switcher
# from galicaster.recorder import base
# from galicaster.recorder.utils import get_videosink

from galicaster.recorder.bins import v4l2

logger = context.get_logger()

pipestr = (" identity name=\"joint\" ! tee name=gc-epiphan-tee ! queue ! "
           " videoconvert ! valve name=gc-epiphan-valve drop=false ! "
           " gc-epiphan-enc ! queue ! gc-epiphan-mux ! "
           " queue ! filesink name=gc-epiphan-sink async=false "
           " gc-epiphan-tee. ! queue ! videoconvert ! identity single-segment=true ! "
           " gc-vsink " )

class GCepiphan(v4l2.GCv4l2):

    order = ["name","flavor","location","file",
             "videoencoder", "muxer", "resolution", "framerate"]

    gc_parameters = {
        "name": {
            "type": "text",
            "default": "Epiphan",
            "description": "Name assigned to the device",
            },
        "flavor": {
            "type": "flavor",
            "default": "presentation",
            "description": "Opencast flavor associated to the track",
            },
        "location": {
            "type": "device",
            "default": "/dev/screen",
            "description": "Device's mount point of the output",
            },
        "file": {
            "type": "text",
            "default": "SCREEN.avi",
            "description": "The file name where the track will be recorded.",
            },
        "drivertype": {
            "type": "select",
            "default": "v4l2",
            "options": [
                "v4l", "v4l2"
                ],
            "description": "v4l2 or v4l to epiphan driver",
            },
        "background": {
            "type": "text",
            "default": "",
            "description": "Not implemented yet",
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
        "resolution": {
            "type": "text",
            "default": "1024,768",
            "description": "Output resolution",
            },
        "framerate": {
            "type": "text",
            "default": "25/1",
            "description": " Output framerate",
            },
        "videosink" : {
            "type": "select",
            "default": "xvimagesink",
            "options": ["xvimagesink", "ximagesink", "autovideosink", "fpsdisplaysink","fakesink"],
            "description": "Video sink",
        },
    }

    is_pausable = True
    has_audio   = False
    has_video   = True

    __gstdetails__ = (
        "Galicaster Epiphan EPIPHAN BIN",
        "Generic/Video",
        "Add descripcion",
        "Teltek Video Research"
        )

    def __init__(self, options={}):
        logger.warning("Epiphan module not implemented, using v4l2")
        v4l2.GCv4l2.__init__(self, options)

    #     raise Exception("Not implemented. Using gst 0.10")

    #     base.Base.__init__(self, options)
    #     Gst.Bin.__init__(self)

    #     # FIXME check route in conf/recorderui and define options
    #     if "background" not in self.options:
    #         background= (path.join(path.dirname(path.abspath(galicaster.__file__)), "..", "resources", "bg.png") )
    #     else:
    #         background = (path.join(path.dirname(path.abspath(galicaster.__file__)), "..", self.options["background"]))

    #     if self.options["drivertype"] == "v4l":
    #         driver_type = "v4lsrc"
    #     else:
    #         driver_type = "v4l2src"

    #     gcvideosink = get_videosink(videosink=self.options['videosink'], name='sink-'+self.options['name'])
    #     aux = (pipestr.replace('gc-vsink', gcvideosink)
    #                   .replace('gc-epiphan-enc', self.options['videoencoder'])
    #                   .replace('gc-epiphan-mux', self.options['muxer']))
    #     size = self.options['resolution']
    #     width, height =  [int(a) for a in size.split(re.search('[,x:]',size).group())]
    #     bin_end = Gst.parse_bin_from_description(aux, True)
    #     logger.info("Setting background for Epiphan: %s", background)
    #     bin_start = Switcher("canguro", self.options['location'], background,
    #                          driver_type, [width,height], self.options['framerate'])
    #     self.bin_start=bin_start
    #     self.add(bin_start, bin_end)
    #     bin_start.link(bin_end)

    #     sink = self.get_by_name("gc-epiphan-sink")
    #     sink.set_property('location', path.join(self.options['path'], self.options['file']))

    # def changeValve(self, value):
    #     valve1=self.get_by_name('gc-epiphan-valve')
    #     valve1.set_property('drop', value)

    # def getVideoSink(self):
    #     return self.get_by_name('sink-' + self.options['name'])

    # def getSource(self):
    #     return self.get_by_name("gc-epiphan-tee")

    # def send_event_to_src(self,event):
    #     self.bin_start.send_event_to_src(event)

    # def switch(self):
    #     self.bin_start.switch2()
