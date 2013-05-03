# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/sinks/base
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

import logging
import gst

from galicaster.recorder import validate

logger = logging.getLogger()


class GCBaseSink(gst.Bin):
    """
    Base bin for sinks
    """
    
    class_name = "base"
    class_type = "sink"
    
    has_audio = False
    has_video = False
    is_pausable = False
    
    __gstdetails__ = (
        "Galicaster {0} Bin".format(class_name),
        "Generic/{0}".format("Both" if has_video and has_audio else "Video"),
        "Generice bin to v4l2 interface devices",
        "Teltek Video Research",
        )
    
    def __init__(self, binname, defaults={}, options={}):

        self.binname = binname
        for key in defaults.iterkeys(): # TODO parse always
            self.parameters[key]['default']=defaults[key]

        gst.Bin.__init__(self, "gc-{0}-{1}-{2}".format(binname, self.class_name,self.class_type))
        error = self.validate_options(options)
        for validity, key in error.iteritems():
            if not validity:
                print str(key)+" Error"

        self.options = dict([(k,v['default']) for k,v in self.parameters.iteritems()])
        self.options.update(options)
 
    def getSink(self):
        return self.get_by_name('gc-{0}-{1}-{2}'.format(self.class_name, self.binname, 'sink')) 

    def getGhostpad(self):
        return self.get_pad('ghostpad')

    def getVideoGhostpad(self):
        if self.has_video and self.has_audio:
            return self.get_pad('ghostpad-video')
        else:
            return self.getGhostpad()

    def getAudioGhostpad(self):
        if self.has_video and self.has_audio:
             return self.get_pad('ghostpad-audio')
        else:
            return self.getGhostpad()

    def blockPad(self):
        #self.first.get_pad('sink').set_blocked_async(block, self.callback)        
        pad = self.first.get_pad('sink')
        pad.set_blocked(True)
        self.set_state(gst.STATE_NULL)
        #elf.first.unlink(peer)

    def unLink(self):
        self.first.get_pad('sink').unlink()
        self.set_state(gst.STATE_NULL)

    def recoverBin(self, location):
        self.getSink().set_property('location',location)
        pad = self.first.get_pad('sink')
        pad.set_blocked(False)
        self.set_state(gst.STATE_PAUSED)
        self.set_locked_state(True)    
        #self.link(peer)

    def callback(self, pad, value=None): #UNUSED
        print pad, "SHOULD UNLINK and NULL STATE"

    def sendEventToSrc(self, event):
        if not isinstance(self.first,list):
            self.first.send_event(event)#TODO be always a list
        else:
            for element in self.first:
                element.send_event(event)

    def drop(self, dropping): # REMOVE if valve's missing
        self.valve.set_property('drop', dropping)

    def validate_options(self, options):
        valid={}
        for key,value in options.iteritems():
            value_type = self.parameters[key]['type']
            validation = getattr(validate,"validate_{0}".format(value_type))
            if value_type is 'float':
                valid[key], options[key] = validation(value,self.parameters[key]['range'])
            elif value_type is 'selection':
                valid[key], options[key] = validation(value,self.parameters[key]['options'])
            else:
                valid[key], options[key] = validation(value)
        return valid

    def makeScaleCaps(self, name, mime, resolution, options={}):
        # TODO move to utils
        element = gst.element_factory_make('capsfilter','gc-{0}-{1}-caps'.format(self.class_name, name))
        caps = "{0},width={1},height={2}".format(mime,resolution[0],resolution[1])
        print "Scale",caps
        if len(options):
            for key,value in options.iterkeys():
                caps+=",{0}={1}".format(key,value)
        element.set_property('caps', gst.Caps(caps))
        return element
            
            
