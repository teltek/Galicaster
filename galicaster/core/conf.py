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
import ConfigParser
import socket
from collections import OrderedDict

YES = ['true', 'yes', 'ok', 'si', 'y']

class Conf(object): # TODO list get and other ops arround profile

   def __init__(self, conf_file='/etc/galicaster/conf.ini', 
                conf_dist_file=None, 
                profile_folder='/etc/galicaster/profiles'):
      self.__conf = ConfigParser.ConfigParser() 
      self.__user_conf = ConfigParser.ConfigParser() 
      self.__profiles = {}
      self.__default_profile = None
      self.__current_profile = None
      
      # FIXME when using 2.7 dict_type=collections.OrderedDict)
      self.conf_file = (conf_file if os.path.isfile(conf_file) else 
                        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'conf.ini')))
      self.conf_dist_file = (conf_dist_file or 
                             os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','conf-dist.ini')))
      self.profile_folder = (profile_folder if os.path.isdir(profile_folder) else 
                             os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'profiles')))

      self.logger = None         
      self.reload()
      self.hostname = self.get_hostname()


   def reload(self):
      """
      Reload the configurations
      """
      self.__conf.read((self.conf_dist_file, self.conf_file))
      self.__user_conf.read(self.conf_file)
      self.__profiles = self.__get_profiles(self.profile_folder)


   def get(self, sect, opt): # TODO overload ConfigParser?
       """
       Return the value of option in section
       """
       try:
          response = self.__conf.get(sect, opt)
       except:
          response = None
       return response


   def get_int(self, sect, opt):
       """
       Return int value of option in section
       """
       return self.get(sect, opt) and int(self.get(sect, opt))


   def get_lower(self, sect, opt):
       """
       Return the value in lower
       """
       return self.get(sect, opt) and self.get(sect, opt).lower()


   def get_boolean(self, sect, opt):
       """
       Return int value of option in section
       """
       return True if self.get_lower(sect, opt) in YES else False


   def get_list(self, sect, opt):
       """
       Return list value of option in section
       key = value1 value2 value2
       """
       return self.get(sect, opt).split() if self.get(sect, opt) else []


   def get_dict(self, sect, opt):
       """
       Return dict value of option in section
       key = key1:value1;key2:value2
       """
       return dict(item.split(":") for item in self.get(sect, opt).split(";")) if self.get(sect, opt) else {}

   def get_section(self, sect):
       """
       Returns a dictionay instead of a list
       """
       try:
          return dict(self.__conf.items(sect))
       except ConfigParser.NoSectionError:
          return {}


   def set(self, sect, opt, value):
      """
      Set the specified option from the specified section. 
      If the section does not exist.
      """
      self.__force_set(self.__user_conf, sect, opt, value)
      self.__force_set(self.__conf, sect, opt, value)


   def get_hostname(self):
      prefix = 'GCMobile-' if self.is_admin_blocked() else 'GC-'
      return self.get('ingest', 'hostname') or (prefix + socket.gethostname())


   def get_size(self):
      return self.get('basic', 'resolution') or "auto"

   def is_admin_blocked(self):
      return self.get_boolean('basic', 'admin') or False
   
   def tracks_visible_to_matterhorn(self):
      return self.get_boolean('ingest', 'visible_tracks') or False
      
   
   def get_modules(self):
        modules = []
        modules.append('recorder')
             
        if self.get_boolean('basic', 'admin'):
            modules.append('media_manager')
            modules.append('player')

        if self.get_boolean('ingest', 'active'):
            modules.append('scheduler')

        return modules


   def __force_set(self, conf, section, option, value):
       """
       Creates a new section or option depending of the parameters
       """
       if not conf.has_section(section):
          conf.add_section(section)
       conf.set(section, option, value)

       
   def remove_option(self, sect, opt):
      """
      Remove the specified option from the specified section. 
      If the option existed to be removed, return True; otherwise return False.
      """
      if self.__user_conf.has_section(sect):
         self.__user_conf.remove_option(sect, opt)
      if self.__conf.has_section(sect):
         return self.__conf.remove_option(sect, opt)
      return False
      

   def update(self):
      """
      Update the configuration file
      """

      self.update_profiles()
      configfile = open(self.conf_file, 'wb')
      self.__user_conf.write(configfile)
      configfile.close()
      

   def update_profiles(self):
      """
      Write on disk profile modifications, delete file if neccesary.
      """
      for profile in self.__profiles.values():
         if profile.to_delete:
            os.remove(profile.path)
            self.__profiles.pop(profile.name)
         elif profile.name != 'Default':
            #profile.export_to_file() #Uncomment if profiles are editable
            if profile == self.__current_profile:
               self.__conf.set('basic','profile',profile.name)
            

   def get_tracks_in_mh_dict(self):
      # Tracks blocked by Galicaster
      if not self.tracks_visible_to_matterhorn(): 
         return {'capture.device.names': 'defaults'}
      # Tracks configurable by matterhorn
      if self.logger:
         self.logger.info('Be careful using profiles and matterhorn scheduler')
      default  = self.get_current_profile()
      names = []
      tracks = {}
      for track in default.tracks:
               names.append(track.name)
               tracks['capture.device.' + track.name + '.flavor']     = track.flavor + '/source' 
               tracks['capture.device.' + track.name + '.outputfile'] = track.file
               tracks['capture.device.' + track.name + '.src']        = track.location or '/dev/null'
      if names:
         tracks['capture.device.names'] = ','.join(names)

      return tracks  


   def create_profile_from_conf(self, activated=True):
      profile = Profile()
      parser = self.__conf
      profile.name = 'Default'
      profile.import_tracks_from_parser(parser)
      if activated:
         def f(x): return x.get('active', 'true').lower() in YES
         profile.tracks = filter(f, profile.tracks)
      return profile


   def get_permission(self,permit):
      try: 
         return self.__conf.getboolean('allows',permit)
      except:
         if self.logger:
            self.logger.error('Unknow permission')
         return None


   def __get_profiles(self, profile_folder=None): # TODO profiles as a key variable
      """
      Load existing profiles, including the default one, as a dictionary with 
      the profile name as key
      """
      profile_list = {}
      self.__default_profile= self.create_profile_from_conf()

      profile_list[self.__default_profile.name] = self.__default_profile
      for filename in os.listdir(profile_folder):
         filepath = os.path.join(profile_folder, filename)
         if os.path.splitext(filename)[1]=='.ini':
            profile = Profile()
            valid = profile.import_from_file(filepath)
            if valid:
               profile_list[profile.name] = profile
            else:
               if self.logger:
                  self.logger.warning("Invalid profile {0}".format(filepath))
               profile = None
      
      current = self.get("basic","profile")      
      try:
         self.__current_profile = profile_list[current]
      except:
         if self.logger:
            self.logger.error("Forcing default profile since current doesn't exits")
         self.__current_profile = self.__default_profile

      return profile_list


   def get_profiles(self):
      """
      Return the current list of profiles
      """
      profiles = {}

      #return filter(,self.__
      for name,profile in self.__profiles.iteritems():
         if not profile.to_delete:
            profiles[name]=profile           
      return profiles


   def add_profile(self,profile, old_key=None):
      self.__profiles[profile.name] = profile
      if old_key:
         if self.__profiles.has_key(old_key):
            del self.__profiles[old_key]
      

   def get_current_profile(self):      
      return self.__current_profile


   def change_current_profile(self,name):
      if name != self.__current_profile.name:
         self.__current_profile = self.__profiles[name]
         self.force_set_current_profile(name)


   def force_set_current_profile(self,name):
       self.set("basic","profile",name)   


   def set_default_profile_as_current(self):
      self.__current_profile = self.__default_profile
      self.force_set_current_profile("Default")


   def get_default_profile(self):
      return self.__default_profile


   def __get_free_number(self):
      for i in range(100):
         if not self.__conf.has_section('track'+unicode(i)):
            return i


   def get_free_profile(self): # TODO include in conf
      index=0
      while True:
         index+=1
         new_path=os.path.join(self.profile_folder, 'profile'+str(index)+ '.ini')
         if not os.path.isfile(new_path):
            break
      return new_path


   def get_color_style(self):
      classic = self.get_boolean('color','classic')
      return classic


   def get_palette(self, old_style = True):
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
   """
   Contains the name, location and tracks of a profile
   Allows to import and export to files, and also import from conf
   Tracks can be created
   Other features are reordering tracks
   """
   def __init__(self, name='New Profile', path=None):
      self.name = name
      self.tracks = []
      self.path = path
      self.execute = None
      self.to_delete = False
      
   def new_track(self, options):
      new = Track(options)
      return self.add_track(new)

   def add_track(self, track):
      self.tracks.append(track)
      return track

   def remove_track(self, track):
      self.tracks.remove(track)
      return track

   #TODO error OJO self.tracks(. No es un metodo
   def reorder_tracks(self, order=[]):
      new_order = []
      for index in range(len(order)):
         new_order.append(self.tracks(order[index]).copy())
      for track in self.tracks:
         if self.tracks.index(track) not in order:
            new_order.append(track.copy())        
      self.tracks = new_order

   #TODO igual que profile.path
   def set_path(self, path):
      self.path = path

   def import_tracks_from_parser(self, parser):
      for section in parser.sections():
         if section.count('track'):
            self.tracks.append(Track(parser.items(section)))

   def import_from_file(self, filepath):
      parser = ConfigParser.ConfigParser()
      parser.read(filepath)
      if not parser.has_section("data"):
         return False
      
      self.name = parser.get('data', 'name')
      if parser.has_option('data', 'execute'):
         self.execute = parser.get('data', 'execute')
      self.path = filepath
      self.import_tracks_from_parser(parser)
      return True

   def export_to_file(self, filepath=None): #MAYBE move to conf, for sure ONLY used by conf  
      if not filepath:
         filepath = self.path
               
      parser = ConfigParser.ConfigParser()
      parser.add_section('data')
      parser.set('data','name', self.name)
      if self.execute:
         parser.set('data','execute', self.execute)
      index = 1
      for track in self.tracks:
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
   """ 
   Custom dictionary focused on Galicaster's Track parameters handling.
   BASIC parameters allways exists and are properties
   It is capable of mantain the parameters ordered, for UI porpuses.
   
   Based on:
   http://stackoverflow.com/questions/2328235/pythonextend-the-dict-class

   """

   BASIC = ['name', 'device', 'flavor', 'location', 'file']

   def __init__(self, *args, **kw):
      super(Track,self).__init__(*args, **kw)

      for key in self.BASIC:
         if not self.has_key(key):
            self[key] = None

   def _get_name(self):
        return self['name']

   def _set_name(self, value):
        self['name'] = value

   name = property(_get_name, _set_name)

   def _get_device(self):
        return self['device']

   def _set_device(self, value):
        self['device'] = value

   device = property(_get_device, _set_device)

   def _get_flavor(self):
        return self['flavor']

   def _set_flavor(self, value):
        self['flavor'] = value

   flavor = property(_get_flavor, _set_flavor)

   def _get_location(self):
        return self['location']

   def _set_location(self, value):
        self['location'] = value

   location = property(_get_location, _set_location)

   def _get_file(self):
        return self['file']

   def _set_file(self, value):
        self['file'] = value

   file = property(_get_file, _set_file)

   def options_keys(self):
      sequence = []
      for key in self.keys():
         if key not in self.BASIC:
            sequence.append(key)
      return sequence

   def basic(self):      
      out = {}
      for key in self.BASIC:
         out[key] = self[key]
      return out

   def options(self):
      out = {}
      for key in self.options_keys():
         out[key] = self[key]
      return out
