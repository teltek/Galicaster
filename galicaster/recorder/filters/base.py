# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/filters/base
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


class GCBaseFilter(gst.Bin):
    """
    Base bin for filtesr
    """
    
    class_name = "base"
    class_type = "filter"
    
    has_audio = False
    has_video = False
    is_pausable = False
    srcpads = 0
    sinkpads = 0
    
    __gstdetails__ = (
        "Galicaster {0} Bin".format(class_name),
        "Generic/{0}".format("Filter"),
        "Generice bin for filters",
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


    def getSourceGhostpads(self):
        pads = []
        for index in range(self.sourcepads):
            pads += self.getGhospad('ghostsource-'+index)
        return pads
        
    def getSinkGhostpads(self):
        pads = []
        for index in range(self.sinkpads):
            pads += self.getGhospad('ghostsink-'+index)
        return pads

    def getGhostpad(self, name):
        return self.get_pad(name)       

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
