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
Logger Proxy class to use in Galciaster.
"""
import sys
import logging
import getpass

from os import path

class Logger(logging.Logger):
    def __init__(self, log_path, level="DEBUG", rotate=False, use_syslog=False):
        logging.Logger.__init__(self, "galicaster", level)

        formatting = [
            "%(user)s",
            "%(asctime)s",
            "%(levelname)s",
            "%(module)s",
            "%(message)s"]

        if use_syslog:
            from logging.handlers import SysLogHandler
            loghandler = SysLogHandler(address='/dev/log')
            formatting.insert(0, "Galicaster") 
            del(formatting[2]) 
            loghandler.setFormatter(logging.Formatter(" ".join(formatting)))
        elif log_path == None or len(log_path) == 0:
            loghandler = logging.NullHandler()
        else:
            if log_path[0] != "/":
                log_path = path.abspath(path.join(path.dirname(__file__), "..", "..", log_path))
            if rotate:
                from logging.handlers import TimedRotatingFileHandler
                loghandler = TimedRotatingFileHandler(log_path, "midnight")
            else:
                try:
                    loghandler = logging.FileHandler(log_path, "a")
                except IOError:
                    fallback_log_path = path.expanduser('~/.galicaster.log')
                    sys.stderr.write("Error writing in the log in '{0}', using '{1}'\n".format(log_path, fallback_log_path))
                    loghandler = logging.FileHandler(fallback_log_path, "a")

            loghandler.setFormatter(logging.Formatter("\t".join(formatting)))

        self.addFilter(GalicasterFilter())
        self.addHandler(loghandler)




class GalicasterFilter(logging.Filter):
    """
    This filter injects contextual information in the log.
    (Namely, the user running Galicaster)
    """
    CURRENT_USER = getpass.getuser()

    def filter(self, record):
        # Insert the username in a parameter named 'user'
        record.user = GalicasterFilter.CURRENT_USER
        return True
