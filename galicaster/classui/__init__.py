# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/classui/__init__
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.
"""
UI related modules
"""

from os import path

def get_ui_path(ui_file=""):
    """Retrieve the path to the folder where glade UI files are stored.
    If a file name is provided, the path will be for the file
    """

    return path.join(get_data_dir(), "ui", ui_file)

def get_image_path(image_file=""):
    """Retrieve the path to the folder where images files are stored.
    If a file name is provided, the path will be for the file
    """
    return path.join(get_data_dir(), "images", image_file)

def get_data_dir():
    """Retrieve the path to the folder where resource files are stored.
    If a file name is provided, the path will be for the file
    """
    
    return path.abspath(path.join(path.dirname(__file__), "..", "..", "resources"))





