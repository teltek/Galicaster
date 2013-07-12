# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/iso639
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

# Based on http://stackoverflow.com/questions/2879856/get-system-language-in-iso-639-3-letter-codes-in-python

from os import path
from galicaster.classui import get_data_dir
import codecs


def get_iso():
    data = path.join(get_data_dir(), 'ISO-639-2_utf-8.txt')
    f = codecs.open(data, 'rb', 'utf-8')    
    D = {}

    for line in f:
        iD = {}
        iD['bibliographic'], iD['terminologic'], iD['alpha2'], \
            iD['english'], iD['french'] = line.strip().split('|')
        D[iD['bibliographic']] = iD
        
        if iD['terminologic']:
            D[iD['terminologic']] = iD

        if iD['alpha2']:
            D[iD['alpha2']] = iD

        for k in iD:
            iD[k] = iD[k] or None
    f.close()
    return D

def get_iso_name(alpha):
    """From an Alpha 2 or 3 returns the name in English """
    
    return get_iso()[alpha]['english'].split(";")[0]

def get_alpha3(alpha):
    """From the Alpha2 return the Alpha3"""
    return get_iso()[alpha]['bibliographic']

def get_alpha2(alpha):
    """From the Alpha3 return the Alpha3"""
    return get_iso()[alpha]['alpha2']
