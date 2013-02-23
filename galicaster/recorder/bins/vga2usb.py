# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/bins/vga2usb
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
from os import path
import galicaster

from galicaster.core import context
from galicaster.recorder.utils import Switcher
from galicaster.recorder import base
from galicaster.recorder import module_register

logger = context.get_logger()

pipestr = (" identity name=\"joint\" ! tee name=gc-vga2usb-tee ! "
           " queue !  videorate silent=true ! video/x-raw-yuv,framerate=25/1 ! "
           " videoscale add-borders=true ! video/x-raw-yuv,width=800,height=600 ! "
           " ffmpegcolorspace ! valve name=gc-vga2usb-valve drop=false ! queue ! "
           " gc-vga2usb-enc ! queue ! gc-vga2usb-mux ! "
           " queue ! filesink name=gc-vga2usb-sink async=false "
           " gc-vga2usb-tee. ! queue ! ffmpegcolorspace ! identity single-segment=true ! "
           " xvimagesink qos=false async=false sync=false name=gc-vga2usb-preview " )

class GCvga2usb(gst.Bin, base.Base):

    order = ["name","flavor","location","file","drivertype",
             "encoder", "muxer"]

    gc_parameters = {
        "name": {
            "type": "text",
            "default": "Epiphan",
            "description": "Name assigned to the device",
            },
        "flavor": {
            "type": "flavor",
            "default": "presentation",
            "description": "Matterhorn flavor associated to the track",
            },
        "location": {
            "type": "device",
            "default": "/dev/screen",
            "description": "Device's mount point of the MPEG output",
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
        "encoder": {
            "type": "text",
            "default": "xvidenc bitrate=5000000",
            #Other examples: "x264enc pass=5 quantizer=22 speed-preset=4 profile=1"
            "description": "Gstreamer encoder element used in the bin",
            },
        "muxer": {
            "type": "text",
            "default": "avimux",
            "description": "Gstreamer encoder muxer used in the bin",
            },
        }
    
    is_pausable = True
    has_audio   = False
    has_video   = True

    __gstdetails__ = (
        "Galicaster Epiphan VGA2USB BIN",
        "Generic/Video",
        "Add descripcion",
        "Teltek Video Research"
        )

    def __init__(self, options={}): 
        base.Base.__init__(self, options)
        gst.Bin.__init__(self, self.options['name'])

        # FIXME check route in conf/recorderui and define options
        if "background" not in self.options:
            background= (path.join(path.dirname(path.abspath(galicaster.__file__)), "..", "resources", "bg.png") )
        else:
            background = (path.join(path.dirname(path.abspath(galicaster.__file__)), "..", self.options["background"]))

        if self.options["drivertype"] == "v4l":
            driver_type = "v4lsrc"
        else:
            driver_type = "v4l2src"

        aux = (pipestr.replace("gc-vga2usb-preview", "sink-" + self.options['name'])
                      .replace('gc-vga2usb-enc', self.options['encoder'])
                      .replace('gc-vga2usb-mux', self.options['muxer']))


        bin_end = gst.parse_bin_from_description(aux, True)
        logger.info("Setting background for Epiphan: %s", background)
        bin_start = Switcher("canguro", self.options['location'], background, driver_type)
        self.bin_start=bin_start            

        self.add(bin_start, bin_end)
        bin_start.link(bin_end)

        sink = self.get_by_name("gc-vga2usb-sink")
        sink.set_property('location', path.join(self.options['path'], self.options['file']))

    def changeValve(self, value):
        valve1=self.get_by_name('gc-vga2usb-valve')
        valve1.set_property('drop', value)

    def getVideoSink(self):
        return self.get_by_name("gc-vga2usb-preview")

    def getSource(self):
        return self.get_by_name("gc-vga2usb-tee")

    def send_event_to_src(self,event): # IDEA made a common for all our bins
        self.bin_start.send_event_to_src(event)

    def switch(self): # IDEA made a common for all our bins
        self.bin_start.switch2()
        
        

gobject.type_register(GCvga2usb)
gst.element_register(GCvga2usb, "gc-vga2usb-bin")
module_register(GCvga2usb, 'vga2usb')
