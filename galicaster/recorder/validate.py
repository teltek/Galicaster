# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/validate
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

import re
import gst
        
def validate_videopath(value):
    return True, value

def validate_audiopath(value):
    return True, value
    
def validate_selection(value, options): # TODO place appart for all galicaster
    if value not in options['options']:
        return False, value # TODO parse spaces and capital letters
    else:
        return True, value      

def validate_framerate(value):
    if re.match('[0-9]*\/[0-9]*',value):
        return True, value
    else:
        return False, value

def validate_boolean(value):        
    if str(value).lower() in [True, 'true', 'yes', '1' ]:
        return True, True
    elif str(value).lower() in [False, 'false', 'no', '0' ]:
        return True, False
    else:
        return False, value #invaled

def validate_resolution(value):
    """Splits resolution in two parts, lookin for separators , . : x _"""
    try:
        resolution =  [int(a) for a in value.split(re.search('[,.x:]',value).group())]
        return True, resolution
    except:
        return False, value

def validate_gstelement(value):
    try:
        gst.element_factory_make(value)
    except:
        return False,value
    return True, value
