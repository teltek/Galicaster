# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/mediapackage/deserializer
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.


from os import path
from datetime import datetime
from xml.dom import minidom
import json

from galicaster.mediapackage import mediapackage
from galicaster.mediapackage.utils import _checknget, _checkget
from galicaster.mediapackage.utils import _getElementAbsPath

"""
This module allow to obtain a mediapackage object from manifest and other files in a mediapackage directory and the information of a recorded presentation from a mpeg7 file.
"""
def fromXML(xml, logger=None):
    # FIXME: xml could be a file or a path.
    # TODO: if does not exist.
    """
    Gets information from manifest.xml by parsing it. Then tries to get information from galicaster.xml if the file exists.
    At the end calls marshalDublinCore(), a mediaPackage method in which the instance from the Mediapackage class gets the information from series.xml and episode.xml files by parsing them.
    Args:
        xml (str): absolute path of the manifest.xml file.
        logger (Logger): the object that prints all the information, warning and error messages. See galicaster/context/logger.
    Returns:
        Mediapackage: the object that represent a set of records.
    """
    mp_uri = path.dirname(path.abspath(xml))
    mp = mediapackage.Mediapackage(uri = mp_uri)
    manifest = minidom.parse(xml)
    principal = manifest.getElementsByTagName("mediapackage")
    mp.setDuration(principal[0].getAttribute("duration") or 0) # FIXME check if empty and take out patch in listing.populatetreeview
    mp.setIdentifier(principal[0].getAttribute("id"))

    if principal[0].hasAttribute("start"):
        mp.setDate(datetime.strptime(principal[0].getAttribute("start"), '%Y-%m-%dT%H:%M:%S'))

    without_galicaster = False

    galicaster_json = False

    try:
        with open(path.join(mp.getURI(), 'galicaster.json')) as file:
            galicaster_json = json.load(file)
    except IOError:
        if logger:
            logger.warning("The Mediapackage: "+mp.identifier+" : has no galicaster.json file. Trying to load outdated galicaster.xml")
        # Keep The XML read logic for backwards compatibility:
        try:
            galicaster = minidom.parse(path.join(mp.getURI(), 'galicaster.xml'))

            mp.status = int(_checknget(galicaster, "status"))
            for i in galicaster.getElementsByTagName("operation"):
                op = unicode(i.getAttribute("key"))
                status = _checknget(i, "status")
                mp.setOpStatus(op, int(status))
            for i in galicaster.getElementsByTagName("property"):
                op = unicode(i.getAttribute("name"))
                value = _checkget(i)
                mp.properties[op] = unicode(value)
        except IOError:
            if logger:
                logger.error("The Mediapackage: "+mp.identifier+" : has no galicaster.xml or galicaster.json file")
            without_galicaster = True

    if galicaster_json and 'galicaster' in galicaster_json:
        galicaster_json = galicaster_json['galicaster']
        mp.status = galicaster_json['status']
        mp.operations = galicaster_json['operations']
        mp.properties = galicaster_json['properties']

    for etype, tag in mediapackage.MANIFEST_TAGS.items():
        for i in manifest.getElementsByTagName(tag):
            if i.hasAttribute("id"):
                identifier = unicode(i.getAttribute("id"))
            else:
                identifier = None
            uri = _checknget(i, "url")
            flavor = unicode(i.getAttribute("type"))
            mime = _checknget(i, "mimetype")
            duration = _checknget(i, "duration")
            element_path = _getElementAbsPath(uri, mp.getURI())
            ref = unicode(i.getAttribute("ref"))

            tags = []
            for tag_elem in i.getElementsByTagName("tags"):
                tag_text = unicode(_checknget(tag_elem, "tag"))
                tags.append(tag_text)

            if i.hasAttribute("ref"):
                ref = unicode(i.getAttribute("ref"))
            else:
                ref = None
            if not path.exists(element_path):
                raise IOError, "Not exists the element {} in the MP {}".format(element_path, mp.identifier)
            mp.add(element_path, etype, flavor, mime, duration, ref, identifier, tags)

            if uri == 'org.opencastproject.capture.agent.properties' and etype == mediapackage.TYPE_ATTACHMENT:
                mp.manual = False

            if etype == mediapackage.TYPE_TRACK and mp.status == mediapackage.NEW and without_galicaster:
                mp.status = mediapackage.RECORDED

    mp.marshalDublincore()

    # To rewrite the galicaster.xml file with a galicaster.json file
    if not without_galicaster and not galicaster_json:
        from galicaster.mediapackage import serializer
        serializer.save_in_dir(mp)

    return mp
