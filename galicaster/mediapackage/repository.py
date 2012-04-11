# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/mediapackage/repository
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import logging
import os
from shutil import rmtree
from datetime import datetime

from galicaster.mediapackage import mediapackage
from galicaster.mediapackage import serializer
from galicaster.mediapackage import deserializer

logger = logging.getLogger()

class Repository(object):
    attach_dir = 'attach'

    def __init__(self, root=None):
        """
        FIXME doc

        param: root...
        """ 
        self.root = root or os.path.expanduser('~/Repository')

        if not os.path.isdir(self.root):
            os.mkdir(self.root)
            
        if not os.path.isdir(os.path.join(self.root, self.attach_dir)):
            os.mkdir(os.path.join(self.root, self.attach_dir))
            
        self.__list = dict()
        self.refresh()


    def refresh(self):
        self.__list.clear()
        if self.root != None:
            for folder in os.listdir(self.root):
                if folder == self.attach_dir:
                    continue
                try:
                    manifest = os.path.join(self.root, folder, "manifest.xml")
                    if os.path.exists(manifest):
                        novo = deserializer.fromXML(manifest)
                        self.__list[novo.getIdentifier()] = novo
                except:
                    logger.error('Error in deserializer {0}'.format(folder))


    def list(self):
        return self.__list


    def list_by_status(self, status):
        def is_valid(mp):
            return mp.status == status

        next = filter(is_valid, self.__list.values())
        return next

    def size(self):
        return len(self.__list)

    def values(self):
        return self.__list.values()

    def items(self):
        return self.__list.items()

    def iteritems(self):
        return self.__list.iteritems()

    def __iter__(self):
        return self.__list.__iter__()

    def __len__(self):
        return len(self.__list)

    def __contains__(self, v):
        return v in self.__list

    def __getitem__(self, k):
        return self.__list[k]

    def filter(self):
        # TODO filter by certain parameters
        return self.__list

    def get_next_mediapackages(self):
        """
        Return de next mediapackages to be record.
        """
        def is_future(mp):
            return mp.getDate() > datetime.utcnow()

        next = filter(is_future, self.__list.values())
        next = sorted(next, key=lambda mp: mp.startTime) 
        return next


    def get_next_mediapackage(self):
        """
        Retrive de next mediapackage to be record.
        """
        next = None
        for mp in self.__list.values():
            if mp.getDate() > datetime.utcnow():
                if next == None:
                    next = mp
                else:
                    if mp.getDate() < next.getDate():
                        next = mp

        return next


    def get(self, key):
        """Returns the Mediapackage identified by key"""
        return self.__list.get(key)


    def has(self, mp):
        return self.__list.has_key(mp.getIdentifier())


    def has_by_key(self, key):
        return self.__list.has_key(key)
    

    def add(self, mp):
        if self.has(mp):
            raise KeyError('Key Repeated')
        if mp.getURI() == None:
            mp.setURI(self.__get_folder_name())
        else:
            assert mp.getURI().startswith(self.root + os.sep)            
        os.mkdir(mp.getURI())

        return self.__add(mp)


    def add_after_rec(self, mp, bins, duration):
        if not self.has(mp):
            mp.setURI(self.__get_folder_name())
            os.mkdir(mp.getURI())

        for bin in bins:
            if mp.manual or (mp.getOCCaptureAgentProperty('capture.device.names') 
                             and bin['name'] in mp.getOCCaptureAgentProperty('capture.device.names')):
                filename = bin['file']
                dest = os.path.join(mp.getURI(), os.path.basename(filename))
                os.rename(filename, dest)
                etype = 'audio/mp3' if bin['klass'] in ['pulse.GCpulse'] else 'video/' + dest.split('.')[1].lower()
                flavour = bin['options']['flavor'] + '/source'
                mp.add(dest, mediapackage.TYPE_TRACK, flavour, etype, duration) # FIXME MIMETYPE
        mp.forceDuration(duration)
        # ADD MP to repo
        self.__add(mp) 
        


    def delete(self, mp):
        if not self.has(mp):
            raise KeyError('Key not Exists')

        del self.__list[mp.getIdentifier()]
        rmtree(mp.getURI())
        return mp

        
    def update(self, mp):
        if not self.has(mp):
            raise KeyError('Key not Exists')
        #Si cambio URI error.
        return self.__add(mp)
            

    def get_new_mediapackage(self, name=None, add_episode=True, timestamp=None):
        folder = self.__get_folder_name(name)
        mp = mediapackage.Mediapackage(uri=folder, date=timestamp)
        if add_episode:
            mp.add(os.path.join(folder, 'episode.xml'), mediapackage.TYPE_CATALOG, 'dublincore/episode', 'text/xml')
        return mp

    def save_attach(self, name, data):
        m = open(os.path.join(self.root, self.attach_dir, name), 'w')  
        m.write(data)  
        m.close()
        
    def get_attach(self, name):
        return open(os.path.join(self.root, self.attach_dir, name))  

    def get_attach_path(self):
        return os.path.join(self.root, self.attach_dir)

    def __get_folder_name(self, name=None):
        if name == None:
            timestamp = datetime.now().replace(microsecond=0).isoformat()
            folder = os.path.join(self.root, "gc_" + timestamp)
        else:
            folder = os.path.join(self.root, "gc_" + name)
        
        return folder

    def __add(self, mp):
        self.__list[mp.getIdentifier()] = mp
        serializer.save_in_dir(mp)
        #FIXME escribir de nuevo los XML de metadata.xml y episode.xml y series.xml
        return mp
        
    



    
    
