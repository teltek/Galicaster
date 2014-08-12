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
Beep generator using Gstreamer
"""
from gi.repository import Gst
Gst.init(None)

def do_beep():
    pipeline = Gst.Pipeline.new()
    src = Gst.ElementFactory.make("audiotestsrc", "source")
    src.set_property('num-buffers', 20) 
    src.set_property('wave', 7)
    sink = Gst.ElementFactory.make("autoaudiosink", "sink")
    pipeline.add(src)
    pipeline.add(sink)
    src.link(sink)
    pipeline.set_state(Gst.State.PLAYING)

