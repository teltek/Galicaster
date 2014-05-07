# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/readable
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import datetime

from galicaster.core import context
from galicaster.utils.i18n import _

logger = context.get_logger()

EXP_STRINGS = [ (0, 'B'), (10, 'KB'),(20, 'MB'),(30, 'GB'),(40, 'TB'), (50, 'PB')]

def size(value):
    """ Print sizes in human readable format (e.g., 1K 234M 2G)"""
    num = float(value)
    i = 0
    rounded_val = 0
    while i+1 < len(EXP_STRINGS) and num >= (2 ** EXP_STRINGS[i+1][0]):
        i += 1
        rounded_val = round(float(num) / 2 ** EXP_STRINGS[i][0], 2)

    resultado = '%s %s' % (rounded_val, EXP_STRINGS[i][1])
    return resultado


def date(iso, style="%d-%m-%Y %H:%M"):
    """ Transform from an isoformat datetime to a defined style text"""
    date = datetime.datetime.strptime(iso, '%Y-%m-%dT%H:%M:%S')
    return date.strftime(style)


def time(value):
    """ Generates date hout:minute:seconds from seconds """	
    seconds=int(value)
    return "{0:2d}:{1:02d}:{2:02d}".format(seconds/3600,(seconds%3600)/60,seconds%60) if seconds>3599 else "{0:2d}:{1:02d}".format((seconds%3600)/60,seconds%60)


def long_time(timedif):
    """ Take a timedelta and return it formatted"""              
    if timedif < datetime.timedelta(0,300): # 5 minutes tops
        formatted = "{minutes:02d}:{seconds:02d}".format( 
            minutes = timedif.seconds // 60, 
            seconds = timedif.seconds % 60 )
    elif timedif < datetime.timedelta(1,0): # 24 hours
        formatted = "{hours:02d}:{minutes:02d}:{seconds:02d}".format(
            hours =  timedif.days*24 + timedif.seconds // 3600, 
            minutes = timedif.seconds % 3600 // 60 ,
            seconds = timedif.seconds % 60)
    else: # days
        today = datetime.datetime.now()
        then = today + timedif
        dif = then.date() - today.date()
        singular = _("day")
        plural = _("days")
        formatted = "{days_number} {word}".format(
            days_number =  dif.days,
            word = plural if dif.days > 1 else singular)

    return formatted


def list(listed):
    """ Generates a string of items from a list, separated by commas """
    if not len(listed):
        #logger.warn("Transforming empty list")
        return ""
    else:
        return  ", ".join(listed)

    
