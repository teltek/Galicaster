# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/gstremaer
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import weakref

class WeakMethod(object):

    def __init__(self, inst, method_name):
        if not callable(getattr(inst, method_name)):
            raise TypeError(
                '{!r} attribute is not callable'.format(method_name)
            )
        self.proxy = weakref.proxy(inst)
        self.method_name = method_name

    def __call__(self, *args):
        try:
            method = getattr(self.proxy, self.method_name)
        except ReferenceError:
            return
        return method(*args)
