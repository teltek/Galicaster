# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/core/logger
#
# Copyright (c) 2013, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
Logger Proxy class to use in galciaster.
"""

import logging

class Logger(logging.Logger):
    def __init__(self, log_path, level="DEBUG", rotate=False, use_syslog=False):
        logging.Logger.__init__(self, "galicaster", level)

        formatting = [
            "%(asctime)s",
            "%(levelname)s",
            "%(module)s",
            "%(message)s"]

        if log_path == None:
            loghandler = logging.NullHandler()
        elif use_syslog:
            from logging.handlers import SysLogHandler
            loghandler = SysLogHandler(address='/dev/log')
            formatting[0] = "Galicaster"
            loghandler.setFormatter(logging.Formatter(" ".join(formatting)))
        elif rotate:
            from logging.handlers import TimedRotatingFileHandler
            loghandler = TimedRotatingFileHandler(log_path, "midnight")
            loghandler.setFormatter(logging.Formatter("\t".join(formatting)))
        else:
            loghandler = logging.FileHandler(log_path, "a")
            loghandler.setFormatter(logging.Formatter("\t".join(formatting)))


        self.addHandler(loghandler)

