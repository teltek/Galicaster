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
import datetime
import re
import itertools
from shutil import rmtree
import ConfigParser

from galicaster import __version__
from galicaster.mediapackage import mediapackage
from galicaster.mediapackage import serializer
from galicaster.mediapackage import deserializer

logger = logging.getLogger()


class Repository(object):
    attach_dir = 'attach'

    def __init__(self, root=None, hostname='', 
                 folder_template='gc_{hostname}_{year}-{month}-{day}T{hour}h{minute}m{second}'):
        """
        param: root: absolute path to the working folder. ~/Repository use if is None
        param: hostname: galicaster name use in folder prefix
        param: folder_template
        """ 
        self.root = root or os.path.expanduser('~/Repository')

        self.hostname = hostname
        self.folder_template = folder_template

        self.create_repo(hostname)

        self.__list = dict()
        self.refresh(True)


    def create_repo(self, hostname):
        if not os.path.isdir(self.root):
            os.mkdir(self.root)
            
        if not os.path.isdir(os.path.join(self.root, self.attach_dir)):
            os.mkdir(os.path.join(self.root, self.attach_dir))

        info_repo_file = os.path.join(self.root, self.attach_dir, 'info.ini')
        if not os.path.isfile(info_repo_file):
            with open(info_repo_file, 'wb') as configfile:
                conf = ConfigParser.ConfigParser() 
                conf.add_section('repository')
                conf.set('repository', 'version', __version__)
                conf.set('repository', 'hostname', hostname)
                conf.write(configfile)
        

    def refresh(self, check_inconsistencies=False):
        self.__list.clear()
        if self.root != None:
            for folder in os.listdir(self.root):
                if folder == self.attach_dir:
                    continue
                try:
                    manifest = os.path.join(self.root, folder, "manifest.xml")
                    if os.path.exists(manifest):
                        new_mp = deserializer.fromXML(manifest)
                        self.__list[new_mp.getIdentifier()] = new_mp
                        if check_inconsistencies: self.repair_inconsistencies(new_mp)
                except:
                    logger.error('Error in deserializer {0}'.format(folder))


    def repair_inconsistencies(self, mp):
        """
        Check if any operations was being processed before the previous running
        """
        change = False
        if mp.status > mediapackage.FAILED:
            mp.status = mediapackage.RECORDED
            change = True
        for (op_name, op_value) in mp.operation.iteritems():
            if op_value in [mediapackage.OP_PROCESSING, mediapackage.OP_PENDING]:
                mp.setOpStatus(op_name, mediapackage.OP_FAILED)
                change = True

        if change:
            self.update(mp)


    def list(self):
        return self.__list


    def list_by_status(self, status):
        def is_valid(mp):
            return mp.status == status

        next = filter(is_valid, self.__list.values())
        return next


    def list_by_operation_status(self, job, status):
        def is_valid(mp):
            return (mp.getOpStatus(job) == status)

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
            return mp.getDate() > datetime.datetime.utcnow()

        next = filter(is_future, self.__list.values())
        next = sorted(next, key=lambda mp: mp.startTime) 
        return next


    def get_next_mediapackage(self):
        """
        Retrive de next mediapackage to be record.
        """
        next = None
        for mp in self.__list.values():
            if mp.getDate() > datetime.datetime.utcnow():
                if next == None:
                    next = mp
                else:
                    if mp.getDate() < next.getDate():
                        next = mp

        return next


    def get_past_mediapackages(self, days=0):
        """
        Return de next mediapackages to be record.
        """
        def is_stale(mp):
            return mp.getDate() < (datetime.datetime.utcnow() - datetime.timedelta(days=days))

        next = filter(is_stale, self.__list.values())
        next = sorted(next, key=lambda mp: mp.startTime) 
        return next


    def get(self, key):
        """Returns the Mediapackage identified by key"""
        return self.__list.get(key)


    def has(self, mp):
        return self.__list.has_key(mp.getIdentifier())


    def has_key(self, key):
        return self.__list.has_key(key)
    

    def add(self, mp): 
        if self.has(mp):
            raise KeyError('Key Repeated')
        if mp.getURI() == None:
            mp.setURI(self.__get_folder_name(mp))
        else:
            assert mp.getURI().startswith(self.root + os.sep)            
        os.mkdir(mp.getURI())

        return self.__add(mp)


    def add_after_rec(self, mp, bins, duration, add_catalogs=True): 
        if not self.has(mp):
            mp.setURI(self.__get_folder_name(mp))
            os.mkdir(mp.getURI())

        for bin in bins:
            # TODO rec all and ingest 
            capture_dev_names = mp.getOCCaptureAgentProperty('capture.device.names')
            if mp.manual or len(capture_dev_names) == 0 or capture_dev_names == 'defaults' or bin['name'] in capture_dev_names:
                filename = os.path.join(bin['path'], bin['file'])
                dest = os.path.join(mp.getURI(), os.path.basename(filename))
                os.rename(filename, dest)
                etype = 'audio/mp3' if bin['device'] in ['pulse','audiotest','rtpaudio'] else 'video/' + dest.split('.')[1].lower()
                flavour = bin['flavor'] + '/source'
                mp.add(dest, mediapackage.TYPE_TRACK, flavour, etype, duration) # FIXME MIMETYPE
        mp.forceDuration(duration)

        if add_catalogs:
            mp.add(os.path.join(mp.getURI(), 'episode.xml'), mediapackage.TYPE_CATALOG, 'dublincore/episode', 'text/xml')
            if mp.series:
                mp.add(os.path.join(mp.getURI(), 'series.xml'), mediapackage.TYPE_CATALOG, 'dublincore/series', 'text/xml')

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


    def save_attach(self, name, data):
        m = open(os.path.join(self.root, self.attach_dir, name), 'w')  
        m.write(data)  
        m.close()
        

    def get_attach(self, name):
        return open(os.path.join(self.root, self.attach_dir, name))  


    def get_attach_path(self, name=None):
        if name:
            return os.path.join(self.root, self.attach_dir, name)
        else:
            return os.path.join(self.root, self.attach_dir)


    def __get_folder_name(self, mp):
        mappings = {
            'id'       : mp.identifier,
            'title'    : mp.title, 
            'series'   : mp.series_title, 
            'hostname' : self.hostname, 
            'type'     : 'M' if mp.manual else 'S',
            'longtype' : 'manual' if mp.manual else 'scheduled',
            'year'     : mp.getDate().strftime('%Y'),
            'month'    : mp.getDate().strftime('%m'),
            'day'      : mp.getDate().strftime('%d'),
            'hour'     : mp.getDate().strftime('%H'),
            'minute'   : mp.getDate().strftime('%M'),
            'second'   : mp.getDate().strftime('%S')}
        
        base = folder_name = re.sub(r'\W+', '', self.folder_template.format(**mappings))
        
        # Check if folder_name exists
        count = itertools.count(2)
        while os.path.exists(os.path.join(self.root, folder_name)):
            folder_name = (base + "_" + str(next(count)))

        return os.path.join(self.root, folder_name)


    def __add(self, mp):
        self.__list[mp.getIdentifier()] = mp
        serializer.save_in_dir(mp)
        #FIXME escribir de nuevo los XML de metadata.xml y episode.xml y series.xml
        return mp
        
    
