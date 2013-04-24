# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/sources/v4l2
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


class v4l2Source(GCBaseSource):

    class_name = "v4l2"
    class_type = "source"
    order = ["location","framerate", "resolution", "input-encoding"]
    
    parameters = {
        "location": {
            "type": "videopath",
            "default": "/dev/webcam",
            "description": "Device's mount point of the output",
            },
        "input-encoding" : {
            "type" : "selection",
            "description" : "Encoding type of the source",
            "default" : None, # Better RAW?,
            "options": [None,"mjpeg"],
            },
        "framerate" : {
            "type" : "framerate",
            "description" : "Demands or fix a certain framerate to the source",
            "default" : None,
            },
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
        "Generic/{0}".format("Video" if not has_audio else "Both"),
        "Generice source for v4l2 interface devices",
        "Teltek Video Research",
        )
        
    def __init__(self, binname, default={}, options={}):
        
        GCBaseSource.__init__(self,binname, default, options)

        # CHECK options
        elements = []
        encoding = 'video/x-raw-yuv' if not self.options['input-encoding'] else 'image/jpeg'

        #SOURCE
        source = gst.element_factory_make('v4l2src','gc-{0}-{1}-src'.format(self.class_name, binname))
        source.set_property('device', self.options['location'])
        sourceCaps =  self.makeVideoCaps('src', 
                                    encoding,
                                    self.options['resolution'],
                                    self.options['framerate'])
        sourceQueue= gst.element_factory_make('queue','gc-{0}-{1}-src-queue'.format(self.class_name, binname))
        #sourceQueue.set_property('leaky',2)
        elements += [source, sourceCaps, sourceQueue]
        
        # Decoding for MJPEG sources
        if encoding == 'image/jpeg':
            mjpegDecoder = gst.element_factory_make('jpegdec','gc-{0}-{1}-src-mjpeg-decoder'.format(self.class_name, 
                                                                                                    binname))
            mjpegDecoder.set_property('max-errors', -1)
            mjpegQueue = gst.element_factory_make('queue','gc-{0}-{1}-mjpeg-queue'.format(self.class_name, binname))
            elements += [mjpegDecoder, mjpegQueue]
                
        # FRAMERATE safeguard
        rateSafeguard = gst.element_factory_make('videorate','gc-{0}-{1}-src-rate-safeguard'.format(self.class_name, 
                                                                                                    binname))
        rateCaps = self.makeVideoCaps('{0}-src'.format(binname), 
                                 'video/x-raw-yuv',
                                 self.options['resolution'],
                                 self.options['framerate'])
        elements += [rateSafeguard, rateCaps]

        for element in elements:
            self.add(element)
        for n, element in enumerate(elements):
            if n<len(elements)-1:
                element.link(elements[n+1])      
        end = elements[len(elements)-1]
        self.add_pad(gst.GhostPad('ghostpad', end.get_pad('src')))       

gobject.type_register(v4l2Source)
gst.element_register(v4l2Source, 'gc-v4l2-source')
module_register(v4l2Source, 'v4l2-source')
