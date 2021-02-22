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
loaded = []
prefixes = {'galicaster.plugins.': 'Internal',
            'galicaster_plugin_': 'External'}


def init():
    global loaded
    conf = context.get_conf()

    list_plugins = conf.get_section('plugins')
    for plugin, v in list(list_plugins.items()):
        if v.lower() == 'true':
            for prefix in prefixes:
                plugin_type = prefixes[prefix]
                try:
                    name = prefix + plugin
                    __import__(name)
                    sys.modules[name].init()
                    logger.info('{} plugin {} started'.format(plugin_type,
                                                              plugin))
                    loaded.append(name)
                    break
                except Exception as e:
                    if e.msg == 'No module named {}'.format(plugin):
                        logger.warning('{} plugin {} not found'
                                       .format(plugin_type, plugin))
                    else:
                        logger.error('Exception thrown starting plugin {}:'
                                     .format(plugin), exc_info=True)
            else:
                logger.error('Error starting plugin {}'.format(plugin))
        else:
            logger.info('Plugin {0} not enabled in conf'.format(plugin))
