# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/sources/pulse
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
from galicaster.recorder.sources.base import GCBaseSource
from galicaster.recorder import module_register


class pulseSource(GCBaseSource):

    class_name = "pulse"
    class_type = "source"
    order = ["location"]
    
    parameters = {
        "location": {
            "type": "audiopath",
            "default": "default",
            "description": "Device's mount point of the output",
            },
        }
    is_pausable = True
    has_audio   = True
    has_video   = False

    __gstdetails__ = (# TODO move to BASE
        "Galicaster {0} {1}".format(class_name.upper(),class_type.capitalize()),
        "Generic/{0}".format("Audio"),
        "Generice source for pulse audio system devices",
        "Teltek Video Research",
        )
        
    def __init__(self, binname, default={}, options={}):
        
        GCBaseSource.__init__(self, binname, default, options)

        elements = []

        #SOURCE
        source = gst.element_factory_make('pulsesrc','gc-{0}-{1}src'.format(self.class_name, binname))
        source.set_property('device', self.options['location'])
        sourceQueue= gst.element_factory_make('queue','gc-{0}-{1}-src-queue'.format(self.class_name, binname))
        elements += [source, sourceQueue]

        for element in elements:
            self.add(element)
        for n, element in enumerate(elements):
            if n<len(elements)-1:
                element.link(elements[n+1])      
        end = elements[len(elements)-1]
        self.add_pad(gst.GhostPad('ghostpad', end.get_pad('src')))       

gobject.type_register(pulseSource)
gst.element_register(pulseSource, 'gc-pulse-source')
module_register(pulseSource, 'pulse-source')
