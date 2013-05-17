# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/mediapackage/mediapackage
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


"""
Sobre URI de los elementos que forman el MP.

La idea es guardar en memoria el path absoluto al archivo, pero cuando se escribe el manifiesto en XML
solo guradar la ruta relatiba al mismo. Se evitan los problemas la los archivos de sito.
"""

import uuid
import re
import time
import os
from os import path
from datetime import datetime
from xml.dom import minidom
from galicaster.mediapackage.utils import _checknget, read_ini

# Mediapackage Status
NEW = 0
UNSCHEDULED = 1
SCHEDULED = 2
RECORDING = 3
RECORDED = 4
FAILED = 5
PENDING = 6 #DEPRECATED see Operation Status
INGESTING = 7 #DEPRECATED see Operation Status
INGESTED = 8 #DEPRECATED see Operation Status
INGEST_FAILED = 9 #DEPRECATED see Operation Status

# Operation Status
OP_IDLE = 0
OP_NIGHTLY = 1
OP_PENDING = 2
OP_PROCESSING = 3
OP_DONE = 4
OP_FAILED = 5


# Text equivalents
mp_status = {
    0: 'New',
    1: 'Unscheduled',
    2: 'Scheduled',
    3: 'Recording',
    4: 'Recorded',
    5: 'Failed',
    6: 'Pending',
    7: 'Ingesting',
    8: 'Ingested',
    9: 'Fail Ingesting'        
}

op_status = {
    0: 'No',
    1: 'Nightly',
    2: 'Pending',
    3: 'Processing',
    4: 'Done',
    5: 'Failed',

}

# Module Constants
TYPE_TRACK = 'Track'
TYPE_CATALOG = 'Catalog'
TYPE_ATTACHMENT = 'Attachment'
TYPE_OTHER = 'Other'

ELEMENT_TYPES = frozenset([TYPE_TRACK, TYPE_CATALOG, TYPE_ATTACHMENT, TYPE_OTHER])
MANIFEST_TAGS = { TYPE_TRACK: 'track', TYPE_CATALOG: 'catalog', TYPE_ATTACHMENT: 'attachment', TYPE_OTHER: 'other' }

class IllegalStateError(Exception):
    pass


class Element(object):
    """
    Base class for classes that may be contained by a Mediapackage Matterhorn.
    
    Mediapackage elements may be: Track, Catalog, Attachment, Other
    See: org.opencastproject.mediapackage.MediaPackageElement Java Interface in 
    http://opencast.jira.com/svn/MH/trunk/modules/matterhorn-common/src/main/java/org/opencastproject/mediapackage/MediaPackageElement.java
    """
    def __init__(self, uri, flavor=None, mimetype=None, identifier=None):
        # Avoids direct instantiation of Element
        if self.__class__ is Element:
            raise RuntimeError, "Element is an abstract class"
        
        # Element puede ser que no exista y se vaya a crear:
        # Ejemplos: - episode.xml en los nuevos MediaPackages
        #           - los tracks antes de grabarse...
        #if path.exists(uri):
        #    self.uri = uri
        #else:
        #    raise ValueError("The argument 'uri' must be a valid URI")
        self.uri = uri

        self.etype = None
        self.mime = mimetype
        self.flavor = flavor
        self.tags = set()
        self.__id = identifier
        self.__mp = None

    def __repr__(self):
        return '{0}({1}, {2})'.format(self.__class__.__name__, self.flavor, self.uri)
    
    def __eq__(self, other):
        return isinstance(other, Element) and \
            path.samefile(self.uri, other.uri) and \
            self.etype == other.etype and \
            self.flavor == other.flavor 

    def getIdentifier(self):
        return self.__id
 
    def setIdentifier(self, identifier):
        self.__id = identifier

    def addTag(self, tag):
        return self.tags.append(tag)
          
    def removeTag(self, tag):
        return self.tags.remove(tag)
     
    def containsTag(self, tag):
        return tag in self.tags

    def getTags(self):
        return self.tags

    def clearTags(self, tag):
        self.tags = set()

    def getURI(self):
        return self.uri

    def getMimeType(self):
        return self.mime
    
    def setMimeType(self, mime):
        self.mime = mime
    
    def getFlavor(self):
        return self.flavor
    
    def getElementType(self):
        return self.etype

    def getMediapackage(self):
        return self.__mp

    def setMediapackage(self, mp):
        if mp == None or isinstance(mp, Mediapackage):
            self.__mp = mp
        else:
            raise TypeError("Argument 'mp' needs to be a Mediapackage")       

class Track(Element):
    """
    Tracks de audio e video para introducir en MH Mediapackage

    See: org.opencastproject.mediapackage.Track Java Interface in 
    http://opencast.jira.com/svn/MH/trunk/modules/matterhorn-common/src/main/java/org/opencastproject/mediapackage/Track.java
    """
    def __init__(self, uri, duration, flavor=None, mimetype=None, identifier=None):
        super(Track, self).__init__(uri=uri, flavor=flavor, mimetype=mimetype, identifier=identifier)
        self.etype = TYPE_TRACK
        if isinstance(duration, basestring):
            self.duration = int(duration)
        else:
            self.duration = duration
    
    def getDuration(self):
        return self.duration
    
    def setDuration(self, duration):
        if isinstance(duration, basestring):
            self.duration = int(duration)
        else:
            self.duration = duration
        
    # hasAudio, hasVideo, getStreams??



class Catalog(Element):
    """
    XML cos datos sobre a gravacion
    """
    def __init__(self, uri, flavor=None, mimetype=None, identifier=None):
        super(Catalog, self).__init__(uri=uri, flavor=flavor, mimetype=mimetype, identifier=identifier)
        self.etype = TYPE_CATALOG



class Attachment(Element):
    """
    Arquivos adxuntos dun MP
    """
    def __init__(self, uri, flavor=None, mimetype=None, identifier=None):
        super(Attachment, self).__init__(uri=uri, flavor=flavor, mimetype=mimetype, identifier=identifier)
        self.etype = TYPE_ATTACHMENT



class Other(Element):
    """
    Outros arquivos do MP
    """
    def __init__(self, uri, flavor=None, mimetype=None, identifier=None):
        super(Other, self).__init__(uri=uri, flavor=flavor, mimetype=mimetype, identifier=None)
        self.etype = TYPE_OTHER



class Mediapackage(object):
    """ 
    Class to manage Matterhorn Mediapackages
    See: org.opencastproject.mediapackage.MediaPackage Java Interface in 
    http://opencast.jira.com/svn/MH/trunk/modules/matterhorn-common/src/main/java/org/opencastproject/mediapackage/MediaPackage.java
    """
    def __init__(self, identifier=None, title=None, date=None, presenter=None, uri=None): #FIXME init with sets

        # Catalog metadata 
        date = date or datetime.utcnow().replace(microsecond = 0)
        self.metadata_episode = {"title" : title, "identifier" : identifier, 
                                 "creator" : presenter, "created" : date,}
            
        self.metadata_series = {'identifier': None, 
                                'title': None}

        if self.getIdentifier() == None:
            self.setIdentifier(unicode(uuid.uuid4()))

        # Secondary metadata
        self.uri = uri
        self.manual = True
        self.status = NEW
        self.__duration = None
        self.__howmany = dict( (k, 0) for k in ELEMENT_TYPES )
          
        self.operation = dict()
        self.properties = {'notes':'', 'origin': ''}
        self.elements = dict()

    def __repr__(self):
        return repr((self.identifier, self.title, self.startTime))

    # This is necessary because assigning ids based exclusively in the current number of elements of a certain type
    # is inconsistent if elements are erased from the MediaPackage (i.e. there may be duplicated ids)

    def getMetadataByName(self, name):
        if self.metadata_episode.has_key(name):
            return self.metadata_episode[name]
        elif name == "identifier":
            return self.identifier()
        elif name == "created":
            return self.startTime
        elif name.lower() == "ispartof":
            return self.series 
        elif name == "seriestitle":
            return self.series_title
        else:
            return None

    def setMetadataByName(self, name, value):
        self.metadata_episode[name] = value # only for episode


    def __newElementId(self, etype):
        if (etype in ELEMENT_TYPES):
            for count in range(self.__howmany[etype]):
                identifier = etype.lower() + '-' + unicode(count)
                if not self.contains(identifier):
                    return identifier
                
            return etype.lower() + '-' + unicode(self.__howmany[etype])
        else:
            return None
        
    def getIdentifier(self):
        return self.metadata_episode['identifier']

    def setIdentifier(self, identifier):
        self.metadata_episode['identifier'] = identifier

    identifier = property(getIdentifier, setIdentifier)

    def getTitle(self):
        return self.metadata_episode['title']
    
    def setTitle(self, title):
        self.metadata_episode['title'] = title

    title = property(getTitle, setTitle)
        
    def getSeriesTitle(self):
        return self.metadata_series['title']
    
    def setSeriesTitle(self, series_title):
        self.metadata_series['title'] = series_title

    series_title = property(getSeriesTitle, setSeriesTitle)
        
    def getCreator(self):
        return self.metadata_episode['creator']

    def setCreator(self, creator):
        self.metadata_episode['creator'] = creator

    creator = property(getCreator, setCreator)

    def getSeriesIdentifier(self):
        return self.metadata_series["identifier"]

    def getSeries(self):
        return self.metadata_series
    
    def setSeries(self, catalog): # catalog is a dictionary with metadata
        if catalog == None:
            catalog = {'title':None, 'identifier': None }
        self.metadata_episode["isPartOf"] = catalog['identifier']
        self.metadata_series = catalog    

    def getLicense(self):
        return self.metadata_episode['license']
    
    def setLicense(self, license):
        self.metadata_episode['license'] = license        

    license = property(getLicense, setLicense)

    def getContributor(self):
        return self.metadata_episode['contributor']

    def setContributor(self, contributor):
        self.metadata_episode['contributor'] = contributor
    
    contributor = property(getContributor, setContributor)   

    def getLanguage(self):
        return self.metadata_episode['language']
    
    def setLanguage(self, language):
        self.metadata_episode['language'] = language

    language = property(getLanguage, setLanguage)

    def getSubject(self):
        return self.metadata_episode['subject']
    
    def setSubject(self, subject):
        self.metadata_episode['subject'] = subject

    subject = property(getSubject, setSubject)

    def getDescription(self):
        return self.metadata_episode['description']
    
    def setDescription(self, description):
        self.metadata_episode['description'] = description

    description = property(getDescription, setDescription)
            
    def getDate(self):
        return self.metadata_episode["created"]

    def setDate(self, startTime):
        #FIXME check is datetime*
        self.metadata_episode["created"] = startTime

    startTime = property(getDate, setDate)

    def getLocalDate(self):
        aux = time.time()
        utcdiff = datetime.utcfromtimestamp(aux) - datetime.fromtimestamp(aux)
        return self.metadata_episode["created"] - utcdiff

    def setLocalDate(self, startTime):
        aux = time.time()
        utcdiff = datetime.utcfromtimestamp(aux) - datetime.fromtimestamp(aux)        
        self.metadata_episode["created"] = startTime + utcdiff

    def getStartDateAsString(self, isoformat=True, local=True):
        if isoformat: 
            if local:
                return self.getLocalDate().isoformat()
            else:
                return self.getDate().isoformat()
        else:
            if local:
                return unicode(self.getLocalDate()) 
            else:
                return unicode(self.getDate()) 

    def getDuration(self):
        if self.__duration in ["", "0", 0, None] and self.hasTracks():# FIXME check every assignment on duration
            for t in self.getTracks():
                if self.__duration < t.getDuration():
                    self.__duration = t.getDuration()
        return self.__duration
    
    def setDuration(self, duration):
        if self.hasTracks():
            raise IllegalStateError("The Mediapackage has tracks already")
        else:
            self.forceDuration(duration)


    def forceDuration(self, duration):
        if isinstance(duration, basestring):
            self.__duration = int(duration)
        else:
            self.__duration = duration

    def getOpStatus(self, name):
        if name in self.operation:
            return self.operation[name] 
        
        self.operation[name] = OP_IDLE
        return OP_IDLE

    def setOpStatus(self, name, value):
        self.operation[name] = value
    
    def contains(self, element):
        if element == None:
            raise ValueError("Argument 'element' must not be None")
        elif isinstance(element, Element):
            return element in self.elements.values()
        else:
            return self.getElementById(element) != None
         
    def getElements(self, etype=None, flavor=None, tags=None):
        results = sorted(self.elements.values(), key=lambda e: e.getIdentifier())
        if etype != None:
            results = filter(lambda elem: elem.getElementType() == etype, results)
        if flavor != None:
            results = filter(lambda elem: elem.getFlavor() == flavor, results)
        if tags != None:
            if isinstance(tags, basestring):
                # It's a single tag
                results = filter(lambda elem: elem.containsTag(tags), results)
            else:
                # Assuming it's a list of tags
                tagset = set(tags)
                exc_set = set(filter(lambda tag: tag[0] == '-', tagset))
                tagset -= exc_set
                results = filter(lambda elem: (len((set(elem.getTags()) - exc_set) & tagset) > 0), results)
        return results
             
    def getElementById(self, identifier, etype=None):
        elem = self.elements[identifier]
        if etype == None or elem.getElementType() == etype:
            return elem
        else:
            return None
        
    def getElementsByTag(self, tag, etype=None):
        if isinstance(tag, basestring):
            return self.getElementsByTags(self, tag, etype)
        else:
            raise TypeError("The argument 'tag' should be a string")

    def getElementsByTags(self, tags, etype=None):
        """
        Return the elements that are tagged with any of the given tags or an empty list if no such elements are found. 
        
        If any of the tags supplied start with a '-' character, any elements matching the tag will be excluded instead.
        If the tag list is empty or None, all elements are returned
        """
        return self.getElements(tags=tags, etype=etype)
    
    def getElementsByFlavor(self, flavor):
        if flavor == None:
            raise ValueError("Argument 'flavor' cannot be None")
        return self.getElements(flavor=flavor)
    
    def hasElements(self, etype=None):
        """
        Returns True if the Mediapackage contains some element
        
        This method is not present in the original Java implementation, but it is included here for completeness
        """
        if etype == None:
            return sum(self.__howmany[x] for x in self.__howmany.keys()) > 0
        elif etype in ELEMENT_TYPES:
            return self.__howmany[etype] > 0
        else:
            raise ValueError("The argument does not name a valid type")
    
    def getTrack(self, identifier):
        return self.getElementById(identifier, TYPE_TRACK)
    
    def getTracks(self, flavor=None):
        result = self.getElements(etype=TYPE_TRACK)
        if (flavor != None):
            result = filter(lambda elem: elem.getFlavor() == flavor, result)
        return result
    
    def getTracksByTag(self, tag):
        return self.getElementsByTag(tag, TYPE_TRACK)
    
    def getTracksByTags(self, tags):
        return self.getElements(etype=TYPE_TRACK, tags=tags)
    
    def hasTracks(self):
        return self.hasElements(TYPE_TRACK)
    
    def getAttachment(self, identifier):
        return self.getElementById(identifier, TYPE_ATTACHMENT)
    
    def getAttachments(self, flavor=None):
        return self.getElements(etype=TYPE_ATTACHMENT, flavor=flavor)
    
    def getAttachmentsByTag(self, tag):
        return self.getElementsByTag(tag, TYPE_ATTACHMENT)
    
    def getAttachmentsByTags(self, tags):
        return self.getElements(etype=TYPE_ATTACHMENT, tags=tags)
    
    def hasAttachments(self):
        return self.hasElements(TYPE_ATTACHMENT)
    
    def getCatalog(self, identifier):
        return self.getElementById(identifier, TYPE_CATALOG)
    
    def getCatalogs(self, flavor=None):
        return self.getElements(etype=TYPE_CATALOG, flavor=flavor)
    
    def getCatalogsByTag(self, tag):
        return self.getElementsByTag(tag, TYPE_CATALOG)
    
    def getCatalogsByTags(self, tags):
        return self.getElements(etype=TYPE_CATALOG, tags=tags)
    
    def hasCatalogs(self):
        return self.hasElements(TYPE_CATALOG)
    
    def getUnclassifiedElement(self, identifier):
        return self.getElementById(identifier, TYPE_OTHER)
    
    def getUnclassifiedElements(self, flavor=None):
        return self.getElements(etype=TYPE_OTHER, flavor=flavor)
    
    def getUnclassifiedElementsByTag(self, tag):
        return self.getElementsByTag(tag, TYPE_OTHER)
    
    def getUnclassifiedElementsByTags(self, tags):
        return self.getElements(etype=TYPE_OTHER, tags=tags)
    
    def hasUnclassifiedElements(self):
        return self.hasElements(TYPE_OTHER)
    
    def add(self, item, etype=None, flavor=None, mime=None, duration=None, identifier=None): # FIXME incluir starttime?
        if isinstance(item, Element):
            elem = item
            etype = elem.getElementType()
        else:
            # Assuming this is a URI to the element (requires the etype is set)
            if (etype in ELEMENT_TYPES):
                if etype == TYPE_TRACK:
                    elem = Track(uri=item, duration=duration, flavor=flavor, mimetype=mime, identifier=identifier)
                elif etype == TYPE_ATTACHMENT:
                    elem = Attachment(uri=item, flavor=flavor, mimetype=mime, identifier=identifier)
                elif etype == TYPE_CATALOG:
                    elem = Catalog(uri=item, flavor=flavor, mimetype=mime, identifier=identifier)
                else: 
                    elem = Other(uri=item, flavor=flavor, mimetype=mime, identifier=identifier)
            else:
                raise ValueError("Argument 'type' does not name a valid Element type")
        
        if etype not in ELEMENT_TYPES:
            raise ValueError("Invalid element type in argument")

        if elem.getMediapackage() == None:
            if elem.getIdentifier() == None:
                identifier = self.__newElementId(etype)
                elem.setIdentifier(identifier)
            elem.setMediapackage(self)
            self.__howmany[etype] += 1
        elif elem.getMediapackage() != self:
            raise RuntimeError("Trying to add an element already in another Mediapackage")
        
        self.elements[identifier] = elem
        
        return identifier

    def remove(self, arg):
        """
        Remove the element referenced directly or by its identifier Element-X, ie catalog-2
        """
        if isinstance(arg, Element):
            if self.getElementById(arg.getIdentifier()) == arg:
                elem = arg
            else:
                return None
        elif isinstance(arg, basestring):
            identifier = arg
            if self.contains(identifier):
                elem = self.getElementById(identifier)
            else:
                return None

        self.__howmany[elem.getElementType()] -= 1
        del self.elements[elem.getIdentifier()]
        elem.setMediapackage(None)
        elem.setIdentifier(None)
            
        # If the element removed was a track, set the MP duration accordingly
        if self.__howmany[TYPE_TRACK] == 0:
            self.__duration = None

        os.remove(elem.uri)
            
        return elem

    def getSize(self):
        size = 0
        for f in self.getElements():
            size += path.getsize(f.uri)
        #TODO ter en conta o tamaño do xml ou non ter en conta
        return size

    def getURI(self):
        return self.uri


    def setURI(self, uri):
        self.uri = uri

       
    #FIXME merge with add
    def addDublincoreAsString(self, content, name=None, rewrite=False):
        assert path.isdir(self.getURI())

        f_path = path.join(self.getURI(), name if name != None else 'episode.xml' ) #FIXME

        f = open(f_path, 'w')
        f.write(content)
        f.close()

        if not rewrite:
            self.add(f_path, TYPE_CATALOG, 'dublincore/episode', 'text/xml')


    def addSeriesDublincoreAsString(self, content, name=None, rewrite=False):
        """
        From XML (series)  to galicaster.Mediapackage         
        """
        assert path.isdir(self.getURI())

        f_path = path.join(self.getURI(), name if name != None else 'series.xml' ) #FIXME

        f = open(f_path, 'w')
        f.write(content)
        f.close()

        if not rewrite:
            self.add(f_path, TYPE_CATALOG, 'dublincore/series', 'text/xml')
        
        
    def marshalDublincore(self):
        """
        Intarnal function to marshal mediapackage atributes and 
        metadata_episode dict with Dubincore episode file
        """
        for i in self.getCatalogs():               
            if i.getFlavor() == "dublincore/episode":
                dom = minidom.parse(i.getURI())                 
                # retrive terms
                EPISODE_TERMS = []
                for node in dom.firstChild.childNodes:
                    if not node.nodeName.count('dcterms:'):
                        continue
                    EPISODE_TERMS.append(node.nodeName.split(':')[1])    
                for name in EPISODE_TERMS:
                    if name in ["created"]:
                        creat = _checknget(dom, "dcterms:" + name)
                        if creat:
                            if creat[-1] == "Z":
                                self.setDate(datetime.strptime(creat, "%Y-%m-%dT%H:%M:%SZ"))
                            else:
                                self.setDate(datetime.strptime(creat, "%Y-%m-%dT%H:%M:%S")) 
                                # parse erroneous format too
                    elif name in ['isPartOf', 'ispartof']: 
                        new = _checknget(dom, "dcterms:"+name)
                        old = _checknget(dom, "dcterms:"+name.lower() )
                        self.metadata_episode[name] = new if new != None else old
                    else:
                        self.metadata_episode[name] = _checknget(dom, "dcterms:" + name)                     
            elif i.getFlavor() == "dublincore/series": # FIXME cover series data and create files if dont exist
                dom = minidom.parse(i.getURI())                 
                # retrive terms
                SERIES_TERMS = []
                for node in dom.firstChild.childNodes:
                    SERIES_TERMS.append(node.nodeName.split(':')[1])                
                for name in SERIES_TERMS:
                    self.metadata_series[name] = _checknget(dom, "dcterms:" + name)

        # Parse temporal metadatum
        if self.metadata_episode.has_key('temporal') and self.metadata_episode['temporal'] and not self.hasTracks():
            try:
                g = re.search('start=(.*)Z; end=(.*)Z;', self.metadata_episode['temporal'])
                start = datetime.strptime(g.group(1), "%Y-%m-%dT%H:%M:%S")
                stop =  datetime.strptime(g.group(2), "%Y-%m-%dT%H:%M:%S")
                diff = stop - start 
                self.setDuration(diff.seconds*1000)
            except:
                pass
            
    #FIXME merge with add
    def addAttachmentAsString(self, content, name=None, rewrite=False, identifier=None):
        assert path.isdir(self.getURI())

        f_path = path.join(self.getURI(), name if name != None else 'data' )

        f = open(f_path, 'w')
        f.write(content)
        f.close()

        if not rewrite:
            self.add(f_path, etype=TYPE_ATTACHMENT, identifier=identifier)


    def getOCCaptureAgentProperty(self, name):
        # FIXME refactor
        try:
            attach = self.getAttachment('org.opencastproject.capture.agent.properties')
            values = dict(read_ini(attach.getURI()))
            return values[name]
        except:
            return None


    def getOCCaptureAgentProperties(self):
        # FIXME refactor
        try:
            attach = self.getAttachment('org.opencastproject.capture.agent.properties')
            return dict(read_ini(attach.getURI()))
        except:
            return {}
