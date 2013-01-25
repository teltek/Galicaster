# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/__init__
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


import logging

__version__ = '1.2.2'


format = [
    '%(asctime)s',
    '%(levelname)s',
    '%(module)s',
    '%(message)s',
    ]

logging.basicConfig(
    filename = '/var/log/galicaster/galicaster.log',
    filemode = 'a',
    level = logging.INFO,
    format='\t'.join(format),

)
logging.info('galicaster.__version__: %r', __version__)
logging.info('galicaster.__file__: %r', __file__)
