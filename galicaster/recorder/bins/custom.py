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

from os import path

from gi.repository import Gst

from galicaster.recorder import base

class GCcustom(Gst.Bin, base.Base):

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
            "description": "Opencast flavor associated to the track",
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
            "description": "Custom pipeline. It has to have a valve (gc-custom-valve), a source (gc-custom-src) and a filesink (gc-custom-sink)",
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
        Gst.Bin.__init__(self)

        aux = self.options['pipestr'].replace('gc-custom-preview', 'sink-' + self.options['name'])

        #bin = Gst.parse_bin_from_description(aux, False)
        bin = Gst.parse_launch("( {} )".format(aux))
        self.add(bin)

        if self.get_by_name('gc-custom-sink'):
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


