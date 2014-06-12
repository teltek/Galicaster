# -*- coding:utf-8 -*- 
# Galicaster, Multistream Recorder and Player   
#  
#  galicaster/plugins/setuprecording.py
#  
# Copyright (c) 2013, Teltek Video Research <galicaster@teltek.es>  
#  
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of  
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/  
# or send a letter to Creative Commons, 171 Second Street, Suite 300,    
# San Francisco, California, 94105, USA.   
"""
Changes Galicaster default behaviour to show a menu to enter
metadata before starting a manual recording.
"""

from galicaster.core import context
import getpass
from galicaster.utils import series as list_series
from galicaster.classui.metadata import MetadataClass, DCTERMS, EQUIV

import os

from galicaster.utils.i18n import _

#DCTERMS = ["title", "creator", "description", "language", "isPartOf"]
MAPPINGS = { 'user': getpass.getuser() }


def init():
    dispatcher = context.get_dispatcher()
    dispatcher.connect("galicaster-init", post_init)


def post_init(source=None):

    global recorder_ui
    global rec_button
    global metadata

    metadata = {}
    
    # Get a shallow copy of the plugin configuration
    config = context.get_conf().get_section('setuprecording') or {}

    # Get the metadata to setup the mediapackage defaults
    for key, value in config.iteritems():
        final_key = EQUIV.get(key) or key
        if final_key in DCTERMS:
            try:
                metadata[final_key] = value.format(**MAPPINGS)
            except KeyError:
                metadata[final_key] = value

    # Check the special case that series is specified using 'series' rather than 'isPartOf'
    if 'series' in config:
        metadata['isPartOf'] = config['series']

    recorder_ui = context.get_mainwindow().nbox.get_nth_page(0)

    rec_button = recorder_ui.gui.get_object('recbutton')

    rec_button.connect('clicked', on_rec)
    rec_button.handler_block_by_func(recorder_ui.on_rec)
    
def on_rec(button):
    dispatcher = context.get_dispatcher()    
    dispatcher.emit("disable-no-audio")
    global recorder_ui
    global metadata

    mp = recorder_ui.mediapackage
    
    # Add default metadata to the MP
    mp.metadata_episode.update(metadata)
    
    # Check the series
    try:
        del(mp.metadata_episode['isPartOf'])
        mp.metadata_series = list_series.getSeriesbyId(metadata['isPartOf'])['list']
    except (TypeError, KeyError):
        # There was no series specified, so no change was needed
        pass

    series_list = list_series.get_series()

    arguments = { 'package': mp,
                  'series_list': series_list,
                  'title': _("New Recording"),
                  'subtitle': _("New Recording"),
                  'ok_label': _("Start"),
                  }
    
    if len(series_list) <= 1:
        arguments['empty_series_label'] = None
        
    popup = MetadataClass(**arguments)
    
    if popup.return_value == -8:
        recorder_ui.on_rec()
    dispatcher.emit("enable-no-audio")
    
