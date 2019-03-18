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

# LEVELS:
# -------
#
# DEBUG     Detailed information, typically of interest only when diagnosing problems.
# INFO      Confirmation that things are working as expected.
# WARNING   An indication that something unexpected happened, or indicative of some problem in the near future (e.g. ‘disk space low’). The software is still working as expected.
# ERROR     Due to a more serious problem, the software has not been able to perform some function.
# CRITICAL  A serious error, indicating that the program itself may be unable to continue running.
#
# Please use these levels consistently when logging information.
#

"""
Logger Proxy class to use in Galicaster.
"""
import os
import sys
import logging
import getpass

class Logger(logging.Logger):
    def __init__(self, log_path, level="DEBUG", rotate=False, use_syslog=False):
        logging.Logger.__init__(self, "galicaster", level)

        self.log_path = log_path
        formatting = [
            "%(user)s",
            "%(asctime)s",
            "%(levelname)s",
            "%(pathname)s",
            "%(message)s"]

        if use_syslog:
            from logging.handlers import SysLogHandler
            loghandler = SysLogHandler(address='/dev/log')
            formatting.insert(0, "Galicaster")
            del(formatting[2])
            loghandler.setFormatter(logging.Formatter(" ".join(formatting)))
        elif self.log_path is None or len(self.log_path) == 0:
            loghandler = logging.NullHandler()
        else:
            if self.log_path[0] != "/":
                self.log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", self.log_path))
            if rotate:
                from logging.handlers import TimedRotatingFileHandler
                loghandler = TimedRotatingFileHandler(self.log_path, "midnight")
            else:
                try:
                    loghandler = logging.FileHandler(self.log_path, "a")
                except IOError:
                    self.log_path = os.path.expanduser('~/.galicaster.log')
                    sys.stderr.write("Error writing in the log in '{0}', using '{1}'\n".format(self.log_path, self.log_path))
                    loghandler = logging.FileHandler(self.log_path, "a")

            loghandler.setFormatter(logging.Formatter("\t".join(formatting)))

        self.addFilter(GalicasterFilter())
        self.addHandler(loghandler)


    def get_path(self):
        return self.log_path


class GalicasterFilter(logging.Filter):
    """
    This filter injects contextual information in the log.
    (Namely, the user running Galicaster)
    """
    CURRENT_USER = getpass.getuser()

    def filter(self, record):
        # Insert the username in a parameter named 'user'
        record.user = GalicasterFilter.CURRENT_USER

        pathname = record.pathname
        if pathname.find('galicaster/') > -1:
            record.pathname = "/".join(os.path.splitext(pathname)[0].split("/")[-2:])

        return True


