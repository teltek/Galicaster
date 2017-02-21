#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#      setup.py
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


from distutils.core import setup
import galicaster


setup(
    name = 'galicaster',
    url = 'http://galicaster.org',
    version = galicaster.__version__,
    author = 'Héctor Canto, Rubén González',
    author_email = 'galicaster@teltek.es',
    description = 'Galicaster, multistream recorder and player',
    license = 'NonCommercial-ShareAlike 3.0 Unported License',
    packages=[
        'galicaster',
        'galicaster.player',
        'galicaster.recorder',
        'galicaster.recorder.bins',
        'galicaster.scheduler',
        'galicaster.core',
        'galicaster.classui',
        'galicaster.classui.elements',
        'galicaster.mediapackage',
        'galicaster.utils',
        'galicaster.plugins',
        ],
    requires=["pycurl", "icalendar"],

    data_files=[
        ('/usr/bin', ['docs/autostart/galicaster']), # Shell launcher
        ('/usr/share/applications', ['docs/autostart/galicaster.desktop']), # Unity launcher
        ('/usr/share/icons/hicolor/scalable/apps/', ['docs/autostart/galicaster.svg',]),#Icons
        ('/usr/share/icons/hicolor/16x16/apps/', ['docs/icons/16x16/galicaster.png']),
        ('/usr/share/icons/hicolor/22x22/apps/', ['docs/icons/22x22/galicaster.png']),
        ('/usr/share/icons/hicolor/24x24/apps/', ['docs/icons/24x24/galicaster.png']),
        ('/usr/share/icons/hicolor/32x32/apps/', ['docs/icons/32x32/galicaster.png']),
        ('/usr/share/icons/hicolor/36x36/apps/', ['docs/icons/36x36/galicaster.png']),
        ('/usr/share/icons/hicolor/48x48/apps/', ['docs/icons/48x48/galicaster.png']),
        ('/usr/share/icons/hicolor/64x64/apps/', ['docs/icons/64x64/galicaster.png']),
        ('/usr/share/icons/hicolor/72x72/apps/', ['docs/icons/72x72/galicaster.png']),
        ('/usr/share/icons/hicolor/96x96/apps/', ['docs/icons/96x96/galicaster.png']), 
        ('/usr/share/icons/hicolor/128x128/apps/', ['docs/icons/128x128/galicaster.png']), 
        ('/usr/share/icons/hicolor/192x192/apps/', ['docs/icons/192x192/galicaster.png']), 
        ('/usr/share/icons/hicolor/256x256/apps/', ['docs/icons/256x256/galicaster.png']),
        ],

)
