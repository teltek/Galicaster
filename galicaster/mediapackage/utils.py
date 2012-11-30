# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/mediapackage/utils
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
ConfigParser.ConfigParser not in valida to read no section ini file.
"""

from os import path
import ConfigParser

class FakeSecHead(object):
    def __init__(self, fp):
        self.fp = fp
        self.sechead = '[asection]\n'

    def readline(self):
        if self.sechead:
            try: return self.sechead
            finally: self.sechead = None
        else: 
            return self.fp.readline()


def read_ini(f):
    c = ConfigParser.ConfigParser()
    c.optionxform = str # To avoid lower in INI keys (trimHold no trimhold)
    c.readfp(FakeSecHead(open(f)))
    return c.items('asection')


def _getElementAbsPath(name, base_path):
    if path.isabs(name):
        return name
    else:
        return path.join(base_path, name)
        

def _checkget(element): 
    try:
        sout = element.firstChild.wholeText.strip().strip("\n")
    except AttributeError:
        sout = ''
    return sout


def _checknget(archive, name): 
    if archive.getElementsByTagName(name).length != 0:
        try:
            sout = _checkget(archive.getElementsByTagName(name)[0])
        except AttributeError:
            sout = ''
        return sout




