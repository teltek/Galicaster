# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/systemcalls
#
# Copyright (c) 2016, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import subprocess

def execute(command=[], logger=None, logaserror=True):
    level = 40 if logaserror else 10
    if command:
        try:
            proc = subprocess.check_output(command, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as exc:
            logger and logger.log(level, "CalledProcessError trying to execute {}: {}".format(command, exc))
            return False
        except Exception as exc:
            logger and logger.log(level, "Error trying to execute {}: {}".format(command, exc))
            return False
        
    return True


def write_dconf_settings(settings={}, logger=None, logaserror=False):
    for key, value in settings.iteritems():
        execute(["dconf", "write", key, value], logger, logaserror)
