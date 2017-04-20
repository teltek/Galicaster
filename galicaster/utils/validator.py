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
import ast

from gi.repository import Gst

#import gst

FLAVOR = ['presenter', 'presentation', 'other']


def validate_track(options, gc_parameters=None, recursive=False):
    """ Transforms string on proper types and checks value validity """

    def set_default():
        # If the value is not set, put the default value
        if v.has_key("default") :
            options[k] = parse_automatic(v['default'])

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
    default_options = dict([(k,parse_automatic(v['default'])) for k,v in gc_parameters.iteritems()])

    for k, v in options.iteritems():
        default_options[k] = parse_automatic(v)

    options = default_options.copy()

    current_error = None
    global_error_msg = None

    for k,v in gc_parameters.iteritems():
        current_error, value = parse_validate(k, options[k], v)
        options[k] = value

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


def parse_validate(k, option, gc_parameter=None):
    current_error = None

    if not gc_parameter:
        return current_error, option

    if not option and option is not False and option is not 0:
        # If the value is not set, put the default value
        if gc_parameter.has_key("default") :
            option = parse_automatic(gc_parameter['default'])
        return current_error, option

    if gc_parameter['type'] == 'integer':
        if type(option) != int:
            if not re.search('[^0-9]',option):
                option = int(option)
            else:
                current_error = 'INFO: Parameter "{}" with value {} must be {}'.format(k, option, gc_parameter['type'])

        if option < gc_parameter['range'][0] or option > gc_parameter['range'][1]:
            current_error = 'INFO: Parameter "{}" with value {} out of range {}'.format(
                k, option, gc_parameter['range'])


    elif gc_parameter['type'] == 'float':
        try:
            option = float(option)
            if option < gc_parameter['range'][0] or option > gc_parameter['range'][1]:
                current_error = 'INFO: Parameter "{}" with value {} out of range {}'.format(
                    k, option, gc_parameter['range'])
        except:
            current_error = 'INFO: Parameter "{}" with value {} must be {}'.format(
                k, option, gc_parameter['type'])


    elif gc_parameter['type'] == 'hexadecimal':
        try:
            int(option)
        except Exception as exc:
            current_error = 'INFO: Parameter "{}" with value {} must be {}: {}'.format(
                k, option, gc_parameter['type'], exc)


    elif gc_parameter['type'] == 'boolean':
        parse = option

        if type(option) == type(''):
            parse = option.lower()
        if parse in [True, 'true', 'yes', 1, '1', "True"]:
            option = True
        elif parse in [False, 'false', 'no', 0, '0', "False"]:
            option = False
        else:
            current_error = 'INFO: Parameter "{}" with value {} must be an accepted {} ({}). Boolean parser ignores case'.format(
                k, option, gc_parameter['type'],'true, yes, 1, false, no, 0')


    elif gc_parameter['type'] == 'flavor' and option not in FLAVOR:
        current_error = 'INFO: Parameter "{}" with value {} is not a valid {}. Valid flavors are {}'.format(k, option, gc_parameter['type'], FLAVOR)


    elif gc_parameter['type'] == 'select' and option not in gc_parameter['options']:
        current_error = 'INFO: Parameter "{}" with value {} must be a valid option {}'.format(k, option, gc_parameter['options'])

    elif gc_parameter['type'] == 'list':
        # If it is not a list try to convert to dict using JSON
        if not (type(option) is list):
            try:
                option = json.loads(option, "utf-8")
            except Exception as exc:
                current_error = 'INFO: Parameter "{}" with value {} must be {}. {}'.format(
                    k, option, gc_parameter['type'], exc)

        # Check if now it is a list
        if not (type(option) is list):
            if not current_error:
                current_error = 'INFO: Parameter "{}" with value {} must be {}'.format(
                    k, option, gc_parameter['type'])


    elif gc_parameter['type'] == 'dict':
        # If it is not a dict try to convert to dict using JSON
        if not isinstance(option, dict):
            try:
                option = json.loads(option, "utf-8")
            except Exception as exc:
                current_error = 'INFO: Parameter "{}" with value {} must be {}. {}'.format(
                    k, option, gc_parameter['type'], exc)

        # Parse dict
        if not isinstance(option, dict):
            if not current_error:
                current_error = 'INFO: Parameter "{}" with value {} must be {}.'.format(
                    k, option, gc_parameter['type'])
        # else:
        #     iteration_error, options[k] = validate_track(options[k], v['default'], recursive=True)
        #     current_error = iteration_error


    #TODO add check location tests and check only in bins with location
    #if v['type'] == 'device' and type(self).__name__ != 'GCpulse' and not path.exists(options[k]):
    #    raise SystemError('Parameter "{0}" on {1} is not a valid {2}'.format(
    #            k, type(self).__name__ , v['type']))


    # TODO improve the caps validation
    # https://gstreamer.freedesktop.org/data/doc/gstreamer/head/pwg/html/section-types-definitions.html#table-video-types
    elif gc_parameter['type'] == 'caps':
       try:
           caps = Gst.Caps.from_string(option)
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
                       k, option)

       except Exception as exc:
           current_error = 'INFO: Parameter "{}" with value {} must be valid caps. {}'.format(
               k, option, exc)


    # If the value is not set, put the default value
    if option is None and gc_parameter.has_key("default") :
        option = gc_parameter['default']

    return current_error, option

def parse_automatic(value):
    # Parses from string to integer, float, boolean... If not returns the string
    try:
        return ast.literal_eval(value)
    except:
        return value
    return value
