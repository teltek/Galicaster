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

# TODO
# * in getBins for options extract no_in_options keys
# * in getBins do hauppauge generic.

"""
TODO Add Description
"""

import os
import sys
import logging
import ConfigParser
import collections

log = logging.getLogger()

class Conf(object):

   def __init__(self, conf_file=None, conf_dist_file=None):
      self.__conf = ConfigParser.ConfigParser() #
      self.__user_conf = ConfigParser.ConfigParser() #
      # FIXME when using 2.7 dict_type=collections.OrderedDict)

      self.conf_file = conf_file or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'conf.ini'))
      self.conf_dist_file = conf_dist_file or os.path.join(os.path.dirname(self.conf_file), "conf-dist.ini")
         
      self.reload()


   def reload(self):
      """
      Reload the configurations
      """
      self.__conf.read((self.conf_dist_file, self.conf_file))
      self.__user_conf.read(self.conf_file)


   def get(self, sect, opt):
       """
       Return the value of option in section
       """
       try:
          response = self.__conf.get(sect, opt)
       except:
          response = None
       return response


   def get_section(self, sect):
       """
       Returns a dictionay instead of a list
       """
       return dict(self.__conf.items(sect))


   def set(self, sect, opt, value):
      """
      Set the specified option from the specified section. 
      If the section does not exist.
      """
      self.__force_set(self.__user_conf, sect, opt, value)
      self.__force_set(self.__conf, sect, opt, value)


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
      configfile = open(self.conf_file, "wb")
      self.__user_conf.write(configfile)
      configfile.close()


   def getBins(self, base_path):
      """
      Generate list for Recorder.
      """
      no_in_options = ['active', 'flavor', 'device', 'location', 'file']
      bins = []
      index = 0
      while True:
         index += 1
         section = 'track' + unicode(index)
         try:
            if self.__conf.get(section, 'active', 'True') == 'True': #FIXME get as a boolean
               if self.__conf.get(section, 'device') == 'hauppauge': #FIXME make generic
                  try: # FIXME take out
                     other_dev = unicode(int(self.__conf.get(section, 'location')[-1:]) + 32)
                  except:
                     other_dev = "32"
                  hau= {'name': self.__conf.get(section, "name"), 
                        'dev': { 'file' :  self.__conf.get(section, 'location') , 'device' : self.__conf.get(section, 'locprevideo'), 'audio' :  self.__conf.get(section, 'locpreaudio') },
                        'file': os.path.join(base_path, self.__conf.get(section, 'file')),
                        'klass' : 'hauppauge.GChau',
                        'options' : self.get_section(section) #FIXME extract no_in_options
                        }
                  bins.append(hau)
               else:
                  values = {
                     'name' : self.__conf.get(section, "name"),
                     'dev' : self.__conf.get(section, 'location'),
                     'file' : os.path.join(base_path, self.__conf.get(section, 'file')),
                     'klass' : self.__conf.get(section, 'device') + '.GC' + self.__conf.get(section, 'device'),
                     'options' : self.get_section(section)
                     }
                  bins.append(values)
         

         except ConfigParser.NoSectionError:
            break
      return bins

   def get_tracks(self):
      #TODO make a test
      tracks = []
      index = 0
      while True:
         index += 1
         section = 'track' + unicode(index)
         if self.__conf.has_section(section):
            tracks.append(self.get_section(section))
         else:
            break

      return tracks  

   def get_tracks_in_mh_dict(self):
      #TODO make a test
      tracks = {}
      index = 0
      names = []
      while True:
         index += 1
         section = 'track' + unicode(index)
         if self.__conf.has_section(section):
            if self.get(section, 'active') == 'True':
               name = self.get(section, 'name')
               names.append(name)
               tracks['capture.device.' + name + '.flavor']     = self.get(section, 'flavor') + '/source' 
               tracks['capture.device.' + name + '.outputfile'] = self.get(section, 'file')
               tracks['capture.device.' + name + '.src']        = self.get(section, 'location')
         else:
            break

      if names:
         tracks['capture.device.names'] = ",".join(names)

      return tracks  


      
   def devices(self): # Not in use
       d=[ "a" , "b" ]
       try:
          d[0] = ConfigParser.ConfigParser(dict_type=collections.OrderedDict) 
          d[1] = ConfigParser.ConfigParser(dict_type=collections.OrderedDict)
       except:
          d[0] = ConfigParser.ConfigParser()
          d[1] = ConfigParser.ConfigParser()
       d[0].read(self.get("devices",self.get("track1","device")))
       d[1].read(self.get("devices",self.get("track2","device")))
       for a in d:
           if a.get("default","type")=="v4l2":
               comando="v4l2-ctl -d "+a.get("default","device")+" -i "+a.get("default","input")+" -s " + a.get("default","standard")
               os.system(comando)
           elif  a.get("default","type")=="v4l":
               comando="dov4l -d " + a.get("default","device") + " -i "+a.get("default","input")
               os.system(comando)
           else: print "Unknow device type"

   def get_permission(self,permit):
      try: 
         return self.__conf.getboolean("allows",permit)
      except:
         log.error("Unknow permission")
         return None

      # TODO Move all above to Device Configurator
      # FIXME transform parameters into a dictionary 
   def new_track(self, name, kind, flavor, location, archive, vumeter = False, playing = False):

      number=self.__get_free_number()
      section="track"+unicode(number)
      self.__conf.add_section(section)

      # Name
      if name not in ["",None,]:
         self.__conf.set(section, "name",name)# FIXEM check for repeated names
      else:
         self.__conf.set(section, "name","device"+number)

      # Type      
      self.__conf.set(section, "device",kind) # OBLIGATORY

      # Flavor
      if flavor != None:
         self.__conf.set(section, "flavor",flavor)
      else:
         self.__conf.set(section, "flavor",other)

      # Location of the device
      self.__conf.set(section, "location", location) # OBLIGATORY

      # File to be recorded in
      self.__conf.set(section, "file",archive)

      # Default values
      self.__conf.set(section, "active", "False")

      if kind == "pulse":
         self.__conf.set(section, "vumeter", "False")
         self.__conf.set(section, "playing", "False")

      if kind == "mjpeg":
         self.__conf.set(section, "videocrop-left", 160)
         self.__conf.set(section, "videocrop-right", 160)
         self.__conf.set(section, "caps", "image/jpeg,framerate=24/1,width=1280,height=720")

      if kind == "vga2usb":
         pass # FIXME set proper caps

      #REMEMBER TO reload device


   def delete_track(self,section):
      self.__conf.remove_section(section)
      return True


   def modify_track(self,section,options): # options a dictionary
      for key in options.keys():
         self.__conf.set(section,key,options[key])
      return True
   
   def __get_free_number(self):
      for i in range(100):
         if not self.__conf.has_section("track"+unicode(i)):
            return i
