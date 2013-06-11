1# -*- coding:utf-8 -*-
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
Operation loader for custom operations
"""

import os
import ConfigParser
import nas, export_to_zip, sbs, ingest
from galicaster.core import context

def get_operations():
    folder = "/home/galicaster/src/git/uned2/Galicaster/operations/"   
    operations = []
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if os.path.splitext(filename)[1]=='.ini':
            operations += import_from_file(filepath)
    list_operations = convert_operation(operations)
    return list_operations

    #TODO convert dict into configured operations    

def enqueue_operations(operation, packages):
    for package in packages: # TODO perform them in order
        if operation.schedule.lower() == operation.IMMEDIATE:
            context.get_worker().enqueueJob(operation, package) # package is already on the operation?
        else:
            context.get_worker().nightJob(operation, package)

def import_from_file(filepath):
    parser = ConfigParser.ConfigParser()
    parser.read(filepath)
    sections = parser.sections()
    result = []
    for section in sections:
        result += [dict(parser.items(section))]
    return result

def convert_operation(operations):
    # TODO check parameters
    group = []
    for operation in operations: # TODO check valid section type, name
        theType = None
        name = None
        op = None
        try:
            theType = operation.pop("operation") #TODO check valid type # MUST be type
            name = operation.pop("name")
        except:
            pass
        if theType == "zip":
            op = export_to_zip.ExportToZip(operation)
        elif theType == "nas":
            op = nas.IngestNas(operation)
        elif theType == "sbs":
            op = sbs.SideBySide(operation)
        elif theType == "ingest":
            op = ingest.MHIngest(operation)


        else:
            pass # TODO error, do log
        
        group.append((op,name))
    return group
