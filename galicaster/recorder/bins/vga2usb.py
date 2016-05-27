# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/bins/vga2usb
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

from galicaster.core import context
from galicaster.recorder.bins import epiphan
#from galicaster.recorder import module_register

logger = context.get_logger()


class GCvga2usb(epiphan.GCepiphan):

    def __init__(self, options={}): 
        raise Exception("Not implemented. Using gst 0.10")

        logger.error("This bin has been renamed to 'epiphan' and is only provided for compatibility. Use epiphan instead")
        epiphan.GCepiphan.__init__(self, options)

#module_register(GCvga2usb, 'vga2usb')
