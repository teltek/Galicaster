# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/operations/export_to_zip
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
Export to Zip Operation module
"""
import os
import datetime
import tempfile

from galicaster.core import context
from galicaster.mediapackage import serializer
from __init__ import Operation

class ExportToZip(Operation):

    order = ["schedule", "location", "filename" , "use-namespace", "ziptype",]
    show = [ "schedule" ]
    parameters = {
        "schedule": {
            "type": "select",
            "default": "immediate",
            "description": "",
            "options": [ "immediate", "nightly" ]
            },
         "filename": {
            "type": "file",
            "default": "{date}.zip", # TODO use format
            "description": "Zip filename where to save the mediapackage",
            },
         "location": {
            "type": "folder",
            "default": "{export}",#TODO get export folder
            "description": "Location where to save the zip file",
            },
         "use-namespace": {
            "type": "boolean",
            "default": True,
            "description": "Wheter XML namespace is included on metadata files",
            },
         "ziptype": {
            "type": "select",
            "default": "system",
            "description": "Wheter files are zipped via Python or via system zip",
            "options": ["system","native"],
            },
         }
         
    def __init__(self, subtype, options = {}, context=None):
        Operation.__init__(self, "exporttozip", subtype, options, context)

    def configure(self, options={}, is_action=True):

        Operation.configure(self, options, is_action)
        self.date=datetime.datetime.now()
        # TODO use-namespace from conf
        
    def do_perform(self, mp):
        self.options["location"] = self.transform_folder(self.options["location"])
        self.options["filename"] = self.transform_template(self.options["filename"], mp)
        destination = os.path.join(self.options["location"], self.options["filename"])
        # Don't look for duplicates, ingest needs to overwrite files
        self.options["filename"] = os.path.split(destination)[1]
        serializer.save_in_zip(mp, destination, self.options["use-namespace"], 
                               self.options['ziptype'], self.context[0])

    def transform_folder(self, template):

        conf = context.get_conf() # TODO remove or get from worker
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
            '{id}'          : mp.getIdentifier(),
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
