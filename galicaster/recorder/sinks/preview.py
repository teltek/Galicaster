# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/sinks/preview
# -*- coding:utf-8 -*-
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

import gobject
import gst
from galicaster.recorder.sinks.base import GCBaseSink
from galicaster.recorder import module_register

class previewVideoSink(GCBaseSink):

    class_name = "previewvideo"
    class_type = "sink"
    order = ["resolution"]
    
    parameters = {
        "resolution" : {
            "type" : "resolution",
            "description" : "Demands or fix a certain resolution to the source",
            "default" : None,
            },
        }
    
    is_pausable = True
    has_audio   = False
    has_video   = True

    __gstdetails__ = (# TODO move to BASE
        "Galicaster {0} {1}".format(class_name.upper(),class_type.capitalize()),
        "Generic/{0}".format("Sink"),
        "Generice sink for preview video raw",
        "Teltek Video Research",
        )
        
    def __init__(self, binname, default={}, options={}):
        
        GCBaseSink.__init__(self, binname, default, options)
        
        # CHECK options
        elements = []
        
        #SINK
        sinkQueue = gst.element_factory_make('queue','gc-{0}-{1}-sink-queue'.format(binname, self.class_name))
        elements +=[sinkQueue]
        if self.options["resolution"]:
            sinkScale = gst.element_factory_make('videoscale',"gc-{0}-{1}-sink-scale".format(binname, 
                                                                                             self.class_name))
            sinkScale.set_property('add-borders',True)
            sinkScaleCaps= self.makeScaleCaps('sink', 'video/x-raw-yuv', self.options['resolution'])
            elements +=[sinkScale,sinkScaleCaps]            
            
        # sink = gst.element_factory_make('xvimagesink','gc-{0}-{1}-sink'.format(self.class_name, binname))
        sink = gst.element_factory_make('xvimagesink','sink-{0}'.format(binname))
        sink.set_property('async', False)
        sink.set_property('sync', False)
        sink.set_property('qos', False)
        elements += [sink]
        for element in elements:
            self.add(element)
        for n, element in enumerate(elements):
            if n<len(elements)-1:
                element.link(elements[n+1])      
        first = elements[0]
        self.add_pad(gst.GhostPad('ghostpad', first.get_pad('sink')))  

class previewAudioSink(GCBaseSink):

    class_name = "previewaudio"
    class_type = "sink"
    order = ["volume", "player", "vumeter"]
    
    parameters = {
        "volume" : {
            "type" : "float",
            "description" : "Amplification of the audio preview",
            "range" : [0.0,5.0],
            "default" : 1.0,
            },
        "player": { # Volume can do it on its own
            "type": "boolean",
            "default": True,
            "description": "Enable sound play",
            },
        "vumeter": {
            "type": "boolean",
            "default": True,
            "description": "Activate Level message",
            },        
        }

    is_pausable = True
    has_audio   = True
    has_video   = False

    __gstdetails__ = (# TODO move to BASE
        "Galicaster {0} {1}".format(class_name.upper(),class_type.capitalize()),
        "Generic/{0}".format("Sink"),
        "Generice sink for preview audio raw",
        "Teltek Video Research",
        )
        
    def __init__(self, binname, default={}, options={}):
        
        GCBaseSink.__init__(self, binname, default, options)
        
        # CHECK options
        elements = []
        
        #SINK
        binQueue = gst.element_factory_make('queue', 'gc-{0}-{1}-main-queue'.format(binname, self.class_name))
        elements += [binQueue]
        level = gst.element_factory_make('level','gc-{0}-{1}-vumeter'.format(binname, self.class_name))
        level.set_property('message', self.options["vumeter"])
        level.set_property('interval', 100000000)
        volume = gst.element_factory_make('volume', 'gc-{0}-{1}-volume'.format(binname, self.class_name))
        volume.set_property('volume', self.options["volume"])
        sinkQueue = gst.element_factory_make('queue', 'gc-{0}-{1}-sink-queue'.format(binname, self.class_name))
        sink = gst.element_factory_make('alsasink', 'sink-{0}'.format(binname))
        sink.set_property('async', False)
        sink.set_property('sync', False)
        sink.set_property('qos', False) # default is already false
        elements += [level, volume, sinkQueue, sink]
        for element in elements:
            self.add(element)
        for n, element in enumerate(elements):
            if n<len(elements)-1:
                element.link(elements[n+1])      
        first = elements[0]
        self.add_pad(gst.GhostPad('ghostpad', first.get_pad('sink')))     

gobject.type_register(previewVideoSink)
gst.element_register(previewVideoSink, 'gc-preview-video-sink')
module_register(previewVideoSink, 'preview-video-sink')

gobject.type_register(previewAudioSink)
gst.element_register(previewAudioSink, 'gc-preview-audio-sink')
module_register(previewAudioSink, 'preview-audio-sink')
