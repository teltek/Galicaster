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
        branch = []
        # Colorspace

        queuePrimary = gst.element_factory_make('queue',
                                                'gc-{0}-{1}-queue-first'.format(binname, self.class_name))
        colorPrimary = gst.element_factory_make('ffmpegcolorspace', 
                                                'gc-{0}-{1}-color-first'.format(binname, self.class_name))
        capsPrimary =  gst.element_factory_make('capsfilter', 
                                                'gc-{0}-{1}-caps-first'.format(binname, self.class_name))
        capsPrimary.set_property('caps',gst.Caps('video/x-raw-yuv,format=(fourcc)AYUV'))
        queueSecondary = gst.element_factory_make('queue',
                                                'gc-{0}-{1}-queue-second'.format(binname, self.class_name))
        colorSecondary = gst.element_factory_make('ffmpegcolorspace', 
                                                  'gc-{0}-{1}-color-second'.format(binname, self.class_name))
        capsSecondary =  gst.element_factory_make('capsfilter',
                                                 'gc-{0}-{1}-caps-second'.format(binname, self.class_name))
        capsSecondary.set_property('caps',gst.Caps('video/x-raw-yuv,format=(fourcc)AYUV'))
        branch = []
            
        elements += [colorPrimary, capsPrimary, queuePrimary]
        branch += [colorSecondary, capsSecondary, queueSecondary]

        #Mixer
        mixer = gst.element_factory_make('videomixer2', 'gc-{0}-{1}-mixer'.format(binname, self.class_name))
        mixer.set_property('background',1)
        colorMixer = gst.element_factory_make('ffmpegcolorspace', 
                                              'gc-{0}-{1}-color-mixer'.format(binname, self.class_name))
        
        elements += [mixer, colorMixer]
        capsMixer = gst.element_factory_make('capsfilter',
                                             'gc-{0}-{1}-caps-mixer'.format(binname, self.class_name))
        width = self.options['primary'][0]
        if self.options['layout']=='sbs':
            width += self.options['secondary'][0]
        capsMixer.set_property('caps',gst.Caps('{0},width={1},height={2}'.format(
                    'video/x-raw-yuv', width, self.options['primary'][1])))
        elements += [capsMixer]

        #Compostion and Z order
        primary_pad = mixer.get_pad('sink_0')
        secondary_pad = mixer.get_pad('sink_1')
        primary_pad.set_property("zorder",0)
        secondary_pad.set_property("zorder",1)

        # Controler
        self.control_primary = gst.Controller(primary_pad, "xpos", "ypos")
        self.control_secondary = gst.Controller(secondary_pad, "xpos", "ypos")
        self.control_primary.set_interpolation_mode("xpos", gst.INTERPOLATE_LINEAR)
        self.control_primary.set_interpolation_mode("ypos", gst.INTERPOLATE_LINEAR)
        self.control_secondary.set_interpolation_mode("xpos", gst.INTERPOLATE_LINEAR)
        self.control_secondary.set_interpolation_mode("ypos", gst.INTERPOLATE_LINEAR)

        # Initial position

        x2,y2 = self.definePositions(self.options['layout'], self.options['position'])
        
        x1,y1 = [0,0]
        if self.options['layout'] ==  "sbs" and self.options["position"].split('-')[0] == "left":
            x1 = self.options['secondary'][0]

        # TODO take into account margins if defined

        #CONTROL
        self.current_position =  self.options["position"]
        self.control_secondary.set("xpos", 0, x2)
        self.control_secondary.set("ypos", 0, y2)
        self.control_primary.set("xpos", 0, x1)

        # COMMON PART
        for element in elements+branch:
            self.add(element)
        for n, element in enumerate(elements):
            if n<len(elements)-1:
                element.link(elements[n+1])      
        branch += [mixer]
        for n, element in enumerate(branch):
            if n<len(branch)-1:
                element.link(branch[n+1])              

        # PADS
        end = elements[len(elements)-1]
        self.add_pad(gst.GhostPad('ghostsink-{0}'.format(self.sinkpads), elements[0].get_pad('sink')))
        self.sinkpads +=1
        self.add_pad(gst.GhostPad('ghostsink-{0}'.format(self.sinkpads), branch[0].get_pad('sink')))
        self.sinkpads +=1
        self.add_pad(gst.GhostPad('ghostsource-{0}'.format(self.sourcepads), end.get_pad('src'))) 
        self.sourcepads +=1

    def changePosition(self):
        #Idem to shift but selection side-position
        pass  

    def definePositions(self, layout, position): # TODO make it also for SBS
        w1,h1 = self.options['primary']
        w2,h2 = self.options['secondary']
        
        options = self.parameters['position']['options']
        list_pos = {}
        for option in options:
            x,y = [0,0]
            if option.split('-')[1] == 'mid':
                y = int((h1-h2)/2)
            elif option.split('-')[1] == 'bottom':
                y = h1-h2
            if option.split('-')[0] == 'right':
                if layout == "sbs":#TOD Define Primary X
                    x = w1
                elif layout == "pip":
                    x = w1 -w2
            list_pos[option] = (x,y)
        return list_pos[position]
                     
    def shiftPosition(self, base_time=0):
        current = self.parameters['position']['options'].index(self.current_position)
        new = current+1 if (current+1)<(len(self.parameters['position']['options'])) else 0 # rotate index
        self.current_position = self.parameters['position']['options'][new]
        new_position = self.definePositions(self.options['layout'], 
                                            self.current_position)
        #time = self.get_parent().get_clock().get_time()-base_time
        #self.control_secondary.set("xpos", time - (1 * gst.SECOND), new_position[0])
        #self.control_secondary.set("ypos", time - (1 * gst.SECOND) , new_position[1])
        self.control_secondary.set("xpos", 0, new_position[0])
        self.control_secondary.set("ypos", 0, new_position[1])
        if self.options['layout'] == "sbs":
            shifting = 0 if self.current_position.count('right') else self.options['secondary'][0]
            self.control_primary.set("xpos", 0, shifting)
  
gobject.type_register(VideoMixer)
gst.element_register(VideoMixer, 'gc-filter-videomixer')
module_register(VideoMixer, 'filter-videomixer')
