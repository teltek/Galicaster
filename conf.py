import sys, os
from ConfigParser import ConfigParser


class Conf:

   def __init__(self):
      self.conf = ConfigParser()
      self.conf.read('conf.ini')

   def open(self, filename):
       """open a custom configuration file"""
       self.conf.read(filename)

   def get(self, sect, opt):
       """return the value of option in section"""
       return self.conf.get(sect,opt)

   def get_section(self, sect):
       """Returns a dictionay instead of a list"""
       result = dict()
       for i in self.conf.items(sect):
           result[i[0]]=i[1]
       return result

   def set(self, sect, opt, value):
       self.conf.set(sect,opt,value)

   def new(self, section, option=None, value=None):
       """Creates a new section or option depending of the parameters"""
       self.conf.set(section,option,value)
       if option==None:
           self.conf.add_new_section(section)
       else:
           try:
               self.conf.set(section,option,value)
           except NoSectionError:
               self.conf.add_new_section(section)
               self.conf.set(section,option,value)

   def update(self):
      configfile=open("conf.ini","wb")
      self.conf.write(configfile)
      configfile.close()
      return 0

   def devices(self):
       d=[ "a" , "b" ]
       d[0] = ConfigParser() 
       d[1] = ConfigParser() 
       d[0].read(self.get("devices",self.get("track1","device")))
       d[1].read(self.get("devices",self.get("track2","device")))
       for a in d:
           if a.get("default","type")=="v4l2":
               comando="v4l2-ctl -d "+a.get("default","device")+" -i "+a.get("default","input")+" -s " + a.get("default","standard")
               os.system(comando)
               print "Dispositivo "+a.get("default","name")+" configurado"
           elif  a.get("default","type")=="v4l":
               comando="dov4l -d " + a.get("default","device") + " -i "+a.get("default","input")
               os.system(comando)
               print "Dispositivo "+a.get("default","name")+" configurado"
           else: print "Unknow device type"
