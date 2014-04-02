# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/__init__
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import sys
from galicaster.core import context

logger = context.get_logger()

def init():
    conf = context.get_conf()

    list_plugins = conf.get_section('plugins')
    for plugin, v in list_plugins.iteritems():
        if v.lower() == 'true':
            try:
                name = 'galicaster.plugins.' + plugin
                __import__(name)
                sys.modules[name].init()
                logger.info('Plugin {0} started'.format(plugin))
            except:
                logger.error('Error starting plugin {0}'.format(plugin))
        else:
            logger.debug('Plugin {0} not enabled in conf'.format(plugin))
            
