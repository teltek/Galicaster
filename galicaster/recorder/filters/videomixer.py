# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/filters/videomixer
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
from galicaster.recorder.filters.base import GCBaseFilter
from galicaster.recorder import module_register

class VideoMixer(GCBaseFilter):

    class_name = "videomixer"
    class_type = "filter"
    order = ["layout", "position"]
    
    parameters = {
        "layout" : {
            "type" : "selection",
            "description" : "Type of composition layout",
            "options": ["sbs", "pip"],
            "default" : "sbs",
            },
        "position" : {
            "type" : "selection",
            "description" : "Position for the secondary video",
            "options": ["left-top", "left-mid","left-bottom",
                        "right-top", "right-mid","right-bottom"],                        
            "default" : "left-mid",
            },
        "image" : {
             "type" : "path",
            "description" : "Path to a valid image for mixing with the composition",
            "default" : None,
            },
        "mosca" : {
            "type" : "path",
            "description" : "Path to a valid image for mixing with the composition",
            "default" : None,
            },
        "primary" : {
            "type" : "resolution",
            "description" : "Target resolution of the composition",
            "default" : None,
            },
        "secondary" : {
            "type" : "resolution",
            "description" : "Target resolution of the composition",
            "default" : None,
            },

        # TODO superposition between images, designate one of the sources.

        }
    
    is_pausable = True
    has_audio   = False
    has_video   = True
    sourcepads = 0
    sinkpads = 0

    __gstdetails__ = (# TODO move to BASE
        "Galicaster {0} {1}".format(class_name.upper(),class_type.capitalize()),
        "Generic/{0}".format("Sink"),
        "Generice sink for preview video raw",
        "Teltek Video Research",
        )
        
    def __init__(self, binname, default={}, options={}):
        
        GCBaseFilter.__init__(self, binname, default, options)
        
        # CHECK options
        elements = []

        #Mixer
        mixer = gst.element_factory_make('videomixer', 'gc-{0}-{1}-mixer'.format(binname, self.class_name))
        mixer.set_property('background',1)
        elements += [mixer]
        #Compostion
        primary_pad = mixer.get_pad('sink_0')
        secondary_pad = mixer.get_pad('sink_1')
        primary_pad.set_property("zorder",0)
        secondary_pad.set_property("zorder",1)

        # Initial position
        side,position = self.options["position"].split('-')
        w1,h1 = self.options['primary']
        w2,h2 = self.options['secondary']

        if position == "mid":
            secondary_pad.set_property("ypos", int((h1-h2)/2))
        elif position == "bottom":
            secondary_pad.set_property("ypos", h1-h2)            
        else:# top
            secondary_pad.set_property("ypos", 0)
        if self.options["layout"] == "sbs":
            primary_pad.set_property("xpos", w2 if side == "left" else 0)
            secondary_pad.set_property("xpos", 0 if side == "left" else w1)
        else: # pip
            secondary_pad.set_property("xpos", 0 if side == "left" else w1-w2)

        print "PRIMARY",self.options['primary'],primary_pad.get_property('xpos'),primary_pad.get_property('ypos')
        print "SECONDARY",self.options['secondary'],secondary_pad.get_property('xpos'), secondary_pad.get_property('ypos')
        # TODO add images

        # Controler
        #self.control_primary = gst.Controller(primary_pad, "xpos", "ypos")
        #self.control_secondary = gst.Controller(secondary_pad, "xpos", "ypos")
        #self.control_primary.set_interpolation_mode("xpos", gst.INTERPOLATE_LINEAR)
        #self.control_primary.set_interpolation_mode("ypos", gst.INTERPOLATE_LINEAR)
        #self.control_secondary.set_interpolation_mode("xpos", gst.INTERPOLATE_LINEAR)
        #self.control_secondary.set_interpolation_mode("ypos", gst.INTERPOLATE_LINEAR)

        #Color
        #color = gst.element_factory_make('ffmpegcolorspace')
        #elements += [color]

        # COMMON PART
        for element in elements:
            self.add(element)
        for n, element in enumerate(elements):
            if n<len(elements)-1:
                element.link(elements[n+1])      
        first = elements[0] #UNUSED
        end = elements[len(elements)-1]
        self.add_pad(gst.GhostPad('ghostsink-{0}'.format(self.sinkpads), primary_pad)) 
        self.sinkpads +=1
        self.add_pad(gst.GhostPad('ghostsink-{0}'.format(self.sinkpads), secondary_pad)) 
        self.sinkpads +=1
        self.add_pad(gst.GhostPad('ghostsource-{0}'.format(self.sourcepads), end.get_pad('src'))) 
        self.sourcepads +=1

    def changePosition(self):
        #Idem to shift but selection side-position
        pass  

    def shiftPosition(self):
        #Make and index from resolutions
        #Discover current position
        #Set new position with the controller
        #With or without animation
        return

  
  
gobject.type_register(VideoMixer)
gst.element_register(VideoMixer, 'gc-filter-videomixer')
module_register(VideoMixer, 'filter-videomixer')
