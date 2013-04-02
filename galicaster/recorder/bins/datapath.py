# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/bins/datapath
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

from galicaster.recorder.bins import v4l2
from galicaster.recorder import module_register


class GCdatapath(v4l2.GCv4l2):

    is_pausable = False

    def __init__(self, options={}):
        v4l2.GCv4l2.__init__(self, options)

module_register(GCdatapath, 'datapath')
