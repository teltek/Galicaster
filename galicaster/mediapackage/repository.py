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

import os
import datetime
import re
import itertools
import glob, json
import shutil
import ConfigParser

from galicaster import __version__
from galicaster.mediapackage import mediapackage
from galicaster.mediapackage import serializer
from galicaster.mediapackage import deserializer

"""
This class manages (add, list, remove...) all the mediapackages in the repository.
"""
class Repository(object):
    attach_dir = 'attach'
    rectemp_dir = 'rectemp'
    repo_dirs = (attach_dir, rectemp_dir)

    def __init__(self, root=None, hostname='', 
                 folder_template='gc_{hostname}_{year}-{month}-{day}T{hour}h{minute}m{second}',
                 logger=None):
        """Initializes a repository that will contain a set of mediapackage.
        Args:
            root (str): absolute path to the working folder. ~/Repository used if it is None
            hostname (str): galicaster name use in folder prefix
            folder_template (str): name of the mediapackage folder with the timestamp. See get_folder_name mapping.
            logger (Logger): logger that prints information, warnings and errors in the log file. See galicaster/context/logger
        Attributes:
            __list (Dict{str,Mediapackage}): the mediapackages in the repository and its identifiers as keys
        """
        self.logger = logger

        if not root:
            self.root = os.path.expanduser('~/Repository')
            self.logger and self.logger.warning("Repository folder not specified, using {}".format(self.root))
        else:
            self.root = root


        self.hostname = hostname
        self.folder_template = folder_template

        self.create_repo(hostname)        

        self.__list = dict()
        self.check_for_recover_recordings()
        
        if self.logger:
            self.logger.info("Creating repository from {}".format(self.root))
        self.__list.clear()
        self.__refresh(True)


    def create_repo(self, hostname):
        """Creates the directories root and repository if necessary.      
        Configures the information repository file.
        Sets version and hostname information.
        Args:
            hostname (str): galicaster name used in folder prefix .
        """
        if not os.path.isdir(self.root):
            os.mkdir(self.root)
           
        for repo_dir in self.repo_dirs:
            if not os.path.isdir(os.path.join(self.root, repo_dir)):
                os.mkdir(os.path.join(self.root, repo_dir))

        info_repo_file = os.path.join(self.root, self.attach_dir, 'info.ini')
        if not os.path.isfile(info_repo_file):
            with open(info_repo_file, 'wb') as configfile:
                conf = ConfigParser.ConfigParser() 
                conf.add_section('repository')
                conf.set('repository', 'version', __version__)
                conf.set('repository', 'hostname', hostname)
                conf.write(configfile)


    def check_for_recover_recordings(self):
        """If a manifest.xml file exists, calls the recover_recoding method.
        If else, calls the save_crash_recordings method. 
        """
        if os.path.exists(os.path.join(self.get_rectemp_path(), "manifest.xml")):
            self.logger and self.logger.info("Found a recording that has crashed")
            self.crash_file_creator()
            self.recover_recording()
        else:
            self.save_crash_recordings()



    def recover_recording(self):
        """Tries to recover a crashed mediapackage form the manifest.xml associated.
        If any exception occurs while recovering recording, calls save_crash_recording method.
        """
        try:
            self.logger and self.logger.info("Trying to recover the crashed recording")

            ca_prop = None
            info = {}
            # Read info.json
            with open(os.path.join(self.get_rectemp_path(), "info.json"), 'r') as handle:
                info = json.load(handle)

            # Copy the capture agent properties from the original mediapackage folder (for scheduled recordings)
            if info['mp_path']:
                ca_prop = os.path.join(info['mp_path'], "org.opencastproject.capture.agent.properties")
                if os.path.exists(ca_prop):
                    with open(ca_prop, 'rb') as fsrc:
                        dst = os.path.join(self.get_rectemp_path(), "org.opencastproject.capture.agent.properties")
                        with open(dst, 'wb') as fdst:
                            self.logger.info("Copying file {} to {}".format(ca_prop, dst))
                            shutil.copyfileobj(fsrc, fdst)
                            os.fsync(fdst)

            mp = deserializer.fromXML(os.path.join(self.get_rectemp_path(), "manifest.xml"), self.logger)

            # Status to RECORDED
            mp.status = 4
            mp.setTitle("Recovered recording of date {}".format(mp.getStartDateAsString()))
            mp.setNewIdentifier()
            info['mp_id'] = mp.getIdentifier()

            # Change the filenames 
            folder = self.add_after_rec(mp, info['tracks'], mp.getDuration(), add_catalogs=True, remove_tmp_files=False)
            serializer.save_in_dir(mp, self.logger, folder)
            self.logger and self.logger.info("Crashed recording added to the repository")

            # Copy the capture agent properties from the original mediapackage folder (for scheduled recordings)
            if ca_prop and os.path.exists(ca_prop):
                with open(ca_prop, 'rb') as fsrc:
                    dst = os.path.join(mp.getURI(), "org.opencastproject.capture.agent.properties")
                    with open(dst, 'wb') as fdst:
                        self.logger.info("Copying file {} to {}".format(ca_prop, dst))
                        shutil.copyfileobj(fsrc, fdst)
                        os.fsync(fdst)

            # Check if there is some extra files (slides) and move the the mediapackage folder
            mp_dir = mp.getURI()
            for temp_file in os.listdir(self.get_rectemp_path()):
                full_path = os.path.join(self.get_rectemp_path(), temp_file)
                if os.path.isfile(full_path) and os.path.getsize(full_path) and not "screenshot.jpg" in temp_file:
                    os.rename(full_path, os.path.join(mp_dir, temp_file))

        except Exception as exc:
            self.logger and self.logger.error("There was an error trying to recover a recording: {}. Saving crashed recording to a rectemp folder...".format(exc))
            self.save_crash_recordings()

        return
        
            
    def save_crash_recordings(self):
        """Saves the files with the crashed recordings in a directory named with its timestamp. 
        """
        backup_dir = self.get_rectemp_path(datetime.datetime.now().replace(microsecond=0).isoformat())
        for temp_file in os.listdir(self.get_rectemp_path()):
            full_path = os.path.join(self.get_rectemp_path(), temp_file)

            if os.path.isfile(full_path) and os.path.getsize(full_path):
                self.crash_file_creator()

                if not os.path.isdir(backup_dir):
                    os.mkdir(backup_dir)                    
                os.rename(full_path, os.path.join(backup_dir, temp_file))


    def crash_file_exists(self):
        """Checks if the hidden file ".recording_crash" exists.
        Returns:
            Bool: True if exists. False otherwise.
        """
        filename = os.path.join(self.get_rectemp_path(), ".recording_crash")
        if os.path.isfile(filename):
            return True
        else:
            return False
    

    def crash_file_creator(self):
        """Creates a empty file named .recording_crash in the temporary recordings directory"""
        filename = os.path.join(self.get_rectemp_path(), ".recording_crash")
        file = open(filename, 'w')
        file.close()
        return


    def crash_file_remover(self):
        """Removes the hidden file .recording_crash in the temporary recordings directory"""
        filename = os.path.join(self.get_rectemp_path(), ".recording_crash")
        os.remove(filename)
        return


    
    def save_current_mp_data(self, mp, bins_info):
        # Save the current mediapackage
        serializer.save_in_dir(mp, self.logger, self.get_rectemp_path())

        try:
            info = {}
            info['scheduled'] = True if mp.status == mediapackage.SCHEDULED else False
            info['mp_id']     = mp.getIdentifier()
            info['mp_path']   = mp.getURI()
            info['start']     = mp.getDate().isoformat()
            info['tracks']    = bins_info
            
            filename = os.path.join(self.get_rectemp_path(), 'info.json')
            f = open(filename, 'w')
            f.write(json.dumps(info, indent=4, sort_keys=True))
            f.close()

            self.logger and self.logger.debug("Temporal data saved to {}".format(filename))
        except Exception as exc:
            self.logger and self.logger.error("Problem on save temporal data: {}".format(exc))


    

    def __refresh(self, check_inconsistencies=False, first_time=True):
        """Tries to check if it's been done a new recording. If true, it updates the repository with the new recordings.
        If error, logs it appropriately.
        Args:
            check_inconsistencies (bool): True if inconsistencies are going to be checked. False otherwise.
            first_time (bool): True if Galicaster is refreshing its repository while starting. False otherwise. Used to avoid logging that the mediapackages are added the first time.
        """
        if self.logger:
            self.logger.info("Refreshing repository list")

        if self.root != None:
            for folder in os.listdir(self.root):
                if folder in self.repo_dirs:
                    continue
                try:
                    manifest = os.path.join(self.root, folder, "manifest.xml")
                    if os.path.exists(manifest):
                        new_mp = deserializer.fromXML(manifest, self.logger)

                        if not self.__contains__(new_mp.getIdentifier()):
                            self.__list[new_mp.getIdentifier()] = new_mp
                            if check_inconsistencies: 
                                self.repair_inconsistencies(new_mp)
                            self.logger and not first_time and self.logger.info("Added new MP {} of folder {}".format(new_mp.getIdentifier(), new_mp.getURI()))
                        else:
                            self.logger and first_time and self.logger.warning("Found duplicated MP id {} so ignoring {}".format(new_mp.getIdentifier(), new_mp.getURI()))
                except Exception as exc:
                    if self.logger:
                        self.logger.error('Error in deserializer {0}. Exception: {1}'.format(folder, exc))


    def repair_inconsistencies(self, mp):
        """Checks if any operations were being processed before the previous running.
        If true, update the mediapackage.    
        Args:
            mp (Mediapackage): the mediapackage whose inconsistencies are going to be repaired.
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
        """Gets the set of mediapackages in the repository and its identifiers as a dictionary.
        Returns:
            Dict{str,Mediapackage}: the complete list of mediapackages and its identifiers (as keys) in the repository.
        """
        return self.__list


    def list_by_status(self, status):
        """Gets the mediapackages with a particular status.
        Args:
            status (str): the status of the mediapackage that are going to be obtained.
        Returns:
            List[Mediapackage]: the list of mediapackages in the repository that has the status given.
        """
        def is_valid(mp):
            """Checks if the status of the mediapackage is the same as the status recieved as an argument in list_by_status.
            Args:
                mp (Mediapackage): the mediapackage whose status is going to be checked.
            Returns:
                Bool: True if the status match. False otherwise.
            """
            return mp.status == status

        next = filter(is_valid, self.__list.values())
        return next


    def list_by_operation_status(self, job, status):
        """Gets the mediapackages with a particular operation in a particular status.
        Args:
            job (str): name of the operation.
            status (int): status of the operation. See Mediapackage constants in galicaster/mediapackage/mediapackage.py .
        Returns:
            List[Mediapackage]: the list of mediapackages in the repository that have the given operation with the given status.
        """

        def is_valid(mp):
            """Checks if the status of the given operation of the mediapackage is in the given status.
            Args:
                mp (Mediapackage): mediapackage whose operations status are going to be checked.
            Returns:
                Bool: True if the status of the operation job match. False otherwise.
            """
            return (mp.getOpStatus(job) == status)

        next = filter(is_valid, self.__list.values())
        return next


    def size(self):
        """Gets the number of mediapackages in the repository.
        Returns:
            Int: the quantity of mediapackages in the repository.
        """
        return len(self.__list)

    def values(self):
        """Gets al the mediapackages from the repository.
        Returns:
            List[Mediapackage]: list of all the mediapackages in the repository.
        """
        return self.__list.values()

    def items(self):
        """Gets all the mediapackages from the repository and its identifiers as a list of pairs.
        Returns:
            List[(str,Mediapackage)]: the complete list of pairs (mediapackage ID, mediapackage) in the repository.
        """
        return self.__list.items()

    def iteritems(self):
        """Gets a generator of a list with all the mediapackages from the repository and its identifiers as a list of pairs.
        Returns:
            List[(str,Mediapackage)]: a generator of the complete list of pairs (mediapackage ID, mediapackage) in the repository. 
        """
        # Avoid error: dictionary changed size during iteration
        to_return = self.__list.copy()
        return to_return.iteritems()

    def __iter__(self):
        """Allows the Repository to be iterable so that it's possible to obtain a list of mediapackages identifiers in the repository
        Returns:
            List[str]: a generator of the complete list of mediapackages identifiers.
        """
        return self.__list.__iter__()

    def __len__(self):
        """Gets the size of the repository.
        Returns:
            Int: the quantity of mediapackages in the repository.
        """
        return len(self.__list)

    def __contains__(self, v):
        """Checks if the repository contains a mediapackage with the given identifier.
        Args:
            v (str): mediapackage ID
        Returns:
            Bool: True if the set of keys from __list contains v. False otherwise.    
        """
        return v in self.__list

    def __getitem__(self, k):
        """Gets the mediapackage with the given identifier.    
        Args:
            k: ID of a mediapackage
        Returns:
            Mediapackage: mediapackage with the ID k
        """
        return self.__list[k]

    def filter(self):
        # TODO filter by certain parameters
        return self.__list

    def get_next_mediapackages(self):
        """Gets the mediapackage that are going to be recorded in the future.
        Returns:
            List[Mediapackage]: list of mediapackages to be recorded in the future, sorted by the start time.
        """
        def is_future(mp):
            """Checks if the date of a mediapackage is later than now.
            Args:
                mp: the mediapackage whose recording date is going to be checked.
            Returns:
                Bool: True if the date is later than now. False otherwise.
            """
            return mp.getDate() > datetime.datetime.utcnow()

        next = filter(is_future, self.__list.values())
        next = sorted(next, key=lambda mp: mp.startTime) 
        return next


    def get_next_mediapackage(self):
        """Gets the mediapackage that is going to be recorded next.
        Returns:
            Mediapackage: the next mediapackage to be recorded.
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


    def get_last_mediapackage(self):
        """Gets the last mediapackage added to the repository.
        Returns:
            Mediapackage: the last mediapackage added.
        """

        RECORDED = 4

        def is_recorded(mp):
            """Checks if the given mediapackage recording date is sooner than now-days.
            Args:
                mp: the mediapackage whose recording date is going to be checked.
            Returns:
                Bool: True if the date of the mediapackage is sooner than now-days. False otherwise.
            """
            return True if mp.status == RECORDED else False

        next = filter(is_recorded, self.__list.values())
        mps_sorted = sorted(next, key=lambda mp: (mp.getDate()), reverse=True)

        if mps_sorted:
            return mps_sorted[0]

        return None


    def get_past_mediapackages(self, days=0):
        """Gets the mediapackage that has been recorded before the given amount of days.
        Args:
            days (int): the actual date must be decremented this amount of days to obtain the date until we want to get recordings.
        Returns:
            List[Mediapackage]: list of the mediapackages that were recorded before (now-days)
        """
        def is_stale(mp):
            """Checks if the given mediapackage recording date is sooner than now-days.
            Args:
                mp: the mediapackage whose recording date is going to be checked.
            Returns:
                Bool: True if the date of the mediapackage is sooner than now-days. False otherwise.
            """
            return mp.getDate() < (datetime.datetime.utcnow() - datetime.timedelta(days=days))

        next = filter(is_stale, self.__list.values())
        next = sorted(next, key=lambda mp: mp.startTime) 
        return next


    def get(self, key):
        """Gets the mediapackage with the specified identifier.
        Args:
            key (str): the ID from the mediapackage that is going to be returned.
        Returns:
            Mediapackage: the Mediapackage identified by the given key.
        """
        return self.__list.get(key)


    def has(self, mp):
        """Checks if a mediapackage is in the repository.
        Args:
            mp (Mediapackage): mediapackage.
        Returns:
            Bool: True if the mediapackage mp is in the repository. False otherwise. 
        """
        return self.__list.has_key(mp.getIdentifier())


    def has_key(self, key):
        """Checks if the repository has a mediapackage with a particular ID.
        Args:
            key (str): the ID ftom the mediapackage we want to know if it's on the repository
        Returns:
            Bool: True if the repository has a mediapackage with the ID key. False otherwise.
        """
        return self.__list.has_key(key)
    

    def add(self, mp): 
        """Checks if the mediapackage already exists and the URI is correct.
        If it hasn't have URI, calls the __get_folder_name method.
        Then calls the private method __add.
        Args:
            mp (Mediapackage): the mediapackage to be added.
        Returns:
            Mediapackage: the medipackage that has been added.
        Raises:
            KeyError: if the ID of the mediapackage is already in the repository.
        """
        if self.has(mp):
            raise KeyError('Key Repeated')
        if mp.getURI() == None:
            mp.setURI(self.__get_folder_name(mp))
        else:
            assert mp.getURI().startswith(self.root + os.sep)            
        os.mkdir(mp.getURI())

        return self.__add(mp)


    def add_after_rec(self, mp, bins, duration, add_catalogs=True, remove_tmp_files=True): 
        """Adds information to the mediapackage when a recording ends and adds it to the repository.
        Args:
            mp (Mediapackage): the mediapackage whose recordings are going to be updated.
            bins (Dict{str,str}): the information about mediapackage recordings.
            duration (str): duration of the mediapackage.
            add_catalogs (bool): true if the mediapackage belongs to a catalog, false otherwise.
            remove_tmp_files (bool): true if the temporary file are going to be removed. 
        Returns:
            Str: the URI of the mediapackage
        """
        if not self.has(mp):
            mp.setURI(self.__get_folder_name(mp))
            os.mkdir(mp.getURI())

        for bin in bins:
            # TODO rec all and ingest 
            capture_dev_names = mp.getOCCaptureAgentProperty('capture.device.names')
            if mp.manual or not capture_dev_names or len(capture_dev_names) == 0 or capture_dev_names == 'defaults' or bin['name'] in capture_dev_names:
                filename = os.path.join(bin['path'], bin['file'])
                dest = os.path.join(mp.getURI(), os.path.basename(filename))
                os.rename(filename, dest)
                etype = 'audio/mp3' if bin['device'] in ['pulse', 'autoaudio', 'audiotest'] else 'video/' + dest.split('.')[1].lower()
                
                flavour = bin['flavor'] + '/source'

                mp.add(dest, mediapackage.TYPE_TRACK, flavour, etype, duration) # FIXME MIMETYPE
            else:
                self.logger and self.logger.debug("Not adding {} to MP {}").format(bin['file'],mp.getIdentifier())

        mp.forceDuration(duration)

    
        if add_catalogs:
            mp.add(os.path.join(mp.getURI(), 'episode.xml'), mediapackage.TYPE_CATALOG, 'dublincore/episode', 'text/xml')
            if mp.getSeriesIdentifier():
                mp.add(os.path.join(mp.getURI(), 'series.xml'), mediapackage.TYPE_CATALOG, 'dublincore/series', 'text/xml')

        # ADD MP to repo
        self.__add(mp) 

        # Remove temporal files
        self._manage_tmp_files(remove_tmp_files, mp.getURI())

        return mp.getURI()


    def _manage_tmp_files(self, remove_tmp_files, folder):
        """Manages the temporary files being removed or moved.
        Args:
            remove_tmp_files (bool): true if the temporary files are going to be removed. False if they're going to be moved.
            folder (str): if remove_tmp_file is false, these are moved to this folder.
    """
        temporal_files = ['{}/*.json'.format(self.get_rectemp_path()),
                          '{}/*.xml'.format(self.get_rectemp_path())]
        
        for expr in temporal_files:
            files = glob.glob(expr)
            if files:
                for filename in files:
                    if remove_tmp_files:
                        os.remove(filename)
                    else:
                        os.rename(filename, os.path.join(folder, os.path.basename(filename)))

        if self.crash_file_exists():
            self.crash_file_remover()

        if remove_tmp_files:
            self.logger and self.logger.info("Repository temporal files removed")
        else:
            self.logger and self.logger.info("Repository temporal files moved to {}".format(folder))

    def delete(self, mp):
        """Deletes a mediapackage from de repository.
        Args:
            mp (Mediapackage): the mediapackage that is going to be removed.
        Returns:
            Mediapackage: the removed mediapackage.
        Raises:
            KeyError: if the mediapackage is not in the repository.
        """
        if not self.has(mp):
            raise KeyError('Key not Exists')

        del self.__list[mp.getIdentifier()]
        shutil.rmtree(mp.getURI())
        return mp

        
    def update(self, mp):
        """If a mediapackage is in the repository, calls the private method __add in order to add it to the repository.
        Args:
            mp (Mediapackage): the mediapackage that is going to be added.
        Returns:
            Mediapackage (Mediapackage): updated madiapackage.
        Raises:
            KeyError: if key doesn't exist.
        """
        if not self.has(mp):
            raise KeyError('Key not Exists')
        # If change the URI gives error.
        return self.__add(mp)


    def save_attach(self, name, data):
        """Writes data in a file of the attach directory.
        Args:
            name (str): name of the file that is going to be modified.
            data (str): data to be written in the file.
        """
        with open(os.path.join(self.root, self.attach_dir, name), 'w') as m:
            m.write(data)  
        

    def get_attach(self, name):
        """Opens a file of the attached directory.
        Args:
            name (str): name of the file to be opened.
        Returns:
            Bool: True if not errors. False otherwise.
        """
        return open(os.path.join(self.root, self.attach_dir, name))  


    def get_attach_path(self, name=None):
        """Gets the path of the attach folder.
        Args:
            name (str): name of a file in the attach folder.
        Returns:
            Str: absolute path of the attach directory or a file in this folder if the name is specified.
        """
        if name:
            return os.path.join(self.root, self.attach_dir, name)
        else:
            return os.path.join(self.root, self.attach_dir)


    def get_rectemp_path(self, name=None):
        """Gets the temporary recording directory path.
        Returns:
            Str: path from the temporary recording directory.
        """
        if name:
            return os.path.join(self.root, self.rectemp_dir, name)
        else:
            return os.path.join(self.root, self.rectemp_dir)


    def get_free_space(self):
        """Gets the free space in the folder.
        Returns:
            Int: Free space in the folder.
        """
        s = os.statvfs(self.root)
        return s.f_bsize * s.f_bavail


    def __get_folder_name(self, mp):
        """Sets the absolute path of the folder where a mediapackage is by adding the correct timestamp.
        Args:
            mp (Mediapackage): the mediapackage whose folder is going to be created.
        Returns:
            Str: absolute path of the folder where the given mediapackage is.
        """
        utcdate = mp.getDate()
        date = mp.getLocalDate()

        mappings = {
            'id'          : mp.identifier,
            'title'       : mp.getTitle(), 
            'series'      : mp.getSeriesTitle(),
            'hostname'    : self.hostname, 
            'type'        : 'M' if mp.manual else 'S',
            'longtype'    : 'manual' if mp.manual else 'scheduled',
            'year'        : date.strftime('%Y'),
            'month'       : date.strftime('%m'),
            'day'         : date.strftime('%d'),
            'hour'        : date.strftime('%H'),
            'minute'      : date.strftime('%M'),
            'second'      : date.strftime('%S'),
            'utcyear'     : utcdate.strftime('%Y'),
            'utcmonth'    : utcdate.strftime('%m'),
            'utcday'      : utcdate.strftime('%d'),
            'utchour'     : utcdate.strftime('%H'),
            'utcminute'   : utcdate.strftime('%M'),
            'utcsecond'   : utcdate.strftime('%S')}
        
        base = folder_name = re.sub(r'\W+', '', self.folder_template.format(**mappings))
        
        # Check if folder_name exists
        count = itertools.count(2)
        while os.path.exists(os.path.join(self.root, folder_name)):
            folder_name = (base + "_" + str(next(count)))

        return os.path.join(self.root, folder_name)
        
    
    def __add(self, mp):
        """Adds a mediapackage in the repository. 
        Then checks if the mediapackage serie identifier and serie title are consistent.
        If not, updates appropriately.
        Args:
            mp (Mediapackage): the mediapackage that is going to be added.
        Returns:
            mp (Mediapackage): the added mediapackage.
        """
        self.__list[mp.getIdentifier()] = mp

        # This makes sure the series gets properly included/removed from the manifest                                                                                                                              
        # FIXME: Probably shouldn't go here                                                                                                                                                                        
        catalogs = mp.getCatalogs("dublincore/series")
        if mp.getSeriesIdentifier() and not catalogs:
            mp.add(os.path.join(mp.getURI(), 'series.xml'), mediapackage.TYPE_CATALOG, 'dublincore/series', 'text/xml')
        elif not mp.getSeriesIdentifier() and catalogs:
            mp.remove(catalogs[0])
            # FIXME: Remove the file from disk?                                                                                                                                                                     
        # Save the mediapackage in the repo
        serializer.save_in_dir(mp, self.logger)
        #FIXME write new XML metadata, episode, series                                                                                                                                                              
        return mp
