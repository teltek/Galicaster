# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/core/conf
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.


import os
import shutil
import ConfigParser
import socket
import json

from collections import OrderedDict
from datetime import datetime
from galicaster.utils import validator

YES = ['true', 'yes', 'ok', 'si', 'y']
NO = ['false', 'no', 'n']

"""
These classes shapes the galicaster configuration.
The Conf class gets all the configurable parameters and recording profiles including the default one.
The Profile class has a set of configurable tracks to be recorded.
The Track class gets all the configurable parameters of the synchronized tracks that are going to be recorded in a specified profile.
"""
class Conf(object): # TODO list get and other ops arround profile

    def __init__(self, conf_file='/etc/galicaster/conf.ini',
                conf_dist_file=None,
                profile_folder='/etc/galicaster/profiles'):
        """Initializes conf with all the necessary in order to parser and process users configuration, default configuration and the profiles set.
        Args:
            conf_file (str): absolute path of the user's configuration file (config.ini).
            conf_dist_file (str): absolute path of the distribution's configuration file (config-dist.ini).
            profile_folder (str): absolute path of the profile folder.
        Attributes:
            __conf (ConfigParser): parser of user's and distribution's configuration file.
            __user_conf (ConfigParser): parser of user's configuration file.
            __conf_dist (ConfigParser): parser of distribution's configuration file.
            __profiles (Dict{str,Profile}): a set of all the profiles in profile's folder and the default one identified by its name (key of the dictionary)
            __default_profile (Profile): profile set in configuration file.
            __current_profile (Profile): active profile.
            __parser_error (bool): True if any error have been catched while parsing. False otherwise.
            conf_file (str): the given absolute path of the user's configuration file.
            conf_dist_file (str): the given absolute path of the distribution's configuration file.
            profile_folder (str): the given path of the profile folder.
            logger (Logger): the object that prints all the information, warning and error messages. See galicaster/context/logger
        """
        self.__conf = ConfigParser.ConfigParser()
        self.__user_conf = ConfigParser.ConfigParser()
        self.__conf_dist = ConfigParser.ConfigParser()
        self.__profiles = OrderedDict()
        self.__default_profile = None
        self.__current_profile = None
        self.__parser_error = False

        # FIXME when using 2.7 dict_type=collections.OrderedDict)
        self.conf_file = (conf_file if os.path.isfile(conf_file) else
                        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'conf.ini')))
        self.conf_dist_file = (conf_dist_file or
                             os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','conf-dist.ini')))
        self.profile_folder = (profile_folder if os.path.isdir(profile_folder) else
                             os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'profiles')))
        self.logger = None

    def reload(self):
        """Reloads the configurations
        """
        try:
            self.__conf.read((self.conf_dist_file, self.conf_file))
            self.__user_conf.read(self.conf_file)
            self.__conf_dist.read(self.conf_dist_file)
            self._check_conf_user()
            self.__parser_error = False

        except Exception as exc:
            self.logger and self.logger.error("Error parsing the conf file: {}".format(exc))
            self.__parser_error = True
            self.__conf.read(self.conf_dist_file)
            self.__user_conf.read(self.conf_dist_file)
            self.__conf_dist.read(self.conf_dist_file)

        self.__profiles = self.__get_profiles(self.profile_folder)


    def _check_conf_user(self):
        """Checks if there is a section or option invalid (not according with the distribution configuration)
        """
        for section in self.__user_conf.sections():
            if section not in self.__conf_dist.sections():
                self.logger and self.logger.debug('No section "{0}". Please check the file {1}'.format(section, self.conf_file))
            else:
                for option in self.__user_conf.options(section):
                    if option not in self.__conf_dist.options(section):
                        self.logger and self.logger.debug('No option "{0}" in section "{1}". Please check the file {2}'.format(option, section, self.conf_file))


    def get(self, sect, opt, default=None): # TODO overload ConfigParser?
        """Tries to return the value of a specific option in a specific section.
        If any error occurs, the logger prints it propperly.
        Args:
            sect (str): section of configuration file.
            opt (str): option of configuration file.
        Returns:
            Str: the value of option opt in section sect.
        """
        try:
            response = self.__conf.get(sect, opt)
            return response
        except Exception as exc:
            if self.logger:
                self.logger.debug('The parameter "{0}" in section "{1}" does not exist. Exception: {2}'.format(opt, sect, exc))

        return default


    def get_all(self, full=True):
        """
        Tries to return all the configuration
        Args:
            full (boolean): whether to return the full configuration or only the conf.ini
        Returns:
            OrderedDict: conf.
        """
        conf = OrderedDict()
        if full:
            sections = self.get_sections()
        else:
            sections = self.get_user_sections()

        for section in sections:
            if full:
                conf[section]=self.get_section(section)
            else:
                conf[section]=self.get_user_section(section)
        return conf


    def get_int(self, sect, opt, default=None):
        """Tries to return the value of an option in a section as an int.
        If else, returns the given default value.
        Args:
            sect (str): section of configuration file.
            opt (str): option of configuration file.
            default (str): the string return when an exception occurs.
        Returns:
            Int: the value of option opt in section sect if there are no errors. Default otherwise.
        """
        if self.get(sect, opt):
            try:
                return int(self.get(sect, opt))
            except Exception as exc:
                self.logger and self.logger.warning('The parameter "{0}" in section "{1}" is not an int, FORCED TO "{2}". Exception: {3}'.format(opt, sect, default, exc))

        return default


    def get_float(self, sect, opt, default=None):
        """Tries to return the value of an option in a section as a float.
        If else, returns the given default value.
        Args:
            sect (str): section of configuration file.
            opt (str): option of configuration file.
            default (str): the string return when an exception occurs.
        Returns:
            Float: the value of option opt in section sect if there are no errors. Default otherwise.
        """
        if self.get(sect, opt):
            try:
                return float(self.get(sect, opt))
            except Exception as exc:
                self.logger and self.logger.warning('The parameter "{0}" in section "{1}" is not a float, FORCED TO "{2}". Exception: {3}'.format(opt, sect, default, exc))

        return default


    def get_hour(self, sect, opt, default='00:00'):
        """Tries to return the value of an option in a section with a hour format.
        If else, returns the given default value.
        Args:
            sect (str): section of configuration file.
            opt (str): option of configuration file.
            default (str): default output if there is no value.
        Returns:
            Str: the value of option opt in section sect if there are no errors. Default otherwise.
        """
        hour = self.get(sect, opt)
        if hour:
            try:
                datetime.strptime(hour, '%H:%M')
                return hour

            except Exception as exc:
                 self.logger and self.logger.warning('The parameter "{0}" in section "{1}" has not hour format, FORCED TO "{2}". Exception: {3}'.format(opt, sect, default, exc))

        return default


    def get_lower(self, sect, opt, default=""):
        """Tries to return the value of an option in a section converted to lowercase.
        If else returns the given default value.
        Args:
            sect (str): section of configuration file.
            opt (str): option of configuration file.
            default (str): default output if there is no value.
        Returns:
            Str: the value of option opt in section sect in lowercase if ther are no errors. Default otherwise.
        """
        if self.get(sect, opt):
            try:
                return self.get(sect, opt).lower()
            except Exception as exc:
                self.logger and self.logger.warning('Error converting to lowercase the parameter "{0}" in section "{1}", FORCED TO "{2}". Exception: {3}'.format(opt, sect, default, exc))

        return default


    def get_boolean(self, sect, opt, default=False):
        """Tries to return a value of an option in a section as a boolean.
        If else returns the given default value.
        Args:
            sect (str): section of configuration file.
            opt (str): option of configuration file.
            default (str): default output if there is no value.
        Returns:
            Bool: the value of option opt in section sect as a boolean if there are no errors. Default otherwise.
        """
        value = self.get_lower(sect, opt)
        if value in YES:
            return True
        elif value in NO:
            return False
        else:
            self.logger and self.logger.warning('Unknown value "{0}" obtaining a boolean from the parameter "{1}" in section "{2}", FORCED TO "{3}"'.format(value, opt, sect, default))

        return default



    def get_list(self, sect, opt, default=[]):
        """Tries to return a set of values of an option in a section as a list.
        If else returns the given default value.
        Args:
            sect (str): section of configuration file.
            opt (str): option of configuration file.
            default (str): default output if there is no value.
        Returns:
            List[Str]: the value of option opt in section sect as a list of strings. Default otherwise.
        Note:
            key = value1 value2 value2
        """
        try:
            return self.get(sect, opt).split()

        except Exception as exc:
            self.logger and self.logger.warning('There was an error before obtaining a list from the parameter "{0}" in section "{1}", FORCED TO "{2}". Exception: {3}'
                                                             .format(opt, sect, default, exc))
        return default


    def get_choice(self, sect, opt, options, default=None):
        """Tries to return a value of an option in a section if it is in the options list.
        If else returns the given default value.
        Args:
            sect (str): section of configuration file.
            opt (str): option of configuration file.
            options List[str]: a list of options (in lowercase)
            default (str): default output if there is no value.
        Returns:
            Str: the value of option opt in section sect if it is in the options list and there are no errors. Default otherwise.
        """
        try:
            data = self.get(sect, opt).lower()
            if data in options:
                return data
            else:
                self.logger and self.logger.warning('The parameter "{0}" in section "{1}" with value {2} is not in {3}, FORCED TO "{4}"'.format(opt, sect, data, options, default))
                return default

        except Exception as exc:
            self.logger and self.logger.warning('There was an error before obtaining the parameter "{0}" in section "{1}", FORCED TO "{2}". Exception: {3}'.format(opt, sect, default, exc))
        return default


    def get_choice_uppercase(self, sect, opt, options, default=None):
        """Tries to return a value of an option in a section if it is in the options list.
        If else returns the given default value.
        Args:
            sect (str): section of configuration file.
            opt (str): option of configuration file.
            options List[str]: a list of options (in uppercase)
            default (str): default output if there is no value.
        Returns:
            Str: the value of option opt in section sect if it is in the options list and there are no errors. Default otherwise.
        """
        try:
            data = self.get(sect, opt).upper()
            if data in options:
                return data
            else:
                self.logger and self.logger.warning('The parameter "{0}" in section "{1}" with value {2} is not in {3}, FORCED TO "{4}"'.format(opt, sect, data, options, default))
                return default

        except Exception as exc:
            self.logger and self.logger.warning('There was an error before obtaining the parameter "{0}" in section "{1}", FORCED TO "{2}". Exception: {3}'.format(opt, sect, default, exc))
        return default


    def get_dict(self, sect, opt, default={}):
        """Tries to return a set of values of an option in a section as a dictionary.
        If else returns the given default value.
        Args:
            sect (str): section of configuration file.
            opt (str): option of configuration file.
            default (str): default output if there is no value.
        Returns:
            Dict[Str, Str]: the set of values of option opt in section sect if there are no error. Default otherwise.
        Note:
        key = key1:value1;key2:value2
        """
        dictionary = {}
        if self.get(sect, opt):
            try:
                for item in self.get(sect, opt).split(";"):
                    item_list = item.split(":")
                    if len(item_list) > 1:
                        dictionary[item_list[0]] = item_list[1]
            except Exception as exc:
                self.logger and self.logger.warning('Error obtaining a dictionary from "{0}" in section "{1}", FORCED TO "{2}". Exception: {3}'.format(opt, sect, default, exc))
        return dictionary if dictionary else default


    def get_json(self, sect, opt, default={}):
        """Tries to return a set of values of an option in a section as a dictionary.
        If else returns the given default value.
        Args:
            sect (str): section of configuration file.
            opt (str): option of configuration file.
            default (str): default output if there is no value.
        Returns:
            Dict: the set of values of option opt in section sect if there are no error. Default otherwise.
        Note:
        key = {"foo":["bar", null, 1.0, 2]}
        """
        dictionary = {}
        if self.get(sect, opt):
            try:
                dictionary = json.loads(self.get(sect, opt))
            except Exception as exc:
                self.logger and self.logger.warning('Error obtaining a json dictionary from "{0}" in section "{1}", FORCED TO "{2}". Exception: {3}'.format(opt, sect, default, exc))
        return dictionary if dictionary else default


    def get_section(self, sect, default={}):
        """Tries to return a section as a dictionary instead of a list.
        If else returns the given default value.
        Args:
            sect (str): section of configuration file.
            default (str): default output if there is no value.
        Returns:
            Dict[Str, str]: the dictionary with the information of the section sect if there are no errors. Default otherwise.
        """
        try:
            return OrderedDict(self.__conf.items(sect))
        except ConfigParser.NoSectionError as exc:
            self.logger and self.logger.warning('Error obtaining the section "{0}" , FORCED TO "{1}". Exception: {2}'
                                                             .format(sect, default, exc))
        return default


    def get_user_section(self, sect, default={}):
        """Tries to return a section as a dictionary instead of a list.
        If else returns the given default value.
        Args:
            sect (str): section of configuration file.
            default (str): default output if there is no value.
        Returns:
            Dict{Str, str}: the dictionary with the information of the section sect if there are no errors. Default otherwise.
        """
        try:
            return OrderedDict(self.__user_conf.items(sect))
        except ConfigParser.NoSectionError as exc:
            self.logger and self.logger.warning('Error obtaining the section "{0}" , FORCED TO "{1}". Exception: {2}'
                                                             .format(sect, default, exc))
        return default

    def get_sections(self, default={}):
        """Tries to return all sections.
        If else returns the given default value.
        Args:
            default (str): default output if there is no value.
        Returns:
            Dict[Str, str]: the dictionary with all the sections.
        """
        try:
            return self.__conf.sections()
        except ConfigParser.NoSectionError as exc:
            self.logger and self.logger.warning('Error obtaining all the sections, FORCED TO "{0}". Exception: {1}'
                                                             .format(default, exc))
        return default


    def get_user_sections(self, default={}):
        """Tries to return all the user sections.
        If else returns the given default value.
        Args:
            default (str): default output if there is no value.
        Returns:
            List[Str]: a list with all the available sections in conf.ini.
        """
        try:
            return self.__user_conf.sections()
        except ConfigParser.NoSectionError as exc:
            self.logger and self.logger.warning('Error obtaining all the sections in user configuration file, FORCED TO "{0}". Exception: {1}'.format(default, exc))
        return default


    def set(self, sect, opt, value):
        """Sets the specified option from the specified section.
        Args:
            sect (str): the section to be modified.
            opt (str): the option of the specified section to be modified.
            value (str): the value of the specified option to be modified.
        """
        self.__force_set(self.__user_conf, sect, opt, value)
        self.__force_set(self.__conf, sect, opt, value)
        self.update(update_profiles=False)

    def set_section(self, sect_name=None, sect={}):
        """Sets the specified section
        Args:
            sect_name (str): the value of the specified section to be modified.
            sect (dict): the section to be modified.
        """
        try:
            if not sect_name:
                raise Exception("No section name specified")

            for opt,value in sect.iteritems():
                self.__force_set(self.__user_conf, sect_name, opt, value)
                self.__force_set(self.__conf, sect_name, opt, value)

            return True
        except Exception as exc:
            self.logger and self.logger.warning('Error trying to set section with name {}: Exception {}'.format(sect_name , exc))

        return False

    def get_hostname(self):
        """Gets the hostname in configfile or de default one.
        Returns:
                    Str: hostname in the configfile if exists (ingest section). Otherwise: Prefix + socket hostname.
        """

        hostname = self.get('ingest', 'hostname')
        if not hostname or hostname == "":
            prefix = 'GCMobile-' if self.is_admin_blocked() else 'GC-'
            hostname = prefix + socket.gethostname()
            self.set('ingest','hostname',hostname)
            self.update()
        return hostname


    def get_ip_address(self):
        address = '127.0.0.1'

        try:
            address = socket.gethostbyname(socket.gethostname())
        except Exception as exc:
            self.logger and self.logger.error('Problem on obtaining the IP of "{}", forced to "127.0.0.1". Exception: {}'.format(socket.gethostname(),exc))

        return address

    def get_size(self):
        """Gets the resolution in the configfile if exists.
        If not exists gets value 'auto'.
        Returns:
                    Str: resolution in the configfile if exists (basic section). Default value "auto" otherwise.
        """
        return self.get('basic', 'resolution') or "auto"

    def is_admin_blocked(self):
        """Checks if admin is bloqued.
        Returns:
                    Bool: True if admin is bloqued (section basic, option admin from configfile). False otherwise.
        """
        return self.get_boolean('basic', 'admin') or False

    def tracks_visible_to_opencast(self):
        """Checks if the tracks are visible to opencast.
        Returns:
                    Bool: True if the tracks are visible to opencast (section ingest, option visible_tracks from configfile). False otherwise.
        """
        return self.get_boolean('ingest', 'visible_tracks') or False


    def get_modules(self):
        """Checks if the admin is bloqued and if the ingest is active. According to this, it returns a list of modules.
        Returns:
            List [str]: list of modules.
        """
        modules = []
        modules.append('recorder')
        modules.append('scheduler')

        if self.get_boolean('basic', 'admin'):
            modules.append('media_manager')
            modules.append('player')

        if self.get_boolean('ingest', 'active'):
            modules.append('ocservice')

        return modules


    def __force_set(self, conf, section, option, value):
        """Creates a new section or option depending on the arguments received.
        Args:
            conf (ConfigParser): parser of the config file that is going to be modified.
            section (str): The section to be created.
            option (str): The option of a section to be created.
            value (str): The value of the option.
        """
        if not conf.has_section(section):
            conf.add_section(section)
        conf.set(section, option, value)


    def remove_option(self, sect, opt):
        """Removes the specified option from the specified section.
        Args:
            sect (str): the particular section.
            opt (str): the option of the sect to be removed.
        Returns:
                Bool: True If the option existed to be removed. False otherwise.
        """
        if self.__user_conf.has_section(sect):
            self.__user_conf.remove_option(sect, opt)
        if self.__conf.has_section(sect):
            return self.__conf.remove_option(sect, opt)
        return False


    def remove_section(self, sect):
        """Removes the specified section.
        Args:
            sect (str): the particular section.
        Returns:
                Bool: True If the option existed to be removed. False otherwise.
        """

        if self.__user_conf.remove_section(sect):
            return self.__conf.remove_section(sect)
        return False

    def remove_sections(self):
        """Removes ecery section of the user configuration.
        """
        for section in self.__user_conf.sections():
            self.remove_section(section)

    def update(self, update_profiles=True):
        """Updates the configuration file from user.
        """
        update_profiles and self.update_profiles()

        # Make a backup if it was an error parsing the conf file
        if self.__parser_error:
            src = self.conf_file
            now = str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S"))
            dst = self.conf_file + ".orig_" + now

            try:
                with open(src, 'rb') as fsrc:
                    with open(dst, 'wb') as fdst:
                        self.logger and self.logger.warning("Copying original conf file due to an error: {0} to {1}".format(src, dst))
                        shutil.copyfileobj(fsrc, fdst)
                        os.fsync(fdst)
                        os.chmod(dst, 0666)
            except Exception as exc:
                self.logger and self.logger.warning("Error trying to copy the original conf file {} to {}".format(src, dst))

        try:
            configfile = open(self.conf_file, 'wb')
            self.logger and self.logger.debug("Saving current configuration to {}".format(configfile.name))
            self.__user_conf.write(configfile)
            configfile.close()
        except Exception as exc:
            self.logger and self.logger.error('Erros saving configuration: {}'.format(exc))


    def update_profiles(self):
        """Write on disk profile modifications, delete file if neccesary.
        """
        for profile in self.__profiles.values():
            if profile.to_delete:
                self.logger and self.logger("Removing profile {} with path {}".format(profile.name, profile.path))
                os.remove(profile.path)
                self.__profiles.pop(profile.name)
            elif profile.name != self.__default_profile.name:
                #profile.export_to_file() #Uncomment if profiles are editable
                if profile == self.__current_profile:
                    self.set('basic','profile',profile.name)


    def get_tracks_in_oc_dict(self):
        """Returns the tracks names and information if they are configurable by opencast.
        Returns:
            Dict {Str,str}: If the tracks are configurable by opencast, returns its flavor, outputfile and source. Also it returns the names of all tracks. Otherwise returns defaults as names.
        """
        # Tracks blocked by Galicaster
        if not self.tracks_visible_to_opencast():
            return {'capture.device.names': 'defaults'}
        # Tracks configurable by opencast
        default  = self.get_current_profile()
        names = []
        tracks = {}
        for track in default.tracks:
                    names.append(track.name)
                    tracks['capture.device.' + track.name + '.flavor']      = track.flavor + '/source'
                    tracks['capture.device.' + track.name + '.outputfile'] = track.file
                    tracks['capture.device.' + track.name + '.src']          = track.location or '/dev/null'
        if names:
            tracks['capture.device.names'] = ','.join(names)

        return tracks


    def create_profile_from_conf(self, activated=True):
        """Loads a profile from a configuration file.
        Args:
            activated (bool): True if the default profile does not include all tracks in config file (include oonly de tracks with the option active true).
        Returns:
            Profile: created profile.
        """
        parser = self.__conf

        profile = Profile()
        profile.path = self.conf_dist_file

        if not parser.has_section("data") or not parser.has_option('data', 'name'):
            profile.name = 'Default'
        else:
            profile.name = parser.get('data', 'name')
            if parser.has_option('data', 'execute'):
                profile.execute = parser.get('data', 'execute')
            if parser.has_option('data', 'template'):
                profile.template = parser.get('data', 'template')

        profile.import_tracks_from_parser(parser)
        if activated:
            def f(x): return x.get('active', 'true').lower() in YES
            profile.tracks = filter(f, profile.tracks)
        return profile


    def get_permission(self,permit):
        """Checks if config file allows a particular permission.
        Args:
            permit (str): manual, start, stop, pause or overlap.
        Returns:
            Bool: True if it is allowed a permission. False otherwise.
        """
        try:
            return self.__conf.getboolean('allows',permit)
        except Exception as exc:
            if self.logger:
                self.logger.error('Unknow permission. Exception: {0}'.format(exc))
            return None


    def __get_profiles(self, profile_folder=None): # TODO profiles as a key variable
        """Gets existing profiles, including the default one and the current one (if it is not the default profile), as a dictionary with the profile name as key.
        Args:
            profile_folder (str): absolute path of the folder with the not default profiles.
        Returns:
            Dict {Str, Profile}: Dictionary (profile name, profile) with all the valid profiles.
        """
        profile_list = OrderedDict()
        self.__default_profile= self.create_profile_from_conf()

        # Load the default profile
        error_msg, profile_clean = self.__check_tracks(self.__default_profile)
        if error_msg:
            self.logger and self.logger.warning(error_msg)

        profile_list[self.__default_profile.name] = profile_clean

        # Load the profiles located in the profile folder
        for filename in os.listdir(profile_folder):
            filepath = os.path.join(profile_folder, filename)
            if os.path.splitext(filename)[1]=='.ini':
                profile = Profile()
                valid = profile.import_from_file(filepath)

                if valid:
                    error_msg, profile_clean = self.__check_tracks(profile)

                    if error_msg:
                        self.logger and self.logger.warning(error_msg)

                    # Add the profile to the profile list
                    profile_list[profile.name] = profile_clean

                else:
                    if self.logger:
                        self.logger.warning("Invalid profile {0}".format(filepath))
                    profile = None

        current = self.get("basic","profile")
        try:
            self.__current_profile = profile_list[current]
        except Exception as exc:
            if self.logger:
                self.logger.error("Forcing default profile since current ({}) doesn't exist. Exception: {}".format(current, exc))
            self.__current_profile = self.__default_profile

        return profile_list


    def __check_tracks(self, profile):
        """Checks if the tracks of a profile are not repeated or if the profile is invalid. Arranges the profile too.
        Args:
            profile (Profile): the profile whose tracks are going to be checked.
        Returns:
            Str: an error message if the tracks of the profile were repeated or if the profile was invalid.
            Profile: the checked profile and repaired profile.
        """
        profile.original_tracks = list(profile.tracks)
        error_msg = None

        # 1. Check repeated values
        tracks = list(profile.tracks)

        count = 0
        for ind,track in enumerate(tracks):
            tracks.pop(count)
            for k,v in track.iteritems():
                if k in ['name', 'file']:
                    for aux in tracks:
                        if k in aux.keys() and v == aux[k]:

                            # Compose error message
                            if error_msg:
                                error_msg = '{}. Repeated value "{}" for tracks "{}" and "{}", forced to BIS{}'.format(
                                    error_msg, v, track.name, aux.name, v)
                            else:
                                error_msg = 'Profile error in {}, profile name: {}. Repeated value "{}={}" for tracks "{}" and "{}", forced to BIS{}'.format(
                                    profile.path, profile.name, k, v, track.name, aux.name, v)

                            profile.tracks[ind][k] = "BIS{}".format(v)
            count +=1



        # 2. Validate profile
        for ind, track in enumerate(profile.tracks):
            track_clean = track
            try:
                error, track_clean = validator.validate_track(track)
                track_clean = Track(track_clean)
                if error:
                    error_msg = 'Profile error in {0}, profile name: {1}. {2}'.format(
                        profile.path, profile.name, error)
            except Exception as exc:
                error_msg = 'Profile exception in {0}, profile name: {1}. {2}'.format(
                    profile.path, profile.name, exc)


            profile.tracks[ind] = track_clean
            profile.original_tracks[ind] = track

        return error_msg, profile


    def get_profiles(self):
        """Returns:
            Dict {str,Profile}: the current list of profiles identified by its name (as the key of the dictionary)
        """
        profiles = OrderedDict()

        #return filter(,self.__
        for name,profile in self.__profiles.iteritems():
            if not profile.to_delete:
                profiles[name]=profile
        return profiles


    def add_profile(self,profile, old_key=None):
        """Adds a new profile and deletes the old one if it is specified.
        Args:
            profile (Profile): new profile to add.
            old_key (str): the name of the old profile to delete.
        """
        self.__profiles[profile.name] = profile
        if old_key:
            if self.__profiles.has_key(old_key):
                del self.__profiles[old_key]


    def get_current_profile(self):
        """Gets the current profile.
        Returns:
            Profile: current profile.
        """
        return self.__current_profile


    def change_current_profile(self,name):
        """Changes the current profile to a new one given by its name.
        Args:
            name (str): the name of the new current profile.
        """
        if name != self.__current_profile.name:
            if name in self.__profiles:
                self.logger and self.logger.debug("Changing current profile to '{}'".format(name))
                self.__current_profile = self.__profiles[name]
                self.force_set_current_profile(name)
            else:
                self.logger and self.logger.warning('Error trying to change the profile, {} does not exist. Ignoring this action...'.format(name))


    def force_set_current_profile(self,name):
        """Changes the information about the current profile in the configuration files.
        Args:
            name (str): the name of the new current profile.
        """
        self.set("basic","profile",name)


    def set_default_profile_as_current(self):
        """Changes the current profile to the default one.
        """
        self.__current_profile = self.__default_profile
        self.force_set_current_profile(self.__default_profile.name)


    def get_default_profile(self):
        """Gets the default profile.
        Returns:
            Profile: default profile.
        """
        return self.__default_profile


    def get_free_profile(self): # TODO include in conf
        """Gets a name of a profile that is not in use.
        Returns:
            Str: the absolute path of a free profile file name.
        Note:
            Profile name: number + ".ini"
        """
        index=0
        while True:
            index+=1
            new_path=os.path.join(self.profile_folder, 'profile'+str(index)+ '.ini')
            if not os.path.isfile(new_path):
                break
        return new_path


    def get_color_style(self):
        """Checks if the color style is classic.
        Returns:
            Bool: True if the color style is classic. False otherwise.
        """
        classic = self.get_boolean('color','classic')
        return classic


    def get_palette(self, old_style = True):
        """Returns the palette colors as a list if old_style.
        Args:
            old_style (bool): True if config file colours are used. False otherwise.
        Returns:
            List [Str]: list of 6 items. Each one a colour of a state if old_style. Otherwise, 6 items with the none colour element.
        """
        undefined = self.get('color','none')
        nightly = self.get('color','nightly')
        pending = self.get('color','pending')
        processing = self.get('color','processing')
        done = self.get('color','done')
        failed = self.get('color','failed')

        if not old_style:
            return [undefined, undefined, undefined, undefined, undefined, undefined]
        else:
            return [undefined, nightly, pending,processing, done, failed]


class Profile(object):
    def __init__(self, name='New Profile', path=None):
        """Initializer of the object profile that allows to import and export to files, and also import from conf.
        It can creates tracks.
        It also allows to reorder tracks.
        Args:
            name (str): name of the profile.
            path (str): path of the file containing the information of the profile.
        Attributes:
            name (str): the given name of the profile.
            tracks (List[Track]): the list of all of the profile tracks.
            original_tracks (List[Track]): List to store the original tracks (*.ini). In the function export_to_file will be written only these tracks.
            path (str): the given path of the file containing the information of the profile.
            execute (str): the value in the option execute from section data in the profile file.
            template (str): the value in the option template from section data in the profile file.
            to_delete (bool): True if the profile is going to be deleted when profiles are updated in Conf.
        """
        self.name = name
        self.tracks = []
        self.original_tracks = []
        self.path = path if path else datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
        self.execute = None
        self.template = None
        self.to_delete = False

    def new_track(self, options):
        """Creates a new track with the options given.
        Args:
            options (Dict{Str,str}): the optional data of the track as a dictionary {parameter,content}.
        Returns:
            Track: the added track.
        """
        new = Track(options)
        return self.add_track(new)

    def add_track(self, track):
        """Adds a track to the profile dictionary of tracks.
        Args:
            track (Track): the track that is going to be added.
        Returns:
            Track: the added track.
        """
        self.tracks.append(track)
        return track

    def remove_track(self, track):
        """Removes a track from the profile's dictionary of tracks.
        Args:
            track (Track): the track that is going to be removed.
        Returns:
            Track: the track removed.
        """
        self.tracks.remove(track)
        return track


    # TODO: This is a WORKAROUND for https://github.com/teltek/Galicaster/issues/317
    # FIXME
    def get_tracks_audio_at_end(self):
        """
        """
        for indx, element in enumerate(self.tracks):
            if element['device'] in ['audiotest', 'autoaudio', 'pulse']:
                self.tracks += [self.tracks.pop(indx)]

        return self.tracks


    #TODO error, be careful with self.tracks(. It's not a method
    def reorder_tracks(self, order=[]):
        """Reorders the tracks following the order set by the argument order.
        If the new list of index (order) is smaller than the dictionary of tracks, the tracks from the old order are added at the end of the new order.
        Args:
            order (List[int]): the list of the new index of tracks.
        """
        new_order = []
        for index in range(len(order)):
            new_order.append(self.tracks(order[index]).copy())
        for track in self.tracks:
            if self.tracks.index(track) not in order:
                new_order.append(track.copy())
        self.tracks = new_order

    #TODO same as profile.path
    def set_path(self, path):
        """Sets the path of the profile.
        Args:
            path (str): the path to be set.
        """
        self.path = path

    def import_tracks_from_parser(self, parser):
        """Imports the tracks from the parser of a file.
        Adds these tracks to the profile.
        Args:
            parser (ConfigParser): the parser of a file.
        """
        for section in parser.sections():
            if section.count('track'):
                self.tracks.append(Track(parser.items(section)))

    def import_from_file(self, filepath):
        """Imports a profile from a file.
        Args:
            filepath (str): the absolute path of a file.
        Returns:
            Bool: True if there were no errors. False otherwise.
        """
        parser = ConfigParser.ConfigParser()
        try:
            parser.read(filepath)
        except ConfigParser.Error:
            return False
        if not parser.has_section("data"):
            return False

        self.name = parser.get('data', 'name')
        if parser.has_option('data', 'execute'):
            self.execute = parser.get('data', 'execute')
        if parser.has_option('data', 'template'):
            self.template = parser.get('data', 'template')
        self.path = filepath
        self.import_tracks_from_parser(parser)
        return True


    # Note: Use the original tracks, so only will be written the properties already included in the file (*.ini).
    #         This avoid to write all the parameters in the file.
    def export_to_file(self, filepath=None):
        """Exports the information and the tracks of a profile to a file.
        Args:
            filepath (str): the absolute path to the file that is going to have the information of the profile.
        """
        if not filepath:
            filepath = self.path

        parser = ConfigParser.ConfigParser()
        parser.add_section('data')
        parser.set('data','name', self.name)
        if self.execute:
            parser.set('data','execute', self.execute)
        if self.template:
            parser.set('data','template', self.template)
        index = 1
        for track in self.original_tracks:
            section = 'track'+str(index)
            parser.add_section(section)
            for key in track.iterkeys():
                if key not in ['path','active']:
                    parser.set(section,key,track[key])
            index+=1

        configfile = open(filepath, 'wb')
        parser.write(configfile)
        configfile.close()


class Track(OrderedDict):

    BASIC = ['name', 'device', 'flavor', 'location', 'file']

    def __init__(self, *args, **kw):
        """Initializes a custom dictionary focused on Galicaster's Track parameters handling.
        BASIC parameters allways exists and are properties
        It is capable of mantain the parameters ordered, for UI porpuses.
        See:
            url: http://stackoverflow.com/questions/2328235/pythonextend-the-dict-class
        Args:
            *args: list with the pair of parameters of the track.
            **kw: dictionary with the parameters of the track.
        """
        super(Track,self).__init__(*args, **kw)

        for key in self.BASIC:
            if not self.has_key(key):
                self[key] = ""

    def _get_name(self):
        """Gets the name of the track.
        Returns:
            Str: the name of the track.
        """
        return self['name']

    def _set_name(self, value):
        """Sets the name of a track.
        Args:
                value (str): the new name of the track.
        """
        self['name'] = value

    name = property(_get_name, _set_name)

    def _get_device(self):
        """Gets the device of the track.
        Returns:
            Str: the device of the track.
        """
        return self['device']

    def _set_device(self, value):
        """Sets the device of the track.
        Args:
            value (str): the new device of the track.
        """
        self['device'] = value

    device = property(_get_device, _set_device)

    def _get_flavor(self):
        """Gets the flavor (classificatory tag) of the track.
        Returns:
            Str: the flavor of the track.
        """
        return self['flavor']

    def _set_flavor(self, value):
        """Sets the flavor (classificatory tag) of the track.
        Args:
            value (str): the new flavor of the track.
        """
        self['flavor'] = value

    flavor = property(_get_flavor, _set_flavor)

    def _get_location(self):
        """Gets the location of the track.
        Returns:
            Str: the location of the track.
        """
        return self['location']

    def _set_location(self, value):
        """Sets the location of the track.
        Args:
            value (str): the new location of the track.
        """
        self['location'] = value

    location = property(_get_location, _set_location)

    def _get_file(self):
        """Gets the file of the track.
        Returns:
            Str: the file of the track.
        """
        return self['file']

    def _set_file(self, value):
        """Sets the file of the track.
        Args:
            value (str): the new file of the track.
        """
        self['file'] = value

    file = property(_get_file, _set_file)

    def options_keys(self):
        """Gets a list of optional parameters of a track. (Parameters not included in BASIC)
        Returns:
            List[Str]: the list of optional parameters of a track. Such as frequency, pattern, colors...
        """
        sequence = []
        for key in self.keys():
            if key not in self.BASIC:
                sequence.append(key)
        return sequence

    def basic(self):
        """Gets the basic parameters set of the track.
        Returns:
            Dict {Str,str}: the set of the basic track parameters with the parameter name as key.
        """
        out = {}
        for key in self.BASIC:
            out[key] = self[key]
        return out

    def options(self):
        """Returns:
            Dict {Str,str}: the set of the options (not in BASIC) track parameters with the parameter name as key.
        """
        out = {}
        for key in self.options_keys():
            out[key] = self[key]
        return out
