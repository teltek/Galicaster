# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/operations/operation/nas
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
Ingest NAS Operation module
"""

import os, re
import tempfile, shutil, itertools
import datetime

from __init__ import Operation

class IngestNas(Operation):

    order = [ "schedule", "destination", "attachment", "folder", "include-metadata", "include-attachments" ]
    show = [ "schedule" ]

    parameters = {
        "schedule": {
            "type": "select",
            "default": "immediate",
            "description": "",
            "options": [ "immediate", "nightly" ]
            },
        "destination": {
            "type": "path",
            "default": None,
            "description": "A user mountable NAS location",
            },
        "attachment":{
            "type": "path",
            "default": [],  #["attachment1.zip"]
            "description": "Multiple filepaths to attach to the NAS export operation",
            },
        "folder":{
            "type": "path",
            "default": None,
            "description": "A folder where multiple files to attach are stored",
            },
        "include-metadata":{
            "type": "boolean",
            "default": True, #["attachment1.zip"], 
            "description": "Whether include XML files",
            },
        "include-attachments":{
            "type": "boolean",
            "default": True, #["attachment1.zip"], 
            "description": "Whether include XML files",
            },
        }
        
    def __init__(self, subtype, options = {}, context=None ):
        Operation.__init__(self,"nas", subtype, options, context)

    def configure(self, options={}, is_action=True):
        """Parameters in options: server, workflow, workflow-parameters, username, password,
        use-namespace, track-flavors, temporal-path."""

        Operation.configure(self, options, is_action)

        self.data = []
        if self.options["folder"]:
            self.data += list(self.list_files( self.options["folder"] ))
        if self.options["attachment"]:
            self.data += [self.options["attachment"]] # TODO parse list
        self.date=datetime.datetime.now()

    def perform(self, mp):

        self.location = self.transform_template(self.options["destination"], mp)
        self.get_data(mp)
        Operation.perform(self, mp)

    def do_perform(self, mp):
        self.export_to_nas(self.location, self.data)

    def get_data(self, mp):
        for track in mp.getTracks():
            self.data += [track.getURI()]
        if self.options["include-attachments"]:
            for attach in mp.getAttachments():
                self.data += [attach.getURI()]
        if self.options["include-metadata"]:
            for catalog in mp.getCatalogs():
                self.data += [catalog.getURI()]

    def export_to_nas(self, location, data):
        os.makedirs(location)
        for filepath in data:
            shutil.copy(filepath, location)

    def list_files(self, location):
        filelist = []
        for dirname, dirnames, filenames in os.walk('.'):
            for filename in filenames:
                filelist += [ os.path.join(dirname, filename) ]
        return filelist

    def transform_template(self, template, mp):
        date = self.date
        creation = mp.getLocalDate()

        mappings = {
            '{id}'          : mp.getIdentifier(),
            '{title}'       : mp.getTitle(), 
            '{series}'      : mp.getSeriesTitle() or "Undefined_Series",
            '{presenter}'   : mp.getCreator() or "Unknow_Presenter",
            '{type}'        : 'M' if mp.manual else 'S',
            '{longtype}'    : 'manual' if mp.manual else 'scheduled',
            '{year}'        : date.strftime('%Y'),
            '{month}'       : date.strftime('%m'),
            '{day}'         : date.strftime('%d'),
            '{hour}'        : date.strftime('%H'),
            '{minute}'      : date.strftime('%M'),
            '{second}'      : date.strftime('%S'),
            '{creation_year}'        : creation.strftime('%Y'),
            '{creation_month}'       : creation.strftime('%m'),
            '{creation_day}'         : creation.strftime('%d'),
            '{creation_hour}'        : creation.strftime('%H'),
            '{creation_minute}'      : creation.strftime('%M'),
            '{creation_second}'      : creation.strftime('%S'),
            
            }

        for key,value in mappings.iteritems():
            if template.count(key):
                template = template.replace(key,value)
        template = template.replace(' ','_')
        base = template
        folder_name = template
        
        # Check if folder_name exists
        count = itertools.count(2)
        while os.path.exists(folder_name):
            folder_name = (base + "_" + str(next(count)))

        return folder_name
