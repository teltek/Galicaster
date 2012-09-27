# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/nautilus
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import logging
import subprocess
import os

logger = logging.getLogger()


def open_folder(path):
    logger.info("Opening folder {0}".format(path))
    #subprocess.check_call(['nautilus', path])
    #subprocess.call(['nautilus', path])
    os.system('xdg-open '+path)
