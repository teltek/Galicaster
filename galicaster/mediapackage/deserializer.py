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
from galicaster.mediapackage import mediapackage
from galicaster.mediapackage.utils import _checknget, _checkget
from galicaster.mediapackage.utils import _getElementAbsPath

                    
def fromXML(xml):
    # FIXME: xml podria ser un file, o un string con un path.
    # Ojo si no existe.
    """
    Obter os datos do manifest, e despois do episode e o series
    """
    mp_uri = path.dirname(path.abspath(xml))
    mp = mediapackage.Mediapackage(uri = mp_uri)
    manifest = minidom.parse(xml)          
    principal = manifest.getElementsByTagName("mediapackage")
    mp.setDuration(principal[0].getAttribute("duration")) # FIXME check if empty and take out patch in listing.populatetreeview   
    mp.setIdentifier(principal[0].getAttribute("id"))

    if principal[0].hasAttribute("start"):
        mp.setDate(datetime.strptime(principal[0].getAttribute("start"), '%Y-%m-%dT%H:%M:%S'))
   
    without_galicaster = False

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
        print "WHITOUT galicaster.xml"
        without_galicaster = True

    
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
            mp.add(_getElementAbsPath(uri, mp.getURI()), etype, flavor, mime, duration, identifier)

            if uri == 'org.opencastproject.capture.agent.properties' and etype == mediapackage.TYPE_ATTACHMENT:
                mp.manual = False
                
            if etype == mediapackage.TYPE_TRACK and mp.status == mediapackage.NEW and without_galicaster:
                mp.status = mediapackage.RECORDED

    mp.marshalDublincore()
    return mp        

