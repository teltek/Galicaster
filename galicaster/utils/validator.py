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
import json

from gi.repository import Gst

from galicaster.core import context as gc_context

FLAVOR = ['presenter', 'presentation', 'other']
YES = [True, 'true', 'yes', 'ok', 'si', 'y', 1, '1']
NO = [False, 'false', 'no', 'n', 0, '0']

def validate_track(options, gc_parameters=None, recursive=False):
    """ Transforms string on proper types and checks value validity """

    global_error_msg = None
    options = dict(options)

    if not gc_parameters:
        gc_parameters = get_gc_parameters_from_bin(options['device'])

    current_error = None

    for k, gc_parameter in gc_parameters.iteritems():
        v = None
        if options.has_key(k):
            v = options[k]
        current_error, value = parse_validate(k, v, gc_parameter)
        options[k] = value

        if current_error:
            if global_error_msg:
                global_error_msg = "{} - {}, forced to {}.".format(
                    global_error_msg, current_error, gc_parameter['default'])
            else:
                global_error_msg = "{}, forced to {}.".format(
                    current_error, gc_parameter['default'])

            options[k] = gc_parameter['default']

            current_error = None
    return global_error_msg, options


def get_gc_parameters_from_bin(device):
    mod_name = 'galicaster.recorder.bins.' + device
    __import__(mod_name)
    mod = sys.modules[mod_name]
    Klass = getattr(mod, "GC" + device)

    return Klass.gc_parameters

def check_range(key, value, gc_parameter):
    current_error = None
    if value < gc_parameter['range'][0] or value > gc_parameter['range'][1]:
        value = gc_parameter['default']
        current_error = 'INFO: Parameter "{}" with value {} out of range {}. Forced to {}'.format(
            key, value, gc_parameter['range'], value)
    return current_error, value

def parse_validate(k, option, gc_parameter=None):
    current_error = None
    custom_flavors = gc_context.get_conf().get_list('basic', 'custom_flavors');

    if not gc_parameter:
        return current_error, option

    if option is None:
        # If the value is not set, put the default value
        if gc_parameter.has_key("default") :
            option = gc_parameter['default']

    if option is not None:
        if gc_parameter['type'] == 'integer':
            try:
                option = int(option)
                current_error, option = check_range(k, option, gc_parameter)
            except ValueError as exc:
                current_error = 'INFO: Parameter "{}" with value {} must be {}'.format(k, option, gc_parameter['type'])

        elif gc_parameter['type'] == 'float':
            try:
                option = float(option)
                current_error, option = check_range(k, option, gc_parameter)
            except:
                current_error = 'INFO: Parameter "{}" with value {} must be {}'.format(
                    k, option, gc_parameter['type'])

        elif gc_parameter['type'] == 'hexadecimal':
            try:
                option = int(str(option), 16)
            except Exception as exc:
                current_error = 'INFO: Parameter "{}" with value {} must be {}: {}'.format(
                    k, option, gc_parameter['type'], exc)

        elif gc_parameter['type'] == 'boolean':
            parse = option

            if type(option) == type(''):
                parse = option.lower()
            if parse in YES:
                option = True
            elif parse in NO:
                option = False
            else:
                current_error = 'INFO: Parameter "{}" with value {} must be an accepted {} ({}). Boolean parser ignores case'.format(
                    k, option, gc_parameter['type'],'true, yes, 1, false, no, 0')

        elif gc_parameter['type'] == 'flavor' and option not in FLAVOR + custom_flavors:
            current_error = 'INFO: Parameter "{}" with value {} is not a valid {}. Valid flavors are {}'.format(k, option, gc_parameter['type'], FLAVOR + custom_flavors)

        elif gc_parameter['type'] == 'select' and option not in gc_parameter['options']:
            current_error = 'INFO: Parameter "{}" with value {} must be a valid option {}'.format(k, option, gc_parameter['options'])

        elif gc_parameter['type'] == 'list':
            # If it is not a list try to convert to dict using JSON
            if type(option) is not list:
                try:
                    option = json.loads(option, "utf-8")
                except Exception as exc:
                    current_error = 'INFO: Parameter "{}" with value {} must be {}. {}'.format(
                        k, option, gc_parameter['type'], exc)

            # Check if now it is a list
            if type(option) is not list:
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
    if option is None or current_error and gc_parameter.has_key("default") :
        option = gc_parameter['default']

    return current_error, option
