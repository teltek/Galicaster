# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/mediapackage/serializer
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.


# TODO:
# * metadata dict in mediapackage *33
import json
import os
import zipfile
from datetime import datetime
from datetime import timedelta
# from os import system
from xml.dom import minidom
import subprocess

DCTERMS = ['title', 'creator', 'isPartOf', 'description', 'subject',
           'language', 'contributor', 'created', 'temporal']

SERIES_FILE="series.xml"
ziptype = "system" # system,native

"""
This module saves all the information of a mediapackage object into the different XML files:
    manifest.xml
    episode.xml
    galicaster.xml
    series.xml
It also allows to save a recorded presentation information into a mpeg7 file, to zip the mediapackage directory andto obtain the information of the manifest in JSON format.
"""
def save_in_dir(mp, logger=None, directory=None):
    """Calls the necessary functions in order to obtain the content of the different xml files in the mediapackage directory.
    Then writes this strings in the approprite files.
    Args:
        mp (Mediapackage): the mediapackage with the information to be serialized.
        logger (Logger): the object that prints all the information, warning and error messages. See galicaster/context/logger.
        directory (str): mediapackage directory.
    """
    if not directory:
        assert os.path.isdir(mp.getURI())
    # FIXME use catalog to decide what files to modify or create

    # check if series should be added to the catalog

    # Episode **3
    m2 = open(os.path.join(directory or mp.getURI(), 'episode.xml'), 'w')
    m2.write(set_episode(mp)) #FIXME
    m2.close()

    # Galicaster properties
    m = open(os.path.join(directory or mp.getURI(), 'galicaster.json'), 'w')
    m.write(set_properties(mp))
    m.close()
    try:
        # Pythonically remove old galicaster.xml file
        os.remove(os.path.join(directory or mp.getURI(), 'galicaster.xml'))
    except OSError: # For python > 3.3, use with suppress(FileNotFoundError):
        pass

    # Series
    if mp.getSeriesIdentifier != None:
        # Create or modify file
        m3 = open(os.path.join(directory or mp.getURI(), SERIES_FILE), 'w')
        m3.write(set_series(mp,logger)) #FIXME
        m3.close()

    # Manifest
    m = open(os.path.join(directory or mp.getURI(), 'manifest.xml'), 'w')
    m.write(set_manifest(mp))  ##FIXME
    m.close()


def save_native_zip(mp, loc, use_namespace=True, logger=None):
    """Saves in ZIP file using python module.
    Args:
        mp (Mediapackage): mediapackage that is going to be saved in ZIP.
        loc (str or file-like obj): the path of a file (if string) or the file.
        use_namespace (bool): true if the manifest attribute xmlns has 'http://mediapackage.opencastproject.org' value. False otherwise.
        logger (Logger): the object that prints all the information, warning and error messages. See galicaster/context/logger.
    """
    if logger:
        logger.debug("Using Native Zip")
    z= zipfile.ZipFile(loc,'w',zipfile.ZIP_STORED,True)
    # store only (DEFAULT)

    # manifest
    z.writestr('manifest.xml', set_manifest(mp, use_namespace))

    # episode (fist persist episode)
    m2 = open(os.path.join(mp.getURI(), 'episode.xml'), 'w')
    m2.write(set_episode(mp))
    m2.close()

    for catalog in mp.getCatalogs():
        if os.path.isfile(catalog.getURI()):
            z.write(catalog.getURI(), os.path.basename(catalog.getURI()))

    # tracks
    for track in mp.getTracks():
        if os.path.isfile(track.getURI()):
            z.write(track.getURI(), os.path.basename(track.getURI()))

    for attach in mp.getAttachments():
        if os.path.isfile(attach.getURI()):
            z.write(attach.getURI(), os.path.basename(attach.getURI()))

    # FIXME other elements
    z.close()

def save_system_zip(mp, loc, use_namespace=True, logger=None):
    """Saves the mediapackage in a zip file using system's zip command.
    Args:
        mp (mediapackage): mediapackage that is going to be saved in ZIP.
        loc (str or file-like obj): the path of a file (if string) or the file.
        use_namespace (bool): true if the manifest attribute xmlns has 'http://mediapackage.opencastproject.org' value. False otherwise.
        logger (Logger): the object that prints all the information, warning and error messages. See galicaster/context/logger.
    """
    if logger:
        logger.debug("Using System Zip")

    tmp_file = 'manifest.xml'
    m = open(tmp_file,'w')
    m.write(set_manifest(mp, use_namespace))
    m.close()

    # episode (fist persist episode)
    m2 = open(os.path.join(mp.getURI(), 'episode.xml'), 'w')
    m2.write(set_episode(mp))
    m2.close()

    files = [tmp_file]

    #catalogs
    for catalog in mp.getCatalogs():
        if os.path.isfile(catalog.getURI()):
            files += [catalog.getURI()]

    # tracks
    for track in mp.getTracks():
        if os.path.isfile(track.getURI()):
            files += [track.getURI()]

    for attach in mp.getAttachments():
        if os.path.isfile(attach.getURI()):
            files += [attach.getURI()]

    # FIXME other elements

    loc = loc if type(loc) in [str,str] else loc.name
    command = 'zip -j0 "'+loc + '" "'+'" "'.join(files) + '"'
    # system('zip -j0 "'+loc + '" "'+'" "'.join(files) + '" >/dev/null')
    # if os.path.isfile(loc+".zip"): # WORKARROUND to eliminate automatic extension .zip
    #     os.rename(loc+".zip",loc)

    try:
        # FIXME: Use execute from galicaster.utils.systemcalls
        subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        if os.path.isfile(loc+".zip"): # WORKARROUND to eliminate automatic extension .zip
            os.rename(loc+".zip",loc)

    except subprocess.CalledProcessError as e:
        raise Exception("Error trying to create ZIP for MP {}: {}".format(mp.getIdentifier(), e.output.replace('\n', ' ')))
    except Exception as exc:
        raise Exception("Error trying to create ZIP for MP {}: {}".format(mp.getIdentifier(), exc))

    os.remove(tmp_file)

if ziptype == "system":
    save_in_zip = save_system_zip
else:
    save_in_zip = save_native_zip

def set_properties(mp):
    """Creates the string for galicaster properties.
    Args:
        mp (mediapackage): the mediapackage whose galicaster properties are going to be serialized.
    Returns:
        Str: serialized galicaster properties.
    """
    galicaster_json = {
        'galicaster':{
            'status': mp.status,
            'operations': mp.operations,
            'properties': mp.properties,
        }
    }

    return json.dumps(galicaster_json, sort_keys=True, indent=4, separators=(',', ': '))

def set_manifest(mp, use_namespace=True):
    """Creates the manifest xml.
    Args:
        mp (mediapackage): the mediapackage whose manifest is going to be created.
        use_namespace (bool): true if the manifest attribute xmlns has 'http://mediapackage.opencastproject.org' value. False otherwise.
    Returns:
        Str: content of the manifest.xml .
    """
    doc = minidom.Document()
    xml = doc.createElement("mediapackage")
    if use_namespace:
        xml.setAttribute("xmlns", "http://mediapackage.opencastproject.org")
    xml.setAttribute("id", mp.getIdentifier())
    xml.setAttribute("start", mp.getDate().isoformat())
    if mp.getDuration() != None:
        xml.setAttribute("duration", str(mp.getDuration()))

    doc.appendChild(xml)
    media = doc.createElement("media")
    xml.appendChild(media)
    metadata = doc.createElement("metadata")
    xml.appendChild(metadata)
    attachments = doc.createElement("attachments")
    xml.appendChild(attachments)
    # FIXME attachement and others

    for t in mp.getTracks():
        track = doc.createElement("track")
        track.setAttribute("id", t.getIdentifier())
        track.setAttribute("type", t.getFlavor())

        # -- TAGS --
        if t.getTags():
            tags = doc.createElement("tags")
            for tag_elem in t.getTags():
                tag = doc.createElement("tag")
                tagtext = doc.createTextNode(tag_elem)
                tag.appendChild(tagtext)
                tags.appendChild(tag)
            track.appendChild(tags)
        ## --    --

        mime = doc.createElement("mimetype")
        mtext = doc.createTextNode(t.getMimeType())
        mime.appendChild(mtext)
        url = doc.createElement("url")

        utext = doc.createTextNode(os.path.basename(t.getURI()))
        url.appendChild(utext)
        duration = doc.createElement("duration")
        dtext = doc.createTextNode(str(t.getDuration()))
        duration.appendChild(dtext)
        track.appendChild(mime)
        track.appendChild(url)
        track.appendChild(duration)
        media.appendChild(track)

    for c in mp.getCatalogs():
        cat = doc.createElement("catalog")
        cat.setAttribute("id", c.getIdentifier())
        cat.setAttribute("type", c.getFlavor())
        loc = doc.createElement("url")
        uutext = doc.createTextNode(os.path.basename(c.getURI()))
        loc.appendChild(uutext)
        mim = doc.createElement("mimetype")
        mmtext = doc.createTextNode(c.getMimeType())
        mim.appendChild(mmtext)
        cat.appendChild(mim)
        cat.appendChild(loc)


        # -- TAGS --
        tags = doc.createElement("tags")
        for tag_elem in c.getTags():
            tag = doc.createElement("tag")
            tagtext = doc.createTextNode(tag_elem)
            tag.appendChild(tagtext)
            tags.appendChild(tag)
        cat.appendChild(tags)
        # --     --

        metadata.appendChild(cat)

    for a in mp.getAttachments():
        attachment = doc.createElement("attachment")
        attachment.setAttribute("id", a.getIdentifier())
        attachment.setAttribute("type", a.getFlavor())
        attachment.setAttribute("ref", a.getRef())
        loc = doc.createElement("url")
        a_path = os.path.relpath(a.getURI(), mp.getURI())

        # FIX
        if "rectemp" in a_path:
            a_path = a_path.replace("../rectemp/", "")

        uutext = doc.createTextNode(a_path)
        loc.appendChild(uutext)
        mim = doc.createElement("mimetype")
        mmtext = doc.createTextNode(str(a.getMimeType()))
        mim.appendChild(mmtext)
        attachment.appendChild(mim)
        attachment.appendChild(loc)

        # -- TAGS --
        tags = doc.createElement("tags")
        for tag_elem in a.getTags():
            tag = doc.createElement("tag")
            tagtext = doc.createTextNode(tag_elem)
            tag.appendChild(tagtext)
            tags.appendChild(tag)
        attachment.appendChild(tags)
        # --     --

        attachments.appendChild(attachment)

    # FIXME ADD checksum
    return doc.toprettyxml(indent="   ", newl="\n", encoding="utf-8").decode('utf-8')


def set_manifest_json(mp):
    """Creates a JSON manifest.
    Args:
        mp (Mediapackage): the mediapackage whose information is going to be serialized in a JSON format.
    Returns:
        Dict{str,str}: the content of the JSON manifest with the name of the different properties as keys.
    """
    mp_json = {}
    mp_json["id"] = mp.getIdentifier()
    mp_json["title"] = mp.title
    mp_json["status"] = mp.status
    mp_json["start"] = mp.getDate().isoformat()
    mp_json["creator"] = mp.getCreator() if mp.getCreator() else ""

    if "description" in mp.metadata_episode:
        mp_json["description"] = mp.getDescription()
    if "language" in mp.metadata_episode:
        mp_json["language"] = mp.getLanguage()

    if mp.getSeriesIdentifier():
        mp_json["series"] = mp.getSeriesIdentifier()
        mp_json["seriestitle"] = mp.series_title

        series_data = ['creator', 'contributor',
                'subject', 'language', 'license', 'decription']

        for data in series_data:
            if data in mp.metadata_series:
                mp_json['series{}'.format(data)] = mp.metadata_series[data]

    if mp.getDuration() != None:
        mp_json["duration"] = int(mp.getDuration())

    mp_json["size"] = int(mp.getSize())
    mp_json["sizeByFlavor"] = mp.getSizeByFlavors()

    mp_json["properties"] = mp.properties
    mp_json["folder"] = mp.getURI()

    episode_data = ['licence', 'temporal','spatial',
                        'contributor', 'subject', 'rights']

    for data in episode_data:
        if data in mp.metadata_episode:
            mp_json[data] = mp.metadata_episode[data]

    # OPERATIONS STATUS
    mp_json["operations"] = {}
    for op, status in list(mp.operations.items()):
        mp_json["operations"][op] = status

    # MEDIA - TRACKS
    mp_json['media'] = {}
    tracks_json = []

    for t in mp.getTracks():
        track_json = {}
        track_json["id"] = t.getIdentifier()
        track_json["type"] = t.getFlavor()
        track_json["mimetype"] = t.getMimeType()
        track_json["url"] = t.getURI()
        track_json["duration"] = t.getDuration()
        tracks_json.append(track_json)
    mp_json['media']['track'] = tracks_json


    # METADATA - CATALOGS
    mp_json['metadata'] = {}
    catalogs_json = []

    for c in mp.getCatalogs():
        catalog_json = {}
        catalog_json["id"] = c.getIdentifier()
        catalog_json["type"] = c.getFlavor()
        catalog_json["url"] = c.getURI()
        catalog_json["mimetype"] = c.getMimeType()
        catalogs_json.append(catalog_json)
    mp_json['metadata']['catalog'] = catalogs_json


    # ATTACHMENTS
    mp_json['attachments'] = {}
    attachments_json = []

    for a in mp.getAttachments():
        attachment_json = {}
        attachment_json["id"] = a.getIdentifier()
        attachment_json["type"] = a.getFlavor()
        attachment_json["ref"] = a.getRef()
        attachment_json["url"] = a.getURI()
        attachment_json["mimetype"] = str(a.getMimeType())
        attachments_json.append(attachment_json)
    mp_json['attachments']['attachment'] = attachments_json

    return mp_json


def set_episode(mp):
    """Creates a XML episode.
    Args:
        mp (Mediapackage): the mediapackage whose episode information is going to be obtained.
    Returns:
        Str: the content of episode.xml .
    """
    doc = minidom.Document()
    xml = doc.createElement("dublincore")
    xml.setAttribute("xmlns","http://www.opencastproject.org/xsd/1.0/dublincore/")
    xml.setAttribute("xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance/")
    xml.setAttribute("xmlns:dcterms","http://purl.org/dc/terms/")
    doc.appendChild(xml)
    for name in list(mp.metadata_episode.keys()):
        try:
            if name == "isPartOf" and mp.getSeriesIdentifier() !=None:
                created = doc.createElement("dcterms:" + name)
                text = doc.createTextNode(str(mp.getSeriesIdentifier()))
                created.appendChild(text)
                xml.appendChild(created)
            elif not mp.metadata_episode[name]:
                continue
            elif type(mp.metadata_episode[name]) is datetime:
                created = doc.createElement("dcterms:" + name)
                text = doc.createTextNode(mp.metadata_episode[name].isoformat() + "Z")
                created.appendChild(text)
                xml.appendChild(created)
            else:
                created = doc.createElement("dcterms:" + name)
                text = doc.createTextNode(str(mp.metadata_episode[name]))
                created.appendChild(text)
                xml.appendChild(created)

        except KeyError:
            continue

    if 'temporal' not in mp.metadata_episode and mp.getDuration():
        elem = doc.createElement("dcterms:temporal" )
        start = mp.getDate().isoformat() + "Z"
        end = (mp.getDate() + timedelta(seconds=mp.getDuration()/1000)).isoformat() + "Z"
        temporal_data = 'start={start}; end={end}; scheme=W3C-DTF;'.format(start=start, end=end)
        text = doc.createTextNode(str(temporal_data))
        elem.appendChild(text)
        xml.appendChild(elem)

    return doc.toprettyxml(indent="   ", newl="\n", encoding="utf-8").decode('utf-8') #without encoding



def set_series(mp, logger=None):
    """Creates a XML serie.
    Args:
        mp (Mediapackage): the mediapackage that belongs to a serie that is going to be serialized.
        logger (Logger): true if the manifest attribute xmlns has 'http://mediapackage.opencastproject.org' value. False otherwise.
    Returns:
        Str: the content of the series.xml
    """
    doc = minidom.Document()
    xml = doc.createElement("dublincore")
    xml.setAttribute("xmlns","http://www.opencastproject.org/xsd/1.0/dublincore/")
    xml.setAttribute("xmlns:dcterms","http://purl.org/dc/terms/")
    doc.appendChild(xml)
    for name in list(mp.metadata_series.keys()):
        if mp.metadata_series[name] != None:
            try:
                created = doc.createElement("dcterms:" + name)
                text = doc.createTextNode(str(mp.metadata_series[name]))
                created.appendChild(text)
                xml.appendChild(created)
            except KeyError:
                if logger:
                    logger.warning("KeyError in serializer.set_series")
                continue
    return doc.toprettyxml(indent="   ", newl="\n", encoding="utf-8").decode('utf-8') #without encoding
