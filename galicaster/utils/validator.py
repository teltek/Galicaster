# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/validator
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""

"""

import sys
import re
import json

from gi.repository import Gst

#import gst

FLAVOR = ['presenter', 'presentation', 'other']

def validate_track(options, gc_parameters=None, recursive=False):
    """ Transforms string on proper types and checks value validity """

    def set_default():
        # If the value is not set, put the default value
        if v.has_key("default") :
            options[k] = v['default']
        
    #try:
    #    get_module(options['device'])
    #except:
    #    raise SystemError(
    #        "Track {0}: device type {0} doesn't exists.".format(
    #            options['name'],options['device']))

    iteration_error = None
    options = dict(options)

    if not gc_parameters:
        gc_parameters = get_gc_parameters_from_bin(options['device'])

    # Init options with default gc_parameters values and options        
    default_options = dict([(k,v['default']) for k,v in gc_parameters.iteritems()])
    default_options.update(options)
    options = default_options
    
    current_error = None
    global_error_msg = None

    for k,v in gc_parameters.iteritems():
        if not k in options.keys():
            set_default()
            continue
            
        if not options[k] and options[k] is not False and options[k] is not 0:
            set_default()
            continue

        if v['type'] == 'integer':
            if type(options[k]) != int:
                if not re.search('[^0-9]',options[k]):
                    options[k] = int(options[k])
                else:
                    current_error = 'INFO: Parameter "{}" with value {} must be {}'.format(k, options[k], v['type'])

            if options[k] < v['range'][0] or options[k] > v['range'][1]:
                current_error = 'INFO: Parameter "{}" with value {} out of range {}'.format(
                    k, options[k], v['range'])

            
        elif v['type'] == 'float':
            try:
                options[k] = float(options[k])
                if options[k] < v['range'][0] or options[k] > v['range'][1]:
                    current_error = 'INFO: Parameter "{}" with value {} out of range {}'.format(
                        k, options[k], v['range'])
            except:
                current_error = 'INFO: Parameter "{}" with value {} must be {}'.format(
                    k, options[k], v['type'])

                
        elif v['type'] == 'hexadecimal':
            try:
                int(options[k], 16)
            except:
                current_error = 'INFO: Parameter "{}" with value {} must be {}'.format(
                    k, options[k], v['type'])


        elif v['type'] == 'boolean':
            parse = options[k]

            if type(options[k]) == type(''):
                parse = options[k].lower()
            if parse in [True, 'true', 'yes', 1, '1', "True"]:
                options[k] = True
            elif parse in [False, 'false', 'no', 0, '0', "False"]:
                options[k] = False
            else:
                current_error = 'INFO: Parameter "{}" with value {} must be an accepted {} ({}). Boolean parser ignores case'.format(
                    k, options[k], v['type'],'true, yes, 1, false, no, 0')
                                    

        elif v['type'] == 'flavor' and options[k] not in FLAVOR:
            current_error = 'INFO: Parameter "{}" with value {} is not a valid {}. Valid flavors are {}'.format(k, options[k], v['type'], FLAVOR)


        elif v['type'] == 'select' and options[k] not in v['options']:
            current_error = 'INFO: Parameter "{}" with value {} must be a valid option {}'.format(k, options[k], v['options'])

        elif v['type'] == 'list':
            # If it is not a list try to convert to dict using JSON
            if not (type(options[k]) is list):
                try:
                    options[k] = json.loads(options[k], "utf-8")
                except Exception as exc:
                    current_error = 'INFO: Parameter "{}" with value {} must be {}. {}'.format(
                        k, options[k], v['type'], exc)                

            # Check if now it is a list
            if not (type(options[k]) is list):
                if not current_error:
                    current_error = 'INFO: Parameter "{}" with value {} must be {}'.format(
                        k, options[k], v['type'])
            

        elif v['type'] == 'dict':
            # If it is not a dict try to convert to dict using JSON
            if not isinstance(options[k], dict): 
                try:
                    options[k] = json.loads(options[k], "utf-8")
                except Exception as exc:
                    current_error = 'INFO: Parameter "{}" with value {} must be {}. {}'.format(
                        k, options[k], v['type'], exc)

            # Parse dict
            if not isinstance(options[k], dict):
                if not current_error:
                    current_error = 'INFO: Parameter "{}" with value {} must be {}.'.format(
                        k, options[k], v['type'])                
            else:
                iteration_error, options[k] = validate_track(options[k], v['default'], recursive=True)
                current_error = iteration_error


        #TODO add check location tests and check only in bins with location
        #if v['type'] == 'device' and type(self).__name__ != 'GCpulse' and not path.exists(options[k]):
        #    raise SystemError('Parameter "{0}" on {1} is not a valid {2}'.format(
        #            k, type(self).__name__ , v['type']))


        # TODO improve the caps validation
        # https://gstreamer.freedesktop.org/data/doc/gstreamer/head/pwg/html/section-types-definitions.html#table-video-types
        if v['type'] == 'caps':
           try:
               caps = Gst.Caps.from_string(options[k])
               structure = caps.get_structure(0)
               caps_name = structure.get_name()
               
               # Must be a tuple (True, value), it would be false if it is not defined
               # Note that caps like 'video/x-raw,framerate=5/1' does not have height or width but it works anyway
               # if not structure.get_int('height')[0]:
               #     if not current_error:
               #         current_error = 'INFO: Parameter "{}" with value {} must have a height defined.'.format(k, options[k])

               # if not structure.get_int('width')[0]:
               #     if not current_error:
               #         current_error = 'INFO: Parameter "{}" with value {} must be a width defined.'.format(
               #             k, options[k])                

               if not "video" in caps_name and not "image" in caps_name:
                   if not current_error:
                       current_error = 'INFO: Parameter "{}" with value {} must be of type video or image.'.format(
                           k, options[k])                
                                        
           except Exception as exc:
               current_error = 'INFO: Parameter "{}" with value {} must be valid caps. {}'.format(
                   k, options[k], exc)                

            
        # If the value is not set, put the default value
        if options[k] is None and v.has_key("default") :
            options[k] = v['default']

        if current_error:
            if not recursive:
                if global_error_msg:
                    global_error_msg = "{} - {}, forced to {}.".format(
                        global_error_msg, current_error, v['default'])
                else:
                    global_error_msg = "{}, forced to {}.".format(
                        current_error, v['default'])

                if not iteration_error:
                    options[k] = v['default']

            else:
                options[k] = v['default']
                global_error_msg = current_error

            current_error = None
            

    return global_error_msg, options


def get_gc_parameters_from_bin(device):
    mod_name = 'galicaster.recorder.bins.' + device
    __import__(mod_name)
    mod = sys.modules[mod_name]
    Klass = getattr(mod, "GC" + device)

    return Klass.gc_parameters
    

