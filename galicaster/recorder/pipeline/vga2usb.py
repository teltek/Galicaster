# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/pipeline/vga2usb
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import logging

import gobject
import gst
from os import path
import galicaster

from galicaster.recorder.utils import Switcher


log = logging.getLogger()

  

pipestr = (" identity name=\"joint\" ! tee name=gc-vga2usb-tee ! "
           " queue !  videorate silent=true ! video/x-raw-yuv,framerate=25/1 ! "
           " videoscale add-borders=true ! video/x-raw-yuv,width=800,height=600 ! "
           " ffmpegcolorspace ! valve name=gc-vga2usb-valve drop=false ! "
           " queue ! xvidenc bitrate=5000000 ! avimux name=mux2 ! "
           #" x264enc pass=5 quantizer=22 speed-preset=4 profile=1 ! queue ! avimux ! "
           " queue ! filesink name=gc-vga2usb-sink async=false "
           " gc-vga2usb-tee. ! "
           " queue ! ffmpegcolorspace ! identity single-segment=true ! "
           " xvimagesink qos=false async=false sync=false name=gc-vga2usb-preview " )

class GCvga2usb(gst.Bin):

    gc_parameters = {
        'drivertype': 'v4l2 or v4l to epiphan driver',
        'background': 'Not implemented yet'
        }
    
    is_pausable = True

    __gstdetails__ = (
        "Galicaster Epiphan VGA2USB BIN",
        "Generic/Video",
        "Add descripcion",
        "Teltek Video Research"
        )

    def __init__(self, name = None, devicesrc = None, filesink = None, options = {}): 
        # FIXME take out background        
        if not path.exists(devicesrc):
            raise SystemError('Device error in vga2usb bin: path %s not exists' % (devicesrc,) )

        if name == None:
            name = "vga2usb"

        gst.Bin.__init__(self, name)

        # FIXME check route in conf/recorderui and define options
        if "background" not in options:
            background= (path.join(path.dirname(path.abspath(galicaster.__file__)), "..", "resources", "bg.png") )
        else:
            background = (path.join(path.dirname(path.abspath(galicaster.__file__)), "..", options["background"]))

        if "drivertype" not in options or options["drivertype"] == "v4l":
            driver_type = "v4lsrc"
        else:
            driver_type = "v4l2src"

        bin_end = gst.parse_bin_from_description(pipestr.replace("gc-vga2usb-preview", "sink-" + name), True)
        log.info("Setting background for Epiphan: %s", background)
        bin_start = Switcher("canguro", devicesrc, background, driver_type)
        self.bin_start=bin_start            

        self.add(bin_start, bin_end)
        bin_start.link(bin_end)

        if filesink != None:
            sink = self.get_by_name("gc-vga2usb-sink")
            sink.set_property("location", filesink)


    def getValve(self):
        return self.get_by_name("gc-vga2usb-valve")

    def getVideoSink(self):
        return self.get_by_name("gc-vga2usb-preview")

    def send_event_to_src(self,event): # IDEA made a common for all our bins
        self.bin_start.send_event_to_src(event)

    def switch(self): # IDEA made a common for all our bins
        self.bin_start.switch2()
        
        

gobject.type_register(GCvga2usb)
gst.element_register(GCvga2usb, "gc-vga2usb-bin")
