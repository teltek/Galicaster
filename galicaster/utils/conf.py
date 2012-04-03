# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/conf
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

import os
import sys
import ConfigParser
import logging

log = logging.getLogger()

class Conf:

   def __init__(self, conf_file = None):

      if conf_file != None:
         self.conf_file = conf_file 
      else:
         self.conf_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'conf.ini')
         

      self.conf = ConfigParser.ConfigParser() #
      # FIXME when using 2.7 dict_type=collections.OrderedDict)
      self.conf.read(self.conf_file)# FIXME stablish file as constat

   def reload(self):
      self.conf.read(self.conf_file)

   def open(self, filename):
       """Open a custom configuration file"""
       self.conf.read(filename)

   def get(self, sect, opt):
       """Return the value of option in section"""
       try:
          response = self.conf.get(sect, opt)
       except:
          response = None
       return response

   def get_section(self, sect):
       """Returns a dictionay instead of a list"""
       return dict(self.conf.items(sect))

   def set(self, sect, opt, value):
       self.conf.set(sect, opt, value)

   def new(self, section, option=None, value=None):
       """Creates a new section or option depending of the parameters"""
       self.conf.set(section, option, value)
       if option==None:
           self.conf.add_new_section(section)
       else:
           try:
               self.conf.set(section, option, value)
           except ConfigParser.NoSectionError:
               self.conf.add_new_section(section)
               self.conf.set(section, option, value)

   def update(self):
      """
      Update the configuration file
      """
      configfile=open("conf.ini","wb")
      self.conf.write(configfile)
      configfile.close()
      return 0


   def getBins(self, base_path):
      """
      Generate list for Recorder.
      """
      no_in_options = ['active', 'flavor', 'device', 'location', 'file']
      bins = []
      index = 0
      while True:
         index += 1
         section = 'track' + str(index)
         try:
            if self.conf.get(section, 'active', 'True') == 'True': #FIXME get as a boolean
               if self.conf.get(section, 'device') == 'hauppauge': #FIXME make generic
                  try: # FIXME take out
                     other_dev = str(int(self.conf.get(section, 'location')[-1:]) + 32)
                  except:
                     other_dev = "32"
                  hau= {'name': self.conf.get(section, "name"), 
                        'dev': { 'file' :  self.conf.get(section, 'location') , 'device' : self.conf.get(section, 'locprevideo'), 'audio' :  self.conf.get(section, 'locpreaudio') },
                        'file': os.path.join(base_path, self.conf.get(section, 'file')),
                        'klass' : 'hauppauge.GChau',
                        'options' : self.get_section(section) #FIXME extract no_in_options
                        }
                  bins.append(hau)
               else:
                  values = {
                     'name' : self.conf.get(section, "name"),
                     'dev' : self.conf.get(section, 'location'),
                     'file' : os.path.join(base_path, self.conf.get(section, 'file')),
                     'klass' : self.conf.get(section, 'device') + '.GC' + self.conf.get(section, 'device'),
                     'options' : self.get_section(section)
                     }
                  bins.append(values)
         

         except ConfigParser.NoSectionError:
            break
      return bins


      

   def devices(self): # Not in use
       d=[ "a" , "b" ]
       d[0] = ConfigParser.ConfigParser(dict_type=collections.OrderedDict) 
       d[1] = ConfigParser.ConfigParser(dict_type=collections.OrderedDict)
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
         return self.conf.getboolean("allows",permit)
      except:
         log.error("Unknow permission")
         return None

   def new_track(self, name, kind, flavor, location, archive, vumeter = False, playing = False): # FIXME transform parameters into a dictionary 

      number=self._get_free_number()
      section="track"+str(number)
      self.conf.add_section(section)

      # Name
      if name not in ["",None,]:
         self.conf.set(section, "name",name)# FIXEM check for repeated names
      else:
         self.conf.set(section, "name","device"+number)

      # Type      
      self.conf.set(section, "device",kind) # OBLIGATORY

      # Flavor
      if flavor != None:
         self.conf.set(section, "flavor",flavor)
      else:
         self.conf.set(section, "flavor",other)

      # Location of the device
      self.conf.set(section, "location", location) # OBLIGATORY

      # File to be recorded in
      self.conf.set(section, "file",archive)

      # Default values
      self.conf.set(section, "active", "False")

      if kind == "pulse":
         self.conf.set(section, "vumeter", "False")
         self.conf.set(section, "playing", "False")

      if kind == "mjpeg":
         self.conf.set(section, "videocrop-left", 160)
         self.conf.set(section, "videocrop-right", 160)
         self.conf.set(section, "caps", "image/jpeg,framerate=24/1,width=1280,height=720")

      if kind == "vga2usb":
         pass # FIXME set proper caps

      #REMEMBER TO reload device


   def delete_track(self,section):
      self.conf.remove_section(section)
      return True


   def modify_track(self,section,options): # options a dictionary
      for key in options.keys():
         self.conf.set(section,key,options[key])
      return True
   
   def _get_free_number(self):
      for i in range(100):
         if not self.conf.has_section("track"+str(i)):
            return i
