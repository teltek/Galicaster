# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/series
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import os
from os import path
from galicaster.core import context
import json

def get_series():
    repo = context.get_repository() 
    mhclient = context.get_mhclient()
    
    try:
        series_json = mhclient.getseries()
        repo.save_attach('series.json', series_json)
    except:
        try:
            series_json = repo.get_attach('series.json').read()
        except:
            series_json = '{"totalCount":"0","catalogs":[]}'

    

    series_json = json.loads(series_json)
    # convert JSON in ARRAY
    out = {}

    for series in series_json['catalogs']:
        k = series['http://purl.org/dc/terms/']['identifier'][0]['value']
        v = series['http://purl.org/dc/terms/']['title'][0]['value']
        out[k] = v

    return out
    
    
def transform(a):
    return a.strip()


def getSeriesbyId(seriesid):
    #TODO
    """
    Generate a list with the series value name, shortname and id
    """
    list_series = get_series()
    try:
        match = {"id": seriesid, "name": list_series[seriesid]}
        return match
    except KeyError:
        return None

def getSeriesbyName(seriesid):
    """
    Generate a list with the series value name, shortname and id
    """
    list_series = get_series()
    inv_map = dict(zip(list_series.values(), list_series.keys()))
    try:
        match = {"id": inv_map[seriesid], "name": seriesid}
        return match
    except KeyError:
        return None

def serialize_series(series_list, series_path):
    in_json = json.dumps(series_list)
    if path.isfile(series_path):
        with open(series_path, 'w') as f:
            f.write(in_json)
            f.close()    

def deserialize_series(series_path):
    in_json = json.loads(series_path)
    return in_json
