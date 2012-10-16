# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/classui/statusbar
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.
"""
Widget holding multiple information about video status
"""

import gtk
import gobject
import os
from os import path
import datetime
import pango

from galicaster.classui import get_ui_path

EXP_STRINGS = [ (0, 'B'), (10, 'KB'),(20, 'MB'),(30, 'GB'),(40, 'TB'), (50, 'PB'),]
ONE_MB = 1024*1024

class StatusBarClass(gtk.Box):
    """
    Status Information of Galicaster
    """

    __gtype_name__ = 'StatusBarClass'

    def __init__(self):
        gtk.Box.__init__(self)
	builder = gtk.Builder()
        builder.add_from_file(get_ui_path('statusbar.glade'))
        self.bar = builder.get_object("statusbar")
        builder.connect_signals(self)

        self.status=builder.get_object("status")
        self.timer=builder.get_object("timer")
        self.video=builder.get_object("video")
        self.presenter=builder.get_object("presenter")

    def GetStatus(self):
        return self.status.get_text()    

    def GetTimer(self):
        return self.timer.get_text()

    def GetVideo(self):
        return self.video.get_text()

    def GetPresenter(self):
        return self.presenter.get_text()
    
    def SetStatus(self,element,value):
        self.status.set_text(value)

    def SetTimer(self,value):
        """Sets the timer on recording environments"""
        
        self.timer.set_text(self.time_readable(value))

    def SetTimer2(self,value,duration):
        """Sets the timer on reproduction environments"""
        self.timer.set_text(self.time_readable2(value,duration))
        

    def ClearTimer(self):
        """Empties the timer"""
        self.timer.set_text("")

    def SetVideo(self,element,value):
        if value != None:
            self.video.set_text(value)
            self.video.set_property("tooltip-text",value)

    def SetPresenter(self,element,value):
        if type(value) != str:
            text=", ".join(value)
        else:
            text=value
        self.presenter.set_text(text)
        self.presenter.set_property("tooltip-text",value)


    def update(self,status="Iddle",time="00:00",video="None",presenter="Unknow"):    
        """
        Get information from other modules to complete vumeter. 
        Run this function everytime we make a major change or connect it with signals such as play, pause, notebook->change_page ...
        """

        self.SetStatus(status)
        self.SetTimer(time)
        self.SetVideo(video)
        self.SetPresenter(presenter)

    def time_readable(self,seconds):
        """ Generates date hour:minute:seconds from seconds """		

        iso = int(seconds)
        dur = datetime.time(iso/3600,(iso%3600)/60,iso%60)		
        novo = dur.strftime("%H:%M:%S")
        return novo

    def time_readable2(self,s1,s2):
        """ Generates date hour:minute:seconds from seconds """		
        t1=self.time_readable(s1)
        t2=self.time_readable(s2)
        timing = t1+" / "+t2        
        return timing

    def make_human_readable(self,num):
        """Generates human readable string for a number.
        Returns: A string form of the number using size abbreviations (KB, MB, etc.) """
        i = 0
        while i+1 < len(EXP_STRINGS) and num >= (2 ** EXP_STRINGS[i+1][0]):
            i += 1
            rounded_val = round(float(num) / 2 ** EXP_STRINGS[i][0], 2)
        return '%s %s' % (rounded_val, EXP_STRINGS[i][1])


    def resize(self,size): 
        """Adapts GUI elements to the screen size"""
        altura = size[1]
        anchura = size[0]
        
        k = anchura / 1920.0 
        self.proportion = k
        
        def relabel(label,size,bold):           
            if bold:
                modification = "bold "+str(size)
            else:
                modification = str(size)
            label.modify_font(pango.FontDescription(modification))


        relabel(self.timer,k*32,True)
        relabel(self.video,k*32,True)
        relabel(self.presenter,k*32,True)
       
        return True

def GetFreeSpace(directorio): # TODO, this function belong in utils
    """ Return the freespace of the partition where a folder is placed -usually Repository- on human readeble style"""
        stats = os.statvfs(directorio)
        freespace=(stats.f_bsize * stats.f_bavail)
        return freespace,make_human_readable(freespace)

def make_human_readable(num):
        """Generates human readable string for a number.
        Returns: A string form of the number using size abbreviations (KB, MB, etc.) """
        i = 0
        while i+1 < len(EXP_STRINGS) and num >= (2 ** EXP_STRINGS[i+1][0]):
            i += 1
            rounded_val = round(float(num) / 2 ** EXP_STRINGS[i][0], 2)
        return '%s %s' % (rounded_val, EXP_STRINGS[i][1])

gobject.type_register(StatusBarClass)
