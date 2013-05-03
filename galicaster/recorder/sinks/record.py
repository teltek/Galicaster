# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/sinks/record
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

class recordVideoSink(GCBaseSink):

    class_name = "videorecord"
    class_type = "sink"
    order = ["file","videoencoder","muxer"]
    
    parameters = {
        "file" : {
            "type" : "videopath",
            "description" : "Filename, without extension, to record the data",
            "default" : "CAMERA",
            },
        "videoencoder" : {
            "type" : "gstelement",
            "description" : " A tuple with a GST element and a dict of properties in string format",
            "default" : ("xvidenc", {"bitrate":5000000}),
            },
        "muxer" : {
            "type" : "gstelement",
            "description" : " A tuple with a GST element and a dict of properties in string format",
            "default" : ("avimux", {}),
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
        extension=self.options['muxer'][0].split("mux")[0] # TODO only valid for avi, flv, mp4, mxf and some moer
        self.extension = extension

        self.valve = gst.element_factory_make('valve', 
                                         'gc-{0}-{1}-valve'.format(self.class_name,binname))
        elements += [self.valve]
        binQueue = gst.element_factory_make('queue', 'gc-{0}-{1}-main-queue'.format(binname, self.class_name))
        elements += [binQueue]
        #ENCAPSULATION
        colorSpace = gst.element_factory_make('ffmpegcolorspace',
                                              'gc-{0}-{1}-color'.format(self.class_name,binname))
        encoder =  gst.element_factory_make(self.options['videoencoder'][0],
                                            'gc-{0}-{1}-encoder'.format(self.class_name,binname))
        if len(self.options['videoencoder'][1]):
            for key,value in self.options['videoencoder'][1].iteritems(): # TODO check properties in validation
                encoder.set_property(key,value)

        muxerQueue = gst.element_factory_make('queue',
                                              'gc-{0}-{1}-muxer-queue'.format(self.class_name, binname))
        muxer = gst.element_factory_make(self.options['muxer'][0],
                                              'gc-{0}-{1}-muxer'.format(self.class_name, binname))
        if len(self.options['muxer'][1]):
            for key,value in self.options['muxer'][1].iteritems(): # TODO check properties in validation
                muxer.set_property(key,value)

        #SINK
        sinkQueue = gst.element_factory_make('queue',
                                              'gc-{0}-{1}-sink-queue'.format(self.class_name, binname))
        sink = gst.element_factory_make('filesink',
                                              'gc-{0}-{1}-sink'.format(self.class_name, binname))
        sink.set_property('location', 
                          "{0}.{1}".format(self.options['file'],extension))
        sink.set_property("async", False)
        
        elements += [colorSpace, encoder, muxerQueue, muxer, sinkQueue, sink]

        for element in elements:
            self.add(element)
        for n, element in enumerate(elements):
            if n<len(elements)-1:
                element.link(elements[n+1])      
        first = elements[0]
        self.first = first
        self.add_pad(gst.GhostPad('ghostpad', first.get_pad('sink')))       

    def startRecord():
        pass
    def stopRecord():
        pass
    def pauseRecord():
        pass

    def changeLocation(self, new_location):#duplicated on recordaudiosink
        #print "Change Location", self.get_state()
        self.getSink().set_property('location',"{0}.{1}".format(new_location, self.extension))


class recordAudioSink(GCBaseSink):

    class_name = "audiorecord"
    class_type = "sink"
    order = ["file","audioencoder","muxer"]
    
    parameters = {
        "file" : {
            "type" : "audiopath",
            "description" : "Filename, without extension, to record the data",
            "default" : "SOUND",
            },
        "audioencoder" : {
            "type" : "gstelement",
            "description" : "A tuple with a GST element and a dict of properties in string format",
            "default" : ("lamemp3enc", {"target":1,"bitrate":192,"cbr":True}),
            },
        "muxer" : {
            "type" : "gstelement",
            "description" : "A tuple with a GST element and a dict of properties in string format",
            "default" : None, # MP3 doesn't needs a encoder-muxer
            },
        "amplification" : {
            "type" : "float",
            "description" : "Software audio amplification", # CHECK only affects filesink
            "range" : [0.0, 10.0],
            "default" : 1.0, # MP3 doesn't needs a encoder-muxer
            },
        }
    
    is_pausable = True
    has_audio   = True
    has_video   = False

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
        extension = 'mp3' # TODO select extension properly, mp2, mp3, ogg, acc ...
        self.extension = extension

        self.valve = gst.element_factory_make('valve', 
                                         'gc-{0}-{1}-valve'.format(self.class_name,binname))
        elements += [self.valve]
        binQueue = gst.element_factory_make('queue', 'gc-{0}-{1}-main-queue'.format(binname, self.class_name))
        elements += [binQueue]

        #ENCAPSULATION

        audioconvert = gst.element_factory_make('audioconvert',
                                              'gc-{0}-{1}-audioconvert'.format(self.class_name, binname))
        amplify = gst.element_factory_make('audioamplify',
                                              'gc-{0}-{1}-amplifier'.format(self.class_name, binname))
        amplify.set_property("amplification", self.options['amplification'])
        muxerQueue = gst.element_factory_make('queue',
                                              'gc-{0}-{1}-muxer-queue'.format(self.class_name, binname))
        encoder =  gst.element_factory_make(self.options['audioencoder'][0],
                                            'gc-{0}-{1}-encoder'.format(self.class_name,binname)) 
        if len(self.options['audioencoder'][1]):
            for key,value in self.options['audioencoder'][1].iteritems(): # TODO check properties in validation
                encoder.set_property(key,value)
        elements += [ audioconvert, amplify, muxerQueue, encoder ] 
        if self.options['muxer']:
            muxer = gst.element_factory_make(self.options['muxer'][0],
                                             'gc-{0}-{1}-muxer'.format(self.class_name, binname))
            if len(self.options['muxer'][1]):
                for key,value in self.options['muxer'][1].iteritems(): # TODO check properties in validation
                    muxer.set_property(key,value)
            element += [ muxer ]
        # SINK
        sinkQueue = gst.element_factory_make('queue',
                                              'gc-{0}-{1}-sink-queue'.format(self.class_name, binname))
        sink = gst.element_factory_make('filesink',
                                              'gc-{0}-{1}-sink'.format(self.class_name, binname))
        sink.set_property('location', 
                          "{0}.{1}".format(self.options['file'],extension))
        sink.set_property("async", False)
        elements += [ sinkQueue, sink ]
        
        for element in elements:
            self.add(element)
        for n, element in enumerate(elements):
            if n<len(elements)-1:
                element.link(elements[n+1])      
        first = elements[0]
        self.first = first
        self.add_pad(gst.GhostPad('ghostpad', first.get_pad('sink')))       

    def startRecord():
        pass
    def stopRecord():
        pass
    def pauseRecord():
        pass
    def drop(self,dropping):
        self.valve.set_property('drop',dropping)

    def changeLocation(self, new_location):
        #TODO check state before
        self.getSink().set_property('location',"{0}.{1}".format(new_location, self.extension))

class recordAudioVideoSink(GCBaseSink):

    class_name = "avrecord"
    class_type = "sink"
    order = ["file","videoencoder","audioencoder""muxer"]
    
    parameters = {
        "file" : {
            "type" : "videopath",
            "description" : "Filename, without extension, to record the data",
            "default" : "CAMERA",
            },
        "videoencoder" : {
            "type" : "gstelement",
            "description" : " A tuple with a GST element and a dict of properties in string format",
            "default" : ("xvidenc", {"bitrate":5000000}),
            },
        "audioencoder" : {
            "type" : "gstelement",
            "description" : "A tuple with a GST element and a dict of properties in string format",
            "default" : ("lamemp3enc", {"target":1,"bitrate":192,"cbr":True}),
            },
        "muxer" : {
            "type" : "gstelement",
            "description" : " A tuple with a GST element and a dict of properties in string format",
            "default" : ("avimux", {}),
            },
        }
    
    is_pausable = True
    has_audio   = True
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
        branch = []
        extension=self.options['muxer'][0].split("mux")[0] # TODO only valid for avi, flv, mp4, mxf and some moer
        self.extension = extension
        self.pads=[False, False]
        # TODO do the encoders need Queues
        
        #VIDEO ENCODER
        colorSpace = gst.element_factory_make('ffmpegcolorspace',
                                              'gc-{0}-{1}-color'.format(self.class_name,binname))
        encoderVideo =  gst.element_factory_make(self.options['videoencoder'][0],
                                            'gc-{0}-{1}-v-encoder'.format(self.class_name,binname))
        if len(self.options['videoencoder'][1]):
            for key,value in self.options['videoencoder'][1].iteritems(): # TODO check properties in validation
                encoderVideo.set_property(key,value)

        muxerVideoQueue = gst.element_factory_make('queue',
                                              'gc-{0}-{1}-muxer-v-queue'.format(self.class_name, binname))

        # AUDIO ENCODER
        audioConvert =  gst.element_factory_make('audioconvert',
                                                 'gc-{0}-{1}-audioconvert'.format(self.class_name, binname))
        encoderAudio =  gst.element_factory_make(self.options['audioencoder'][0],
                                            'gc-{0}-{1}-a-encoder'.format(self.class_name,binname)) 
        if len(self.options['audioencoder'][1]):
            for key,value in self.options['audioencoder'][1].iteritems(): # TODO check properties in validation
                encoderAudio.set_property(key,value)
        muxerAudioQueue = gst.element_factory_make('queue',
                                                   'gc-{0}-{1}-muxer-a-queue'.format(self.class_name, binname))

        # ENCAPSULATION
        muxer = gst.element_factory_make(self.options['muxer'][0],
                                              'gc-{0}-{1}-muxer'.format(self.class_name, binname))
        if len(self.options['muxer'][1]):
            for key,value in self.options['muxer'][1].iteritems(): # TODO check properties in validation
                muxer.set_property(key,value)

        # SINK
        sinkQueue = gst.element_factory_make('queue',
                                              'gc-{0}-{1}-sink-queue'.format(self.class_name, binname))
        sink = gst.element_factory_make('filesink',
                                              'gc-{0}-{1}-sink'.format(self.class_name, binname))
        sink.set_property('location', 
                          "{0}.{1}".format(self.options['file'],extension))
        sink.set_property("async", False)
        
        elements += [colorSpace, encoderVideo, muxerVideoQueue, muxer, sinkQueue, sink]
        branch += [audioConvert, encoderAudio, muxerAudioQueue]

        for element in elements+branch:
            self.add(element)
        for n, element in enumerate(elements):
            if n<len(elements)-1:
                element.link(elements[n+1])
        branch += [muxer]
        for n, element in enumerate(branch):
            if n<len(branch)-1:
                element.link(branch[n+1])      
        first = [elements[0],branch[0]]
        self.first = first
        self.add_pad(gst.GhostPad('ghostpad-video', first[0].get_pad('sink')))  
        self.add_pad(gst.GhostPad('ghostpad-audio', first[1].get_pad('sink')))       

    def stopElement(self,pad):
        self.pads[pad] = True
        if self.pads[0] and self.pads[1]:
            self.set_state(gst.STATE_NULL)

    def startRecord():
        pass
    def stopRecord():
        pass
    def pauseRecord():
        pass

    def changeLocation(self, new_location):#duplicated on recordaudiosink
        #print "Change Location", self.get_state()
        self.getSink().set_property('location',"{0}.{1}".format(new_location, self.extension))


gobject.type_register(recordVideoSink)
gst.element_register(recordVideoSink, 'gc-record-video-sink')
module_register(recordVideoSink, 'record-video-sink')

gobject.type_register(recordAudioSink)
gst.element_register(recordAudioSink, 'gc-record-audio-sink')
module_register(recordAudioSink, 'record-video-sink')

gobject.type_register(recordAudioVideoSink)
gst.element_register(recordAudioVideoSink, 'gc-record-audiovideo-sink')
module_register(recordAudioVideoSink, 'record-audiovideo-sink')
