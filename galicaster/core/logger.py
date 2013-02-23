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
    def __init__(self, log_path, level="DEBUG", rotate=False):
        logging.Logger.__init__(self, "galicaster", level)

        if log_path == None:
            loghandler = logging.NullHandler()
        elif rotate:
            from logging.handlers import TimedRotatingFileHandler
            loghandler = TimedRotatingFileHandler(log_path, "midnight")
        else:
            loghandler = logging.FileHandler(log_path, "a")

        format = [
            "%(asctime)s",
            "%(levelname)s",
            "%(module)s",
            "%(message)s"]

        formatter = logging.Formatter("\t".join(format))
        loghandler.setFormatter(formatter)
        self.addHandler(loghandler)

