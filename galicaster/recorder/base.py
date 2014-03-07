# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/base
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

from os import path
import re

FLAVOR = ['presenter', 'presentation', 'other']

class Base(object):
    gc_parameters = {
        "name": {
            "type": "text",
            "default": "Device",
            "description": "Name assigned to the device",
            },
        "flavor": {
            "type": "flavor",
            "default": "presenter",
            "description": "Matterhorn flavor associated to the track",
            },
        "location": {
            "type": "device",
            "default": "/dev/video0",
            "description": "Device's mount point of the MPEG output",
            },
        "file": {
            "type": "text",
            "default": "CAMERA.avi",
            "description": "The file name where the track will be recorded.",
            },
        }

    def __init__(self, options):
        # Init gc_parameters add Base and Object class
        self.gc_parameters = self.get_gc_parameters()

        # Init options with default gc_parameters values and options
        self.options = dict([(k,v['default']) for k,v in self.gc_parameters.iteritems()])
        # TODO parsear
        self.options.update(options)

        # Validate option values
        self.validate()

        # Sanitaze values
        self.options["name"] = re.sub(r'\W+', '', self.options["name"])


    def validate(self):
        """ Transforms string on proper types and checks value validity """
        #try:
        #    get_module(self.options['device'])
        #except:
        #    raise SystemError(
        #        "Track {0}: device type {0} doesn't exists.".format(
        #            self.options['name'],self.options['device']))

        for k,v in self.gc_parameters.iteritems():            
            if v['type'] == 'integer':
                if type(self.options[k]) != int: 
                    if not re.search('[^0-9]',self.options[k]):
                        self.options[k] = int(self.options[k])
                    else:
                        raise SystemError(
                            'Parameter "{0}" on {1} must be {2}.'.format(
                                k,type(self).__name__,v['type']))

                if self.options[k] < v['range'][0] or self.options[k] > v['range'][1]:
                    raise SystemError(
                        'Parameter "{0}" on {1} out of range. {2}.'.format(
                            k,type(self).__name__,v['range']))

            if v['type'] == 'float':
                try:
                    self.options[k] = float(self.options[k])
                    if self.options[k] < v['range'][0] or self.options[k] > v['range'][1]:
                        raise SystemError(
                            'Parameter "{0}" on {1} out of range. {2}.'.format(
                                k,type(self).__name__,v['range']))
                except:
                    raise SystemError(
                        'Parameter "{0}" on {1} must be {2}.'.format(
                            k,type(self).__name__,v['type']))

            if v['type'] == 'boolean':
                parse = self.options[k].lower()
                if parse in [True, 'true', 'yes', 1, '1']:
                    self.options[k] = True
                elif parse in [False, 'false', 'no', 0, '0']:
                    self.options[k] = False
                else:
                    raise SystemError(
                        'Parameter "{0}" on {1} must be an accepted {2}.\n{3}. Boolean parser ignores case"'.format(k,type(self).__name__,v['type'],'true, yes, 1, false, no, 0')) 

            if v['type'] == 'flavor' and self.options[k] not in FLAVOR:
                 raise SystemError('{0} is not a valid {1}.\nValid flavors are {2}.'.format(
                         self.options[k],v['type'],FLAVOR)) #

            #TODO add check location tests and check only in bins with location
            #if v['type'] == 'device' and type(self).__name__ != 'GCpulse' and not path.exists(self.options[k]):
            #    raise SystemError('Parameter "{0}" on {1} is not a valid {2}.'.format(
            #            k, type(self).__name__ , v['type']))

            if v['type'] == 'select' and self.options[k] not in v['options']:
                raise SystemError('Parameter "{0}" on {1} must be a valid option.{2}'.format(
                        k,type(self).__name__,v['options'])
                                  ) 

            # TODO validate caps using gst module
            #if v['type'] == 'caps':
            #    try:
            #        caps = gst.caps_from_string(self.options[k])
            #    except:
            #         raise SystemError('Parameter {0} on {1} holds invalid caps'.format(
            #                  k, type(self).__name__)) # TODO Mejorar
            
    
            # TODO Completar

    def set_option_in_pipeline(self, option, element, prop, parse=str):
        element = self.get_by_name(element)
        element.set_property(prop, parse(self.options[option]))

    def set_value_in_pipeline(self, value, element, prop, parse=str):
        element = self.get_by_name(element)
        element.set_property(prop, parse(value))

    def get_display_areas_info(self):
        if self.has_video:
            return ['sink-' + self.options['name']]
        return []

    def get_bins_info(self):
        if not self.options.has_key('mimetype'):
            ext = self.options['file'].split('.')[1].lower()
            self.options['mimetype'] = 'audio/' + ext if self.has_audio and not self.has_video else 'video/' + ext
        return [self.options]

    @classmethod
    def get_gc_parameters(klass):
        ps = {}
        for p in reversed(klass.__mro__):
            ps.update(getattr(p, 'gc_parameters', {}))
        return ps

    @classmethod
    def get_conf_form(self):
        ##TODO necesito GLADE
        pass

