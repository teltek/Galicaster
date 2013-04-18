# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/bins/custom
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
import re

from os import path

from galicaster.recorder import base
from galicaster.recorder import module_register

class GCcustom(gst.Bin, base.Base):

    order = ["name", "flavor", "location", "file", "pipestr"]
    gc_parameters = {
        "name": {
            "type": "text",
            "default": "Webcam",
            "description": "Name assigned to the device",
            },
        "flavor": {
            "type": "flavor",
            "default": "presenter",
            "description": "Matterhorn flavor associated to the track",
            },
        "location": {
            "type": "device",
            "default": "/dev/webcam",
            "description": "Device's mount point of the xoutput",
            },
        "file": {
            "type": "text",
            "default": "CAMERA.avi",
            "description": "The file name where the track will be recorded.",
            },
        "pipestr": {
            "type": "text",
            "default": "fakesrc name=gc-custom-src ! valve drop=false name=gc-custom-valve ! fakesink ",
            "description": "Custom pipeline. It has to hava a valve (gc-custom-valve), a source (gc-custom-src) and a filesink (gc-custom-sink)",
            },
        }
    
    is_pausable = True
    has_audio   = False
    has_video   = True

    __gstdetails__ = (
        "Galicaster CUSTOM Bin",
        "Generic/Video",
        "Generice bin to custom interface devices",
        "Teltek Video Research",
        )

    def __init__(self, options={}):
        base.Base.__init__(self, options)
        gst.Bin.__init__(self, self.options['name'])

        aux = self.options['pipestr'].replace('gc-custom-preview', 'sink-' + self.options['name'])

        #bin = gst.parse_bin_from_description(aux, False)
        bin = gst.parse_launch("( {} )".format(aux))
        self.add(bin)

        self.set_value_in_pipeline(path.join(self.options['path'], self.options['file']), 'gc-custom-sink', 'location')

    def changeValve(self, value):
        valve1=self.get_by_name('gc-custom-valve')
        valve1.set_property('drop', value)

    def getVideoSink(self):
        return self.get_by_name('gc-custom-preview')
    
    def getSource(self):
        return self.get_by_name('gc-custom-src') 

    def send_event_to_src(self, event):
        src1 = self.get_by_name('gc-custom-src')
        src1.send_event(event)


gobject.type_register(GCcustom)
gst.element_register(GCcustom, 'gc-custom-bin')
module_register(GCcustom, 'custom')
