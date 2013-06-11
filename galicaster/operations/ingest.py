# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/operations/operation/ingest
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
Ingest Operation module
"""
import os
import tempfile

from galicaster.core import context

from __init__ import Operation
from export_to_zip import ExportToZip

class MHIngest(Operation):

    order = ["schedule", "use-namespace", "temporal-path"]
    future = ["server","workflow", "workflow-parameters", "username", "password" ]
    show = [ "schedule" ]
    # Workflow
    parameters = {
        "schedule": {
            "type": "select",
            "default": "immediate",
            "description": "",
            "options": [ "immediate", "nightly" ]
            },
        "use-namespace": {
            "type": "boolean",
            "default": True,
            "description": "Wheter XML namespace is included on metadata files",
            },
        "temporal-path": {
            "type": "folder",
            "default": "{temp}",
            "description": "Location wheter to store temporal files",
            },
        }

    future_parameters = { # also hostname
        "server": {
            "type": "list",
            "default": None,
            "description": "A Opencast Matterhorn admin server, port included",
            },
        "workflow": {
            "type": "list",
            "default": None,
            "description": "A workflow available on the designed OC-MH server",
            },
         "workflow-parameters": {
            "type": "text",
            "default": None,
            "description": "Parameters to a OC-MH workflow",
            },
        "username":{
            "type": "text",
            "default": "matterhorn_system_account",
            "description": "Digest user for a matterhorn server",
            },
        "password":{
            "type": "text",
            "default": "CHANGE_ME",
            "description": "Password for the digest user for a matterhorn server",
            },            
        }
        
    def __init__(self, options ={}):
        Operation.__init__(self,"ingest", options)

    def configure(self, options={}, is_action=True):
        """Parameters in options: server, workflow, workflow-parameters, username, password,
        use-namespace, track-flavors, temporal-path."""

        Operation.configure(self, options, is_action)
    
        self.options["temporal-path"] = self.transform_folder(self.options["temporal-path"])
        self.ifile = tempfile.NamedTemporaryFile(dir= self.options["temporal-path"])
        self.options["temporal-path"] = self.ifile.name
        print self.options["temporal-path"]
        # create zip suboperation
        self.export=ExportToZip()
        self.export.configure({"use-namespace": self.options["use-namespace"],
                               "location": os.path.split(self.options["temporal-path"])[0], # TMPfile
                               "filename": os.path.split(self.options["temporal-path"])[1], # TMPfile
                               },
                              is_action=False) 
        # TODO Set NATIVE/SYSTEM zip
        # TODO get user-namespace from legacy conf

    def do_perform(self, mp):
        self.ingest(mp)        

    def ingest(self, mp):
        properties = mp.getOCCaptureAgentProperties()
        try:
            workflow = properties['org.opencastproject.workflow.definition']
        except:
            workflow = None
        for k, v in properties.iteritems():
            if k[0:36] == 'org.opencastproject.workflow.config.':
                parameters[k[36:]] = v

        self.export.perform(mp) # It was defined in configure
        mhclient = context.get_mhclient()
        if mp.manual:
            print mhclient
            mhclient.ingest(self.options["temporal-path"])
        else:
            mhclient.ingest(self.options["temporal-path"], workflow,
                            mp.getIdentifier(), parameters)

        # TODO TODO TODO close file
        self.ifile.close()


    def transform_folder(self, template):

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
