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


from galicaster.core import context
from galicaster.utils.systemcalls import execute

logger = context.get_logger()

def open_folder(path):
    logger.info("Opening folder {0}".format(path))
    return_code = execute(['xdg-open', '{}'.format(path)], logger)
    return return_code
