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

import re

from gi.repository import Gst

from galicaster.utils import validator
from galicaster.core import context

logger = context.get_logger()

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
            "description": "Opencast flavor associated to the track",
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
        self.logger = logger
        # Init gc_parameters add Base and Object class
        self.gc_parameters = self.get_gc_parameters()
        path = 'Unknown'
        current_profile = context.get_conf().get_current_profile()
        if current_profile:
            path = current_profile.path
        # Check the profile parameters (*.ini)
        for k in options:
            if k not in self.gc_parameters and k not in ['device', 'active', 'path']:
                logger.warning('The profile parameter "{0}" does not exist. Please check the file {1}'.format(
                        k, path))



        # Init options with default gc_parameters values and options
        self.options = dict([(k,v['default']) for k,v in self.gc_parameters.iteritems()])
        # TODO parsear

        # Validate option values
        for k, v in options.iteritems():
            gc_parameter = None
            if self.gc_parameters.has_key(k):
                gc_parameter = self.gc_parameters[k]
            if v is not None:
                error, self.options[k] = validator.parse_validate(k, v, gc_parameter)

        # Sanitaze values
        self.options["name"] = re.sub(r'\W+', '', self.options["name"])


    def set_option_in_pipeline(self, option, element_name, prop, parse=str):
        element = self.get_by_name(element_name)
        if not element:
            self.logger.error("There isn't an element named {}".format(element_name))
        elif prop == "caps":
            element.set_property(prop, Gst.Caps.from_string(self.options[option]))
        else:
            element.set_property(prop, parse(self.options[option]))


    def set_value_in_pipeline(self, value, element_name, prop, parse=str):
        element = self.get_by_name(element_name)
        if not element:
            self.logger.error("There isn't an element named {}".format(element_name))
        else:
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

    def prepare(self, bus=None):
        pass

    def disable_input(self):
        self.logger.warning("disable_input not implemented")

    def enable_input(self):
        self.logger.warning("enable_input not implemented")

    def disable_preview(self):
        self.logger.warning("disable_preview not implemented")

    def enable_preview(self):
        self.logger.warning("enable_preview not implemented")

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
