# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/mediainfo
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


"""
Get information about audio/video files.
"""
import gst

from gst.pbutils import Discoverer


def get_duration(path):
    d = Discoverer(gst.SECOND)
    info = d.discover_uri('file://' + path)
    return info.get_duration() / gst.SECOND

