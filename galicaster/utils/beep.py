# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/beep
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


"""
Se genera un pitido usando gstreamer
"""

import logging

import gtk
import gst


def do_beep():
    pipeline = gst.Pipeline()
    src = gst.element_factory_make('audiotestsrc')
    src.set_property('num-buffers', 20) 
    src.set_property('wave', 7)
    sink = gst.element_factory_make('autoaudiosink')
    
    pipeline.add(src, sink)
    src.link(sink)
    pipeline.set_state(gst.STATE_PLAYING)
