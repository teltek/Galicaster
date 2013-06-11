# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/operations/sbs
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
Side by side and Picture in picture Operation module
"""
import os
import datetime
import tempfile
import itertools

from galicaster.core import context
from galicaster.utils import sidebyside
from __init__ import Operation

class SideBySide(Operation):

    order = ["schedule", "location", "filename", "layout"]
    show = ["schedule"]
    parameters = {
        "schedule": {
            "type": "select",
            "default": "immediate",
            "description": "",
            "options": [ "immediate", "nightly" ]
            },
        "filename": {
            "type": "filepath",
            "default": "${title}.zip", # TODO use format
            "description": "Zip filename where to save the mediapackage",
            },
         "location": {
            "type": "folderpath",
            "default": "{export}", # TODO use format
            "description": "Location where the resulting file will be exported",
            },
         "layout": {
            "type": "select",
            "default": "sbs",
            "description": "Video composition layout for the side by side output",
            "options": [ "sbs", "pip_screen", "pip_camera" ] # TODO parameters for differnen layouts
            },
         }
         
    def __init__(self, options = {}):
        Operation.__init__(self, "sidebyside", options)

    def configure(self, options={}, is_action=True):

        Operation.configure(self, options, is_action)

        if os.path.splitext(self.options["filename"])[1] != '.mp4':
            self.optionsn["filename"] = self.options["filename"]+'.mp4' # TODO clean . or similar odd carachters
        self.layout = self.options["layout"]
        self.date=datetime.datetime.now()

    def do_perform(self, mp): # TODO log creation

        self.options["location"] = self.transform_folder( self.options["location"], mp) # TODO update options to reflect changes
        self.options["filename"] = self.transform_template( self.options["filename"], mp)
        destination = os.path.join(self.options["location"], self.options["filename"])
        base = destination
        count = itertools.count(2)
        while os.path.exists(destination):
            destination = (base + "_" + str(next(count)))
        self.options["filename"] = os.path.split(destination)[1]
        camera, screen, audio = self.parse_tracks(mp) # TODO move to configure if possible
        sidebyside.create_sbs(destination, camera, screen, audio, self.options["layout"])

    def parse_tracks(self, mp):
        audio = None 
        camera = None
        screen = None
        for track in mp.getTracks():
            if track.getMimeType()[0:5] == 'audio':
                 audio = track.getURI()
            else:
                if track.getFlavor()[0:9] == 'presenter' :
                    camera = track.getURI()
                if track.getFlavor()[0:12] == 'presentation':
                    screen = track.getURI()

        return camera, screen, audio


    def transform_folder(self, template, mp): # TODO refactorize with export and nas

        conf = context.get_conf()
        mappings = {
            '{export}'     : conf.get('basic', 'export') or os.path.expanduser('~'),
            '{user}'       : os.path.expanduser('~'), 
            '{temp}'       :  conf.get('basic', 'tmp') or tempfile.gettempdir(),
            }

        for key,value in mappings.iteritems():
            if template.count(key):
                template = template.replace(key,value)
        template = template.replace(' ','_')
        return template
            

    def transform_template(self, template, mp):
        date = self.date # Operation configuration, better setCreationTime not UTC
        mpcreation = mp.getLocalDate()

        mappings = {
            '{id}'          : mp.identifier,
            '{title}'       : mp.getTitle(), 
            '{series}'      : mp.getSeriesTitle() or "Undefined_Series",
            '{presenter}'   : mp.getCreator() or "Unknow_Presenter",
            '{type}'        : 'M' if mp.manual else 'S',
            '{longtype}'    : 'manual' if mp.manual else 'scheduled',
            '{date}'        : date.replace(microsecond=0).isoformat(),
            '{year}'        : date.strftime('%Y'),
            '{month}'       : date.strftime('%m'),
            '{day}'         : date.strftime('%d'),
            '{hour}'        : date.strftime('%H'),
            '{minute}'      : date.strftime('%M'),
            '{second}'      : date.strftime('%S'),
            '{creation}'    : mpcreation.replace(microsecond=0).isoformat(),
            '{creation_year}'        : mpcreation.strftime('%Y'),
            '{creation_month}'       : mpcreation.strftime('%m'),
            '{creation_day}'         : mpcreation.strftime('%d'),
            '{creation_hour}'        : mpcreation.strftime('%H'),
            '{creation_minute}'      : mpcreation.strftime('%M'),
            '{creation_second}'      : mpcreation.strftime('%S'),            
            }

        for key,value in mappings.iteritems():
            if template.count(key):
                template = template.replace(key,value)
        template = template.replace(' ','_')
        return template
