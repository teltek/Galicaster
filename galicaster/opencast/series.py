# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/opencast/series
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
from galicaster.mediapackage.mediapackage import Catalog
import json
import getpass


NAMESP = 'http://purl.org/dc/terms/'
DISALLOWED_QUERIES = [ 'q', 'edit', 'sort', 'startPage', 'count', 'default' ]
RESULTS_PER_PAGE = 500
MAPPINGS = { 'user': getpass.getuser() }


def get_series():
    repo = context.get_repository()
    ocservice = context.get_ocservice()

    # Import the 'series' section as a dictionary
    series_conf = context.get_conf().get_section('series')

    # Init 'queries' dictionary
    queries = {'offset': 0, 'limit': RESULTS_PER_PAGE}

    if not ocservice.net:
        series_list = load_series_from_file()
        return series_list

    # Filter out keys that do not refer to a certain series property
    # Also, substitute any placeholder(s) used to filter the series
    # TODO Currently the only placeholder is {user}
    for key in list(series_conf.keys()):
        if key not in DISALLOWED_QUERIES:
            try:
                queries[key] = series_conf[key].format(**MAPPINGS)
            except KeyError:
                # If the placeholder does not exist, log the issue but ignore it
                # TODO Log the exception
                pass

    try:
        series_list = []
        check_default = True

        series_total = int(ocservice.client.countSeries())

        for i in range(0,series_total,RESULTS_PER_PAGE):
            queries['offset']=i
            series_json = json.loads(ocservice.client.getseries(**queries))

            if (int(series_json['count'])==0):
                break

            for serie in series_json['results']:
                try:
                    series_list.append(parse_json_series(serie))
                except KeyError:
                    # Ignore ill-formated series
                    pass

        # Check the default series is present, otherwise query for it
        # if 'default' in series_conf and check_default and series_conf['default'] not in dict(series_list):
        #     check_default = False
        #         queries = { "seriesId": series_conf['default'] }
        #     else:
        #             break
        #     else:
        #         queries['startPage'] += 1

        repo.save_attach('series.json', json.dumps(series_list))

    except (ValueError, IOError, RuntimeError, AttributeError):
        #TODO Log the exception
        series_list = load_series_from_file()

    return series_list

def load_series_from_file():
    try:
        series_list = json.load(repo.get_attach('series.json'))
    except (ValueError, IOError):
        #TODO Log the exception
        series_list = []

def parse_json_series(json_series):
    series = {}
    #{"identifier": "2886ab13-e292-4272-9361-7d055bf6c14c", "created": "2019-12-02T07:09:26Z", "title": "18/19 Better Lives"}]
    try:
        series['identifier'] = json_series['id']
        series['created'] = json_series['creation_date']
        series['title'] = json_series['title']
    except (KeyError, IndexError):
        # Ignore non-existant items
        # TODO Log the exception
        pass
    return (series['identifier'], series)


def transform(a):
    return a.strip()


def get_default_series():
    return context.get_conf().get('series', 'default')


def filterSeriesbyId(list_series, seriesid):
    """
    Generate a list with the series value name, shortname and id
    """
    for element in list_series:
        if seriesid and seriesid in element[1]["identifier"]:
            try:
                match = {"id": seriesid, "name": element[1]["title"], "list": element[1]}
                return match
            except Exception:
                return None


def getSeriesbyId(seriesid):
    #TODO
    """
    Generate a list with the series value name, shortname and id
    """
    list_series = dict(get_series())
    try:
        match = {"id": seriesid, "name": list_series[seriesid]['title'], "list": list_series[seriesid]}
        return match
    except Exception:
        return None


def getSeriesbyName(seriesname):
    """
    Generate a list with the series value name, shortname and id
    """
    list_series = dict(get_series())
    match = None
    for key,series in list(list_series.items()):
        if series['title'] == seriesname:
            match =  {"id": key, "name": seriesname, "list": list_series[key]}
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


def setSeriebyName(mp, seriesname):
    """
    Put the serie by the name in the mediapackage
    """
    setSerie(mp, getSeriesbyName(seriesname))

def setSeriebyId(mp, seriesname):
    """
    Put the serie by the id in the mediapackage
    """
    setSerie(mp, getSeriesbyId(seriesname))

def setSerie(mp, series_list):
    """
    Put the serie received in the mediapackage
    """
    if series_list:
        mp.setSeries(series_list['list'])
        if not mp.getCatalogs("dublincore/series") and mp.getURI():
            new_series = Catalog(path.join(mp.getURI(),"series.xml"),mimetype="text/xml",flavor="dublincore/series")
            mp.add(new_series)
    else:
        mp.setSeries(None)
        catalog= mp.getCatalogs("dublincore/series")
        if catalog:
            mp.remove(catalog[0])
