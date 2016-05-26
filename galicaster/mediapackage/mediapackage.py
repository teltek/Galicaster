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
This module contains:
    the Mediapackage class: manage Opencast mediapackages.
    the mediapackage elements classes (Track, Catalog, Attachment, Other).
    the Element superclass.
"""

import uuid
import re
import time
import os
from os import path
from datetime import datetime
from xml.dom import minidom
from galicaster.mediapackage.utils import _checknget, read_ini

from galicaster.utils.i18n import _

# Mediapackage Status
NEW = 0
UNSCHEDULED = 1
SCHEDULED = 2
RECORDING = 3
RECORDED = 4
FAILED = 5

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
    0: _('No'),
    1: _('Nightly'),
    2: _('Pending'),
    3: _('Processing'),
    4: _('Done'),
    5: _('Failed'),

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
    def __init__(self, uri, flavor=None, mimetype=None, identifier=None, tags=[]):
        """Initializer of the abstract class Element.
        Base class for classes that may be contained by a Mediapackage Opencast.
        Mediapackage elements may be: Track, Catalog, Attachment, Other
        See: org.opencastproject.mediapackage.MediaPackageElement Java Interface in 
            url: http://opencast.jira.com/svn/MH/trunk/modules/opencast-common/src/main/java/org/opencastproject/mediapackage/MediaPackageElement.java
        Args:
            uri (str): the absolute path of the element.
            flavor (str): the classificatory tag of the element.
            mimetype (str): the mime type of the element.
            identifier (str): the identifier of the element.
        Attributes:
            uri (str): the given absolute path of the element.
            etype (str): the type of element. See module constants.
            mime (str): the given mime type of the element.
            flavor (str): the fiven cassificatory tag of the element.
            tags (List[str]): list of the tags (opencast cassificatory tags) of the element.
            __id (str): the given identifier of the element.
            __mp (Mediapackage): the mediapackage which the element belongs.
        Raises:
            RuntimeError: If element is directly instanciated.
        """
        # Avoids direct instantiation of Element
        if self.__class__ is Element:
            raise RuntimeError, "Element is an abstract class"
        
        # Element could not exist and going to be created:
        # Examples: - episode.xml in new MediaPackages
        #           - tracks before being recorded...
        #if path.exists(uri):
        #    self.uri = uri
        #else:
        #    raise ValueError("The argument 'uri' must be a valid URI")
        self.uri = uri
	
        self.etype = None
        self.mime = mimetype
        self.flavor = flavor
        self.tags = tags
        self.__id = identifier
        self.__mp = None

    def __repr__(self):
        """Gets the name, flavor and URI of the element.
        Returns:
            Str: name, flavor and URI of the element.
        """
        return '{0}({1}, {2})'.format(self.__class__.__name__, self.flavor, self.uri)
    
    def __eq__(self, other):
        """Compares if two elements are equals.
        Returns:
            Bool: True if they share file, type and flavor. False otherwise.
        """
        return isinstance(other, Element) and \
            path.samefile(self.uri, other.uri) and \
            self.etype == other.etype and \
            self.flavor == other.flavor 

    def getIdentifier(self):
        """Gets the identifier of the element.
        Returns:
            Str: the identifier of the element.
        """
        return self.__id
 
    def setIdentifier(self, identifier):
        """Sets the id a the element.
        Args:
            identifier (str): the new id of the element.
        """
        self.__id = identifier

    def addTag(self, tag):
        """Adds a tag to the set of tags of the element.
        Args:
            tag (str): a new tag.
        Returns:
            List[Str]: the updated list of tags.
        """
        self.tags.append(tag)
        return self.tags
          
    def removeTag(self, tag):
        """Removes a tag from the list of tags of the element.
        Args:
            tag (str): the tag that is going to be deleted.
        Returns:
            List[Str]: the updated list of tags.
        """
        self.tags.remove(tag)
        return self.tags

    def setTags(self, tags):
        """Set the tag list of the element.
        Args:
            tags List[Str]: the tag list that is going to be set.
        """
        self.tags = tags
     
    def containsTag(self, tag):
        """Checks if a tag is in the list of tags of the element.
        Args:
            tag (str): the tag whose whose belonging to the list is going to be checked.
        Returns:
            Bool: True if the tag is in the tag list of the element. False otherwise.
        """
        return tag in self.tags

    def getTags(self):
        """Gets the list of tags of the element.
        Returns:
            List[Str]: the tag list of the element.
        """
        return self.tags

    def clearTags(self):
        """Removes all the tags from the element tag list.
        """
        self.tags = set()

    def getURI(self):
        """Gets the absolute path of the element.
        Returns:
            Str: the URI of the element.
        """
        return self.uri

    def setURI(self, uri):
        """Sets the URI of the element.
        Args: 
            uri (str): the new URI of the element.
        """
        self.uri = uri

    def getMimeType(self):
        """Gets the mime type of the element.
        Returns:
            Str: the mime type of the element.
        """
        return self.mime
    
    def setMimeType(self, mime):
        """Sets the mime type of the element.
        Args:
            mime (str): the new mime type of the element.
        """
        self.mime = mime

    def getFlavor(self):
        """Gets the flavor (classificatory tag) of the element.
        Returns:
            Str: the flavor of the element.
        """
        return self.flavor

    def setFlavor(self, flavor):
        """Sets the flavor type of the element.
        Args:
            flavor (str): the new flavor type of the element.
        """
        self.flavor = flavor
    
    def getElementType(self):
        """Gets the type of the element. See module constants.
        Returns:
            Str: the element type.
        """
        return self.etype

    def getMediapackage(self):
        """Gets the mediapackage to which the element belongs.
        Returns:
            Mediapackage: the mediapackage.
        """
        return self.__mp

    def setMediapackage(self, mp):
        """Sets the mediapackage to which the element belongs.
        Args:
            mp (Mediapackage): the mediapackage.
        """
        if mp == None or isinstance(mp, Mediapackage):
            self.__mp = mp
        else:
            raise TypeError("Argument 'mp' needs to be a Mediapackage")       


class Track(Element):
    def __init__(self, uri, duration, flavor=None, mimetype=None, identifier=None, tags=[]):
        """Initializes the representation of the audio and video tracks to be introduced into Opencast Mediapackage.
        See: org.opencastproject.mediapackage.Track Java Interface in 
            url: http://opencast.jira.com/svn/MH/trunk/modules/opencast-common/src/main/java/org/opencastproject/mediapackage/Track.java
        Args:
            uri (str): the track's absolute path.
            duration (int): the duration of the track in seconds.
            flavor (str): the classificatory name of the track.
            mimetype (str): the mime type of the track.
            identifier (str): the unique identifier of the track.
        Attributes:
            etype (str): 'Track' (element type)  
            duration (int): the given duration of the track in seconds.
        """
        tags=["archive"]            

        super(Track, self).__init__(uri=uri, flavor=flavor, mimetype=mimetype, identifier=identifier, tags=tags)
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
        
    def getAsDict(self):
        t = {}
        t['uri']        = self.getURI()
        t['duration']   = self.getDuration()
        t['flavor']     = self.getFlavor()
        t['mimetype']   = self.getMimeType()
        t['identifier'] = self.getIdentifier()
        t['tags']       = self.getTags()
        return t

    # hasAudio, hasVideo, getStreams??



class Catalog(Element):
    def __init__(self, uri, flavor=None, mimetype=None, identifier=None, tags=[]):
        """Initializes the representation of the catalog of a mediapackage.
        The catalog has the data about a recording.
        It is saved as a xml.
        Args:
            uri (str): the absolute path of the catalog.
            flavor (str): the cassificatory name of the catalog.
            mimetype (str): the mime type of the catalog.
            identifier (str): the unique identifier of the catalog.
        Attributes:
            etype (str): 'Catalog' (type element)
        """
        # Add the tag 'engage' by default
        if not tags:
            tags=["engage"]

        super(Catalog, self).__init__(uri=uri, flavor=flavor, mimetype=mimetype, identifier=identifier, tags=tags)
        self.etype = TYPE_CATALOG



class Attachment(Element):
    def __init__(self, uri, flavor=None, mimetype=None, identifier=None, ref=None, tags=['engage']):
        """Initializes the representation of the attachments of a mediapackage.
        Attachments are images and others files in the mediapackage.
        Args:
            uri (str): the absolute path of the attachment file.
            flavor (str): the classificatory name of the attachment.
            mimetype (str): the mime type of the attachment.
            identifier (str): the unique identifier of the attachment.
            ref (str): the reference of the attachment file.
        Attributes:
            etype (str): 'Attachment' (type element)
            ref (str): the given reference of the attachment.
        """
        # Add the tag 'engage' by default
        if not tags:
            tags=["engage"]

        super(Attachment, self).__init__(uri=uri, flavor=flavor, mimetype=mimetype, identifier=identifier, tags=tags)
        self.etype = TYPE_ATTACHMENT
        self.ref = ref

    def getRef(self):
        """Gets the reference of the mediapackage attachment.
        Returns:
            Str: Reference of the attachment.
        """
        return self.ref
    
    def setRef(self, ref):
        """Sets the ref of the attachment.
        Args:
            ref (str): the new reference of the attachment.
        """
        self.ref = ref
    



class Other(Element):
    def __init__(self, uri, flavor=None, mimetype=None, identifier=None, tags=['engage']):
        """Initializes the representation of uniclassified files of a mediapackage.
        Args:
            uri (str): the absolute path of the uniclassified file.
            flavor (str): the classificatory name of the uniclassified file.
            mimetype (str): the mime type of the unclassified file.
            identifier (str): the unique identifier of the unclassified file.
        Attributes:
            etype (str): 'Other' (element type)
        """
        # Add the tag 'engage' by default
        if not tags:
            tags=["engage"]

        super(Other, self).__init__(uri=uri, flavor=flavor, mimetype=mimetype, identifier=None, tags=[])
        self.etype = TYPE_OTHER



class Mediapackage(object):
    def __init__(self, identifier=None, title=None, date=None, presenter=None, uri=None): #FIXME init with sets
        """Initializes the class to manage Opencast mediapackages.
        See: org.opencastproject.mediapackage.MediaPackage Java Interface in 
            url: http://opencast.jira.com/svn/MH/trunk/modules/opencast-common/src/main/java/org/opencastproject/mediapackage/MediaPackage.java
        Args:
            identifier (str): the unique identifier of the mediapackage.
            title (str): the title of the mediapackage.
            date (Datetime): timestamp of the mediapackage.
            presenter (str): creator of the mediapackage.
            uri (str): the absolute path of the mediapackage directory.
        Attributes:
            date (Datetime): the given date of the mediapackage or the actual time.
            metadata_episode (Dict{str,str or Datetime}): information about the episode in the metadata.
            metadata_series (Dict{str,str}): information about the serie to which belongs the mediapackage episode.If the episode belongs to no serie, the values of the dictionary are none.
            uri (str): the given absolute path of the mediapackage directory.
            manual (bool): true if the recording of the mediapackage is manually done. False if it is scheduled. 
            status (int): the status of the mediapackage. See Mediapackage status constants. 
            __duration (int): the duration of the longest track in the mediapackage in seconds.
            __howmany (Dict{str,int}): a dictionary where keys represent the different element types of the mediapackage and its value the quantity of them.
            operation (Dict{str,int}): the status of the different operations in the mediapackage identified by the operation name as key.
            properties (Dict{str,str}): the different properties of the mediapackage identifies by the property name as key.
            elements (Dict{str,Element}): the set of elements of the mediapackage identified by its unique identifier as key.
        """

        # Catalog metadata 
        date = date or datetime.utcnow().replace(microsecond = 0)
        self.metadata_episode = {"title" : title, "identifier" : identifier, 
                                 "creator" : presenter, "created" : date,}
            
        self.metadata_series = {'identifier': None, 
                                'title': None}

        if self.getIdentifier() == None:
            self.setNewIdentifier()

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
        """Gets the string that represents the mediapackage printing its identifier, title and start time.
        Returns:
            Str: the mediapackage identifier, title and start time.
        """
        return repr((self.identifier, self.title, self.startTime))

    # This is necessary because assigning ids based exclusively in the current number of elements of a certain type
    # is inconsistent if elements are erased from the MediaPackage (i.e. there may be duplicated ids)

    def getMetadataByName(self, name):
        """Gets the metadate by the name.
        Args:
            name (str): the name of the parameter whose value is going to be returned.
        Returns:
            Str: the value of the parameter name in the mediapackage.
        """
        if self.metadata_episode.has_key(name):
            return self.metadata_episode[name]
        elif name.lower() == "ispartof":
            return self.getSeries()
        elif name == "seriestitle":
            return self.getSeriesTitle()
        else:
            return None

    def setMetadataByName(self, name, value):
        """Sets the value of a parameter of the episode.
        Args:
            name (str): the name of the parameter as a key in metadata_episode.
            value (str): the new value of the parameter name.
        """
        self.metadata_episode[name] = value # only for episode
    
    
    def getAsDict(self):
        mp = {}
        mp["id"]      = self.getIdentifier()
        mp["title"]   = self.title
        mp["status"]  = self.status
        mp["start"]   = self.getDate().isoformat()
        mp["creator"] = self.getCreator() if self.getCreator() else ""

        tracks = []
        for t in self.getTracks(): 
            tracks.append(t.getAsDict())

        mp["tracks"] = tracks
        return mp


    def __newElementId(self, etype):
        """Gets a free (unused) identifier to be set in a new element.
        Returns:
            Str: the identifier of a element that is not in the mediapackage yet.
        """
        if (etype in ELEMENT_TYPES):
            for count in range(self.__howmany[etype]):
                identifier = etype.lower() + '-' + unicode(count)
                if not self.contains(identifier):
                    return identifier
                
            return etype.lower() + '-' + unicode(self.__howmany[etype])
        else:
            return None
        
    def getIdentifier(self):
        """Gets the identifier of the mediapackage.
        Returns:
            Str: the identifier of the mediapackage episode.
        """
        return self.metadata_episode['identifier']

    def setIdentifier(self, identifier):
        """Sets a identifier for the mediapackage episode
        Args:
            identifier (str): episode identifier to be set.
        """
        self.metadata_episode['identifier'] = identifier

    def setNewIdentifier(self):
        """Gets a new identifier from uuid and sets it to the mediapackage episode.
        """
        self.setIdentifier(unicode(uuid.uuid4()))

    identifier = property(getIdentifier, setIdentifier)

    def getTitle(self):
        """Gets the title of the mediapackage episode.
        Returns:
            Str: the title of the mediapackage episode.
        """
        return self.metadata_episode['title']
    
    def setTitle(self, title):
        """Sets the title of the mediapackage episode.
        Args:
            title (str): the title to be set.
        """
        self.metadata_episode['title'] = title

    title = property(getTitle, setTitle)
        
    def getSeriesTitle(self):
        """Gets the title of the serie to which the mediapackage episode belongs.
        Returns:
            Str: the title of the mediapackage serie.
        """
        return self.metadata_series['title']
    
    def setSeriesTitle(self, series_title):
        """Sets the title of the mediapackage serie.
        Args:
            series_title (str): the serie title to be set.
        """
        self.metadata_series['title'] = series_title

    series_title = property(getSeriesTitle, setSeriesTitle)
        
    def getCreator(self):
        """Gets the creator of the mediapackage episode.
        Returns:
            Str: the creator of the mediapackage episode.
        """
        return self.metadata_episode['creator']

    def setCreator(self, creator):
        """Sets the creator of a mediapackage episode.	
        Args:
            creator (str): the creator to be set.
        """
        self.metadata_episode['creator'] = creator

    creator = property(getCreator, setCreator)

    def getSeriesIdentifier(self):
        """Gets the identifier of the serie to which the mediapackage episode belongs.
        Returns:
            Str: the mediapackage serie identifier.
        """
        return self.metadata_series["identifier"]

    def getSeries(self):
        """Gets the metadata of the serie to which the mediapackage episode belongs.
        Returns:
            Dict{Str,Str}: the metadata of the mediapackage serie (title and identifier). 
        """
        return self.metadata_series
    
    def setSeries(self, catalog): # catalog is a dictionary with metadata
        """Sets the metadata of the mediapackage series and episode in order to relation them.
        Args:
            catalog (Dict{Str,str}): information of the metadata serie.
        """
        if catalog == None:
            catalog = {'title':None, 'identifier': None }
        self.metadata_episode["isPartOf"] = catalog['identifier']
        self.metadata_series = catalog    

    def getLicense(self):
        """Gets the mediapackage episode license.
        Returns:
            Str: mediapackage episode license.
        """
        return self.metadata_episode['license']
    
    def setLicense(self, license):
        """Sets the mediapackage episode license.
        Args:
            license (str): the license to be set.
        """
        self.metadata_episode['license'] = license        

    license = property(getLicense, setLicense)

    def getContributor(self):
        """Gets the mediapackage episode contributor.
        Returns:
            Str: mediapackage episode contributor.
        """
        return self.metadata_episode['contributor']

    def setContributor(self, contributor):
        """Sets the mediapackage episode contributor.
        Args:
            contributor (str): the contributor to be set.
        """
        self.metadata_episode['contributor'] = contributor
    
    contributor = property(getContributor, setContributor)   

    def getLanguage(self):
        """Gets the mediapackage episode language.
        Returns:
            Str: mediapackage episode language.
        """
        return self.metadata_episode['language']
    
    def setLanguage(self, language):
        """Sets the mediapackage episode language.
            language (str): the language to be set.
        """
        self.metadata_episode['language'] = language

    language = property(getLanguage, setLanguage)

    def getSubject(self):
        """Gets the mediapackage episode subject.
        Returns:
            Str: the mediapackage episode subject.
        """
        return self.metadata_episode['subject']
    
    def setSubject(self, subject):
        """Sets the mediapackage episode subject.
            subject (str): the episode to be set.
        """
        self.metadata_episode['subject'] = subject

    subject = property(getSubject, setSubject)

    def getDescription(self):
        """Gets the mediapackage episode description.
        Returns:
            Str: the mediapackage episode description.
        """
        return self.metadata_episode['description']
    
    def setDescription(self, description):
        """Sets the mediapackage episode description.
        Args:
            description (str): the description to be set.
        """
        self.metadata_episode['description'] = description

    description = property(getDescription, setDescription)
            
    def getDate(self):
        """Gets the date and time of the mediapackage episode creation.
        Returns:
            Datetime: Datetime of the mediapackage episode creation.		
        """
        return self.metadata_episode["created"]

    def setDate(self, startTime):
        """Sets the date and time of the mediapackage episode creation.
        Args:
            startTime (Datetime): date and time to be set at creation parameter.
        """
        #FIXME check is datetime*
        self.metadata_episode["created"] = startTime

    startTime = property(getDate, setDate)

    def getLocalDate(self):
        """Gets the actual local date and time.
        Returns:
            Datetime: actual local datetime.
        """
        aux = time.time()
        utcdiff = datetime.utcfromtimestamp(aux) - datetime.fromtimestamp(aux)
        return self.metadata_episode["created"] - utcdiff

    def setLocalDate(self, startTime):
        """Sets the local date and time of the mediapackage episode creation.
        Args:
            startTime (Datetime): the datetime of the creation in utf.
        """
        aux = time.time()
        utcdiff = datetime.utcfromtimestamp(aux) - datetime.fromtimestamp(aux)        
        self.metadata_episode["created"] = startTime + utcdiff

    def getStartDateAsString(self, isoformat=True, local=True):
        """Gets the mediapackage timestamp in a specific string format.
        Args:
            isoformat (bool): True if isoformat is going to be returned. False if unicode.
            local (bool): True if local date is going to be returned. False if utf.
        Returns:
            Str: date of the mediapackage episode creation.
        """
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
        """Gets the duration of the largest mediapackage track.
        Returns:
            Int: the largest of the mediapackage tracks duration.
        """
        if self.__duration in ["", "0", 0, None] and self.hasTracks():# FIXME check every assignment on duration
            for t in self.getTracks():
                if self.__duration < t.getDuration():
                    self.__duration = t.getDuration()
        return self.__duration
    
    def setDuration(self, duration):
        """Calls forceDuration if the mediapackage contains no tracks.
        Args:
            duration (int): duration to be set.
        Raises:
            IllegalStateError: if the mediapackage has tracks.
        """
        if self.hasTracks():
            raise IllegalStateError("The Mediapackage has tracks already")
        else:
            self.forceDuration(duration)


    def forceDuration(self, duration):
        """Sets the duration of the mediapackage.
        Args:
            duration (Str or int): the duration to be set as an int.
        """
        if isinstance(duration, basestring):
            self.__duration = int(duration)
        else:
            self.__duration = duration

    def getOpStatus(self, name):
        """Checks if the name of an operation is in the mediapackage. If not exists, adds it with the status OP_IDLE.
        Then returns its status.
        Args:
            name (str): the name of the operation whose status is going to be returned.
        Returns:
            Int: the status of the operation received.	
        """
        if name in self.operation:
            return self.operation[name] 
        
        self.operation[name] = OP_IDLE
        return OP_IDLE

    def setOpStatus(self, name, value):
        """Sets the status of a particular mediapackage operation.
        Args:
            name (Str): name of the operation whose status is going to be set.
            value (int): the status to be set.
        """
        self.operation[name] = value

    def isScheduled(self):
        """ Checks if the status of the MP is scheduled
        Returns:
            Bool: True if the MP is scheduled. False otherwise.
        """
        return self.status == SCHEDULED
    
    def contains(self, element):
        """Checks if the mediapackage contains a particular element.
        Args:
            element (Element): the element to be checked.
        Returns:
            Bool: True if the element is in the mediapackage set of elements. False otherwise.
        Raises:
            ValueError: if the argument received it is not an element.
        """
        if element == None:
            raise ValueError("Argument 'element' must not be None")
        elif isinstance(element, Element):
            return element in self.elements.values()
        else:
            return self.getElementById(element) != None
         
    def getElements(self, etype=None, flavor=None, tags=None, uri=None):
        """Gets the set of (element id,elements) of the mediapackage, ordered by id, that satisfy a particular type, flavor or tags if they are specified.
        If the flavor, tag or type is not specified, gets the elements with any of its possibles values.
        Args:
            etype(str): the type of elements to be returned. See Module constants. 
            flavor (str): a classificatory name of the element.
            tags (str or List): opencast's classificatory names.
        Returns:
            List[Element]: set of elements that satisfies the requested parameters.
        """
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
        """Gets the element of the mediapackage that has a particular identifier and a particular type if it is specified.
        If type specified, gets any element with the given identifier.
        Args:
            identifier (str): the identifier of the element that is going to be returned.
            etype (str): the type of the element that is going to be returned. See Module constants.
        Returns:
            Element: the element with the specified identifier and type.
        """
        if identifier not in self.elements:
            return None     
        elem = self.elements[identifier]
        if etype == None or elem.getElementType() == etype:
            return elem
        else:
            return None
        

    def getElementByURI(self, uri=None):
        """Gets the element of the mediapackage that has a particular uri.
        Args:
            uri (str): the uri of the element that is going to be returned.
        Returns:
            Element: the element with the specified uri.
        """
        result = None
        results = None

        if uri:
            results = sorted(self.elements.values(), key=lambda e: e.getIdentifier())
            results = filter(lambda elem: elem.getURI() == uri, results)

        if results:
            result = results[0]

        return result
        

    #TODO Remove this method an use getElementsByTags instead (string and lists allowed)    
    def getElementsByTag(self, tag, etype=None):
        """Calls getElementsByTags if the tag is a string.
        Otherwise raises TypeError.
        Args:
            tag (str): tag of the elements to be returned.
            etype (str): type of the element to be retured. See module constants.
        Returns:
            List[Element]: a set of elements with the specified tag and type.
        Raises:
            TypeError: If the argument tag type is not a string.
        """
        if isinstance(tag, basestring):
            return self.getElementsByTags(self, tag, etype)
        else:
            raise TypeError("The argument 'tag' should be a string")

    def getElementsByTags(self, tags, etype=None):
        """Returns the elements that are tagged with any of the given tags or an empty list if no such elements are found. 
        If any of the tags supplied start with a '-' character, any elements matching the tag will be excluded instead.
        If the tag list is empty or None, all elements are returned.
	Returns:
		List[Element]: the set of elements that satisfy the specified tags and type.
        """
        return self.getElements(tags=tags, etype=etype)
    
    def getElementsByFlavor(self, flavor):
        """Gets the mediapackage set of elements with the specified flavor.
        Args:
            flavor(str): the classificatory name of one or more elements.
        Returns:
            List[Element]: the set of elements with the given flavor.
        Raises:
            ValueError: if flavor is None.
        """
        if flavor == None:
            raise ValueError("Argument 'flavor' cannot be None")
        return self.getElements(flavor=flavor)
    
    def hasElements(self, etype=None):
        """Checks if the mediapackage contains any element of the given type.
        Args:
            etype (str): type of the element whose existance is going to be checked. See module constants.
        Returns:
            Bool: True if the Mediapackage contains any element (in general or of the type given if specified).
        Raises:
            ValueError: If the type element is invalid.
        Note:
            This method is not present in the original Java implementation, but it is included here for completeness
        """
        if etype == None:
            return sum(self.__howmany[x] for x in self.__howmany.keys()) > 0
        elif etype in ELEMENT_TYPES:
            return self.__howmany[etype] > 0
        else:
            raise ValueError("The argument does not name a valid type")
    
    def getTrack(self, identifier):
        """Gets a particular mediapackage track.
        Args:
            identifier (str): track identifier.
        Returns:
            Track: the track with the given identifier.
        """
        return self.getElementById(identifier, TYPE_TRACK)
    
    def getTracks(self, flavor=None, mimetype=None):
        """Gets the tracks with a particular flavor.
        If no flavor is specified, gets all mediapackage tracks.
        Args:
            flavor (str): the flavor of the tracks that are going to be returned.
        Returns:
            List[Track]: a list of tracks with the specified flavor.	
        """
        result = self.getElements(etype=TYPE_TRACK)
        if (flavor != None):
            result = filter(lambda elem: elem.getFlavor() == flavor, result)
        if (mimetype != None):
            result = filter(lambda elem: elem.getMimeType() == mimetype, result)
        return result

    def getTracksAudio(self):
        """Gets the tracks with a particular flavor.
        If no flavor is specified, gets all mediapackage tracks.
        Args:
            flavor (str): the flavor of the tracks that are going to be returned.
        Returns:
            List[Track]: a list of tracks with the specified flavor.	
        """
        result = self.getElements(etype=TYPE_TRACK)
        result = filter(lambda elem: "audio" in elem.getMimeType(), result)
        return result


    def getTracksMaster(self):
        """Gets the master video tracks of the mediapackage.
        If no master tracks are found, returns None.
        Returns:
            List[Track]: a list of master tracks.	
        """
        result = filter(lambda elem: "presenter/source" in elem.getFlavor() or "presentation/source" in elem.getFlavor(),
                        self.getElements(etype=TYPE_TRACK))

        return result


    def getTracksVideoMaster(self):
        """Gets the master tracks of the mediapackage.
        If no master tracks are found, returns None.
        Returns:
            List[Track]: a list of master tracks.	
        """
        result = filter(lambda elem: "video" in elem.getMimeType(), self.getTracksMaster())

        return result


    def getTracksAudioMaster(self):
        """Gets the master tracks of the mediapackage.
        If no master tracks are found, returns None.
        Returns:
            List[Track]: a list of master tracks.	
        """
        result = filter(lambda elem: "audio" in elem.getMimeType(), self.getTracksMaster())

        return result

        
    #TODO Remove this method an use getTracksByTags instead (string and lists allowed)    
    def getTracksByTag(self, tag):
        """Gets the tracks with a particular tag.
        Args:
            tag (str): the tag of the tracks that are going to be returned.
        Returns:
            List[Track]: a list of tracks with the specified tag.
        """
        return self.getElementsByTag(tag, TYPE_TRACK)
    
    def getTracksByTags(self, tags):
        """Gets the tracks that contains determined tags.
        Args:
            tags (List[str]): set of tags of the tracks that are going to be returned.
        Returns:
            List[Track]: a list of tracks with the specified tags.
        """
        return self.getElements(etype=TYPE_TRACK, tags=tags)
    
    def hasTracks(self):
        """Checks if the mediapackage contains any track.
        Returns:
            Bool: True if the mediapackage conatains any track. False otherwise.
        """
        return self.hasElements(TYPE_TRACK)
    
    def getAttachment(self, identifier):
        """Gets a particular attachment of the mediapackage.
        Args:
            identifier (str): identifier of the particular attachment that is going to be returned.
        Returns:
            Attachment: Attachment with the given identifier.
        """
        return self.getElementById(identifier, TYPE_ATTACHMENT)
    
    def getAttachments(self, flavor=None):
        """Gets a set of attachments with a flavor.
        If no flavor is specified, all attachments are returned.
        Args:
            flavor (str): the flavor of the attachments that are going to be returned.
        Returns:
            List[Attachment]: a list of attachments with a determined flavor if it is specified.
        """
        return self.getElements(etype=TYPE_ATTACHMENT, flavor=flavor)
    
    #TODO Remove this method an use getAttachmentsByTags instead (string and lists allowed)    
    def getAttachmentsByTag(self, tag):
        """Gets a set of attachments with a tag. 
        Args: 
            tag (str): the tag of the attachments that are going to be returned.
        Returns:
            List[Attachment]: a list of attachments with a determined tag.
        """
        return self.getElementsByTag(tag, TYPE_ATTACHMENT)
    
    def getAttachmentsByTags(self, tags):
        """Gets a set of attachments that containes a determined set of tags.
        Args:
            tags (List[Str]): a list of tags of the attachments that are going to be returned.
        Returns:
            List[Attachment]: a list of attachments that contains the specified set of tags.
        """
        return self.getElements(etype=TYPE_ATTACHMENT, tags=tags)
    
    def hasAttachments(self):
        """Checks if the mediapackage has any attachment.
        Returns:
            Bool: True if the mediapackage contains one or more attachments. False otherwise.
        """
        return self.hasElements(TYPE_ATTACHMENT)
    
    def getCatalog(self, identifier):
        """Gets a particular catalog from the mediapackage.
        Args:
            identifier (str): identifier of the catalog.
        Returns:
            Catalog: the catalog with the given identifier.
        """
        return self.getElementById(identifier, TYPE_CATALOG)
    
    def getCatalogs(self, flavor=None):
        """Gets all the catalogs with a particular flavor if specified.
        If no flavor is specified, all the catalogs are returned.
        Args:
            flavor (str): the flavor of the catalogs that are going to be returned.
        Returns:
            List[Catalog]: a list of catalogs with the given flavor if it is specified.
        """
        return self.getElements(etype=TYPE_CATALOG, flavor=flavor)
    
    #TODO Remove this method an use getCatalogsByTags instead (string and lists allowed)    
    def getCatalogsByTag(self, tag):
        """Gets all the catalogs with the given tag.
        Args:
            tag (str): the tag of the catalogs that are going to be returned.
        Returns:
            List[Catalog]: list of Catalogs with the given tag.
        """
        return self.getElementsByTag(tag, TYPE_CATALOG)
    
    def getCatalogsByTags(self, tags):
        """Gets the catalogs that contains a set of tags.
        Args:
            tags (List[Str]): a set of tags that are going to contain the returned Catalogs.
        Returns:
            List[Catalog]: a set of catalogs with the given set of tags.
        """
        return self.getElements(etype=TYPE_CATALOG, tags=tags)
    
    def hasCatalogs(self):
        """Checks if the mediapackage contains any Catalog
        Returns:
            Bool: True if the mediapackage contains any Catalog. False otherwise.
        """
        return self.hasElements(TYPE_CATALOG)
    
    def getUnclassifiedElement(self, identifier):
        """Gets a particular element of type other.
        Args:
            identifier (str): the identifier of the particular element.
        Returns:
            List[Other]: List of unclassified elements.
        """
        return self.getElementById(identifier, TYPE_OTHER)
    
    def getUnclassifiedElements(self, flavor=None):
        """Gets all the unclassifed elements (type other) with a particular flavor if specified.
        If no flavor is specified, returns all unclassified elements.
        Args:
            flavor (str): the flavor of the elements that are going to be returned.
        Returns:
            List[Other]: list of the elements typed other with a particular flavor if it is given.
        """
        return self.getElements(etype=TYPE_OTHER, flavor=flavor)
    
    #TODO Remove this method an use getUnclassifiedElementsByTags instead (string and lists allowed)    
    def getUnclassifiedElementsByTag(self, tag):
        """Gets all the unclassified elements (type other) with a particular tag.
        Args:
            tag (str): the tag of the elements that are going to be returned.
        Returns:
            List[Other]: list of the elements typed other with the given tag.
        """
        return self.getElementsByTag(tag, TYPE_OTHER)
    
    def getUnclassifiedElementsByTags(self, tags):
        """Gets the unclassified elements (type other) that contains a given set of tags.
        Args:
            tags (List[Str]): the set of tags that are going to contain the returned elements.
        Returns:
            List[Other]: list of the elements typed other with the given set of tags.
        """
        return self.getElements(etype=TYPE_OTHER, tags=tags)
    
    def hasUnclassifiedElements(self):
        """Checks if the mediapackage has any unclassified element.
        Returns:
            Bool: True if the mediapackage has one or more unclassified elements. False otherwise.
        """
        return self.hasElements(TYPE_OTHER)
    
    def add(self, item, etype=None, flavor=None, mime=None, duration=None, ref=None, identifier=None, tags=[]): # FIXME incluir starttime?
        """Creates if necessary and adds a new Element to the mediapackage.
        Args:
            item (str or Element): the element to be added or the URI of the new Element.
            etype (str): the type of the Elemet that is going to be added.
            flavor (str): the flavor of the Element that is going to be added.
            mime (str): the mime type of the Element that is going to be added.
            duration (int): the duration of the Element that is going to be added.
            ref (str): the reference of the Element that is going to be added.
            identifier (str): the identifier of the Element that is going to be added.
        Returns:
            Str: the identifier of the added element.
        Raises:
            ValueError: if the element type is invalid.
            RuntimeError: if the element is already added.
        """
        if isinstance(item, Element):
            elem = item
            etype = elem.getElementType()
        else:
            # Assuming item is a URI to the element (requires the etype is set)
            if (etype in ELEMENT_TYPES):
                if etype == TYPE_TRACK:
                    elem = Track(uri=item, duration=duration, flavor=flavor, mimetype=mime, identifier=identifier, tags=tags)
                elif etype == TYPE_ATTACHMENT:
                    elem = Attachment(uri=item, flavor=flavor, mimetype=mime, ref=ref, identifier=identifier, tags=tags)
                elif etype == TYPE_CATALOG:
                    elem = Catalog(uri=item, flavor=flavor, mimetype=mime, identifier=identifier, tags=tags)
                else: 
                    elem = Other(uri=item, flavor=flavor, mimetype=mime, identifier=identifier, tags=tags)
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

    def remove(self, arg, soft=False):
        """Removes the element referenced directly or by its identifier Element-X, for example catalog-2
        Args:
            arg(Element or str): the element to be removed or its identifier.
        Returns:
            Obj: removed element.
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

        if not soft:
            os.remove(elem.uri)

        return elem

    def getSize(self):
        """Gets the size of the files in the mediapackage directory (in bytes)
        Returns:
            Int: size (bytes) of the total element files in a mediapackage. 
        """
        size = 0
        for f in self.getElements():
            size += path.getsize(f.uri)
        #TODO taking into account the size of the xml or not.
        return size

    def getSizeByFlavors(self):
        """Returns:
            Dict{str,int}: a set of (flavor, size) that represents the size of the element files for each element type.		
        """
        info = {}        
        for f in self.getElements():
            # Sum size of elements with the same flavor
            if f.getFlavor() in info:
                info[f.getFlavor()] += path.getsize(f.getURI())
            else:
                info[f.getFlavor()] = path.getsize(f.getURI())

        return info

    def getURI(self):
        """Gets the URI of the mediapackage.
        Returns:
            Str: the absolute path of the mediapackage directory.
        """
        return self.uri


    def setURI(self, uri):
        """Sets the URI of the mediapackage.
        Args:
            uri (str): URI to be set.
        """
        self.uri = uri

       
    #FIXME merge with add
    def addDublincoreAsString(self, content, name=None, rewrite=False):
        """Writes information abaout an episode in a xml file.
        If name is not specified, the file is episode.xml.
        Args:
            content (str): content to be written in the xml file.
            name (str): name of the file.
            rewrite (bool): true if the file is going to be rewritten. False otherwise.
        """
        assert path.isdir(self.getURI())

        f_path = path.join(self.getURI(), name if name != None else 'episode.xml' ) #FIXME

        f = open(f_path, 'w')
        f.write(content)
        f.close()

        if not rewrite:
            self.add(f_path, TYPE_CATALOG, 'dublincore/episode', 'text/xml')


    def addSeriesDublincoreAsString(self, content, name=None, rewrite=False):
        """Writes information about a serie in a xml file.
        If name is not specified, the file is serie.xml
        Args:
            content (str): content to be written in the xml file.
            name (str): name of the file.
            rewrite (bool): true if the file is going to be rewritten. False otherwise.
        Note:        
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
        """Internal function to marshal mediapackage atributes and metadata_episode dict with Dubincore episode file
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
                                try:
                                    self.setDate(datetime.strptime(creat, "%Y-%m-%dT%H:%M:%SZ"))
                                except:
                                    self.setDate(datetime.strptime(creat, "%Y-%m-%d %H:%M:%SZ"))
                            else:
                                try:
                                    self.setDate(datetime.strptime(creat, "%Y-%m-%dT%H:%M:%S")) 
                                except:
                                    self.setDate(datetime.strptime(creat, "%Y-%m-%d %H:%M:%S"))

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
                    if not node.nodeName.count('dcterms:'):
                        continue
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
                self.setDate(start)
            except:
                pass
            
    #FIXME merge with add
    def addAttachmentAsString(self, content, name=None, rewrite=False, identifier=None):
        """Adds the information of an attachment in a file.
        If no name is specified, file is going to be named as data.
        Args:
            content (str): the information about the attachment element to be written.
            name (str): the name of the file.
            rewrite (bool): true if the file is going to be rewritten. False otherwise.
            identifier (str): the identifier of the attachment element.
        """
        assert path.isdir(self.getURI())

        f_path = path.join(self.getURI(), name if name != None else 'data' )

        f = open(f_path, 'w')
        f.write(content)
        f.close()

        if not rewrite:
            self.add(f_path, etype=TYPE_ATTACHMENT, identifier=identifier)


    def getOCCaptureAgentProperty(self, name):
        # FIXME refactor
        """Tries the value of a property in the opencast's configuration file.
        If any error is catched, it returns none.
        Args:
            name (str): name of the property
        Returns:
            Str: Value of the property.
        """
        try:
            attach = self.getAttachment('org.opencastproject.capture.agent.properties')
            values = dict(read_ini(attach.getURI()))
            return values[name]
        except:
            return None


    def getOCCaptureAgentProperties(self):
        # FIXME refactor
        """Tries to get the properties of the opencast's configuration file.
        If any error is catched, it returns an empty dictionary.
        Returns:
            Dict{Str,Str}: a dictionary with the name of all the properties of the opencast's config file and its values.
        """
        try:
            attach = self.getAttachment('org.opencastproject.capture.agent.properties')
            return dict(read_ini(attach.getURI()))
        except:
            return {}


    def setProperty(self, prop=None, value=None):
        """Sets the value of a property in the mediapackage.
        Args:
            prop (str): the name of the property.
            value (str): the new value of the property name.
        """
        if not prop or not value:
            return None
        else:
            self.properties[prop] = value
            return True


    def getProperty(self, prop=None):
        """Gets the property specified of the mediapackage.
        Returns:
            Obj: the object with the value of the property specified
        """
        if not prop:
            return None
        else:
            if prop in self.properties:
                return self.properties[prop]
            else:
                return None
