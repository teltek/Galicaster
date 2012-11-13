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
import os
import sys
import traceback
import logging
import zipfile
from os import path,system
from xml.dom import minidom

from galicaster.mediapackage import mediapackage

logger = logging.getLogger()

SERIES_FILE="series.xml"
ziptype = "system" # system,native

def save_in_dir(mp):
    assert path.isdir(mp.getURI())
    # FIXME use catalog to decide what files to modify or create


    # check if series should be added to the catalog

    # Episode **3
    m2 = open(path.join(mp.getURI(), 'episode.xml'), 'w')
    m2.write(set_episode(mp)) #FIXME
    m2.close()

    # Galicaster properties
    m = open(path.join(mp.getURI(), 'galicaster.xml'), 'w')
    m.write(set_properties(mp))
    m.close()

    # Series
    if mp.series not in [None, "", "[]"]:
        # Create or modify file
        m3 = open(path.join(mp.getURI(), SERIES_FILE), 'w')
        m3.write(set_series(mp)) #FIXME
        m3.close()        

    # Manifest
    m = open(path.join(mp.getURI(), 'manifest.xml'), 'w')  
    m.write(set_manifest(mp))  ##FIXME
    m.close()


def save_native_zip(mp, loc):
    """
    Save in ZIP file using python module

    @param mp Mediapackage to save in ZIP.
    @param file can be either a path to a file (a string) or a file-like object.
    """

    z= zipfile.ZipFile(loc,'w',zipfile.ZIP_STORED,True)
    # store only (DEFAULT)        

    # manifest
    z.writestr('manifest.xml', set_manifest(mp))

    # episode (fist persist episode)
    m2 = open(path.join(mp.getURI(), 'episode.xml'), 'w')
    m2.write(set_episode(mp))
    m2.close()
        
    for catalog in mp.getCatalogs():
        if path.isfile(catalog.getURI()):
            z.write(catalog.getURI(), path.basename(catalog.getURI()))

    # tracks
    for track in mp.getTracks():
        if path.isfile(track.getURI()):
            z.write(track.getURI(), path.basename(track.getURI()))

    for attach in mp.getAttachments():
        if path.isfile(attach.getURI()):
            z.write(attach.getURI(), path.basename(attach.getURI()))

    # FIXME other elements
    z.close()

def save_system_zip(mp, loc):

    tmp_file = 'manifest.xml'
    m = open(tmp_file,'w')
    m.write(set_manifest(mp))
    m.close()    

    # episode (fist persist episode)
    m2 = open(path.join(mp.getURI(), 'episode.xml'), 'w')
    m2.write(set_episode(mp))
    m2.close()

    files = [tmp_file]

    #catalogs
    for catalog in mp.getCatalogs():
        if path.isfile(catalog.getURI()):
            files += [catalog.getURI()]

    # tracks    
    for track in mp.getTracks():
        if path.isfile(track.getURI()):
            files += [track.getURI()]

    for attach in mp.getAttachments():
        if path.isfile(attach.getURI()):
            files += [attach.getURI()]
    
    # FIXME other elements
    
    try:
        loc = loc if type(loc) in [str,unicode] else loc.name
        system('zip -j0 "'+loc + '" "'+'" "'.join(files) + '" >/dev/null')
        if os.path.isfile(loc+".zip"): # WORKARROUND to eliminate automatic extension .zip
            os.rename(loc+".zip",loc)
        
        #FNULL = open('/dev/null', 'w')
        #subprocess.check_call(['zip','-j0',loc]+files,stdout=FNULL)
    except Exception:
        logger.error("Zip failed: "+str(sys.exc_info()[0]))
    loc = None
    os.remove(tmp_file)

if ziptype == "system":
    logger.debug("Ussing System Zip")
    save_in_zip = save_system_zip
else: 
    logger.debug("Ussing Native Zip")
    save_in_zip = save_native_zip


def set_properties(mp):
    """
    Crear la string para galicaster.properties
    """
    doc = minidom.Document()
    galicaster = doc.createElement("galicaster") 
    doc.appendChild(galicaster)
    status = doc.createElement("status")
    stext = doc.createTextNode(unicode(mp.status))
    status.appendChild(stext)
    galicaster.appendChild(status)

    operations = doc.createElement("operations")
    galicaster.appendChild(operations)
    for (op_name, op_value) in mp.operation.iteritems():
        operation = doc.createElement("operation")
        operation.setAttribute("key", op_name) 
        status = doc.createElement("status")
        text = doc.createTextNode(unicode(op_value))
        status.appendChild(text)
        operation.appendChild(status)
        operations.appendChild(operation)        

    properties = doc.createElement("properties")
    galicaster.appendChild(properties)
    for (prop_name, prop_value) in mp.properties.iteritems():
        prop = doc.createElement("property")
        prop.setAttribute("name", prop_name) 
        text = doc.createTextNode(unicode(prop_value))
        prop.appendChild(text)
        properties.appendChild(prop)

    return doc.toxml(encoding="utf-8")

def set_manifest(mp):
    """
    Crear un manifest XML 
    """
    doc = minidom.Document()
    xml = doc.createElement("mediapackage") 
    xml.setAttribute("xmlns", "http://mediapackage.opencastproject.org")  
    xml.setAttribute("id", mp.getIdentifier()) 
    xml.setAttribute("start", mp.getDate().isoformat())
    if mp.getDuration() != None:
        xml.setAttribute("duration", unicode(mp.getDuration())) 
    
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
        mime = doc.createElement("mimetype")
        mtext = doc.createTextNode(t.getMimeType()) 
        mime.appendChild(mtext)
        url = doc.createElement("url")
        utext = doc.createTextNode(path.basename(t.getURI()))
        url.appendChild(utext)
        duration = doc.createElement("duration")               
        dtext = doc.createTextNode(unicode(t.getDuration()))
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
        uutext = doc.createTextNode(path.basename(c.getURI()))
        loc.appendChild(uutext)
        mim = doc.createElement("mimetype")
        mmtext = doc.createTextNode(c.getMimeType())
        mim.appendChild(mmtext)
        cat.appendChild(mim)
        cat.appendChild(loc)
        metadata.appendChild(cat)   

    for a in mp.getAttachments():
        attachment = doc.createElement("attachment")
        attachment.setAttribute("id", a.getIdentifier())
        loc = doc.createElement("url")
        uutext = doc.createTextNode(path.basename(a.getURI()))
        loc.appendChild(uutext)
        attachment.appendChild(loc)
        attachments.appendChild(attachment)   
        
    # FIXME ADD checksum
    # return doc.toprettyxml(indent="   ", newl="\n",encoding="utf-8")    
    return doc.toxml(encoding="utf-8")          
         

def set_episode(mp):
    """
    Crear un episode XML
    """
    doc = minidom.Document()
    xml = doc.createElement("dublincore")
    xml.setAttribute("xmlns","http://www.opencastproject.org/xsd/1.0/dublincore/")
    xml.setAttribute("xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance/")
    xml.setAttribute("xmlns:dcterms","http://purl.org/dc/terms/")
    doc.appendChild(xml)
    for name in mediapackage.DCTERMS: #FIXME *33
        try:
            if not mp.metadata_episode[name]:
                continue
            if type(mp.metadata_episode[name]) is not list:
                created = doc.createElement("dcterms:" + name)
                text = doc.createTextNode(unicode(mp.metadata_episode[name]))
                created.appendChild(text)
                xml.appendChild(created)
            else:
                if  len(mp.metadata_episode[name]):
                    for element in mp.metadata_episode[name]:
                        created = doc.createElement("dcterms:" + name)
                        text = doc.createTextNode(element)
                        created.appendChild(text)
                        xml.appendChild(created)
                    
        except KeyError:
            continue

    return doc.toxml(encoding="utf-8") #without encoding



def set_series(mp):
    """
    Crear un episode XML
    """
    doc = minidom.Document()
    xml = doc.createElement("dublincore")
    xml.setAttribute("xmlns","http://www.opencastproject.org/xsd/1.0/dublincore/")
    xml.setAttribute("xmlns:dcterms","http://purl.org/dc/terms/")
    doc.appendChild(xml)
    for name in ["title", "identifier"]: # FIXME Set mediapackage.SeriesDCTERMS
        try:
            created = doc.createElement("dcterms:" + name)
            text = doc.createTextNode(unicode(mp.metadata_series[name]))
            created.appendChild(text)
            xml.appendChild(created)
        except KeyError:
            print "KeyError in serializer.set_series"
            continue
    return doc.toxml(encoding="utf-8") #without encoding
