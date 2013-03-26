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
        group = {}
        for parameter in series['http://purl.org/dc/terms/'].iterkeys():
            try:
                group[parameter] = series['http://purl.org/dc/terms/'][parameter][0]['value']
            except:
                group[parameter] = None
        out[k] = group
        
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
        match = {"id": seriesid, "name": list_series[seriesid]['title'], "list": list_series[seriesid]}
        return match
    except KeyError:
        return None

def getSeriesbyName(seriesname):
    """
    Generate a list with the series value name, shortname and id
    """
    list_series = get_series()
    match = None
    for key,series in list_series.iteritems():
        if series['title'] == seriesname:
            match =  {"id": key, "name": seriesname, "list": list_series[seriesid]}
            break
    return match

def serialize_series(series_list, series_path):
    in_json = json.dumps(series_list)
    if path.isfile(series_path):
        with open(series_path, 'w') as f:
            f.write(in_json)
            f.close()    

def deserialize_series(series_path):
    in_json = json.loads(series_path)
    return in_json
