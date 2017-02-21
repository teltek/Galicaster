# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/ui/calendarwindow
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


#     This file is part of Bitacora. 
#     Please, read the "Copyright" and "LICENSE" variables for copyright advisement
#   (just below this line):

# Bitacora is a TODO Manager and a Binacle of TODOs
COPYRIGHT = "Copyright 2007-2009 Miguel Angel Garcia Martinez <miguelangel.garcia@gmail.com>"

LICENSE = """
    This file is part of Bitacora.

    Bitacora is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Bitacora is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Bitacora.  If not, see <http://www.gnu.org/licenses/>.
"""

import datetime
import time
from gi.repository import Gtk

from galicaster.classui import get_ui_path


class CalendarWindow:
    date = None

    # DESTROY WITH PARENT
    # QUIT ON ESCAPE PRESSED (selected_none)
    # ORANGE HIGHLIGTHNING
    # Check focus-out-event
    #

    def __init__(self, initial_value=0, parent_window=None):
        #print "Running CalendarWindow"
        self.gi = Gtk.Builder()
        self.gi.add_from_file(get_ui_path('datetime.glade'))
        self.gi.connect_signals(self)   

        self.w = self.gi.get_object("dialog1") 
        if parent_window:
            parent_window.set_transient_for(self) 
        self.w.connect("focus-out-event",self.do_hide_calendar) 
        self.calendar=self.gi.get_object("calendar1")
        if not initial_value:
            year, month, day, hour, minute, second, dow, doy, isdst = time.localtime()
        else:
            year, month, day, hour, minute, second, dow, doy, isdst = initial_value.timetuple()
        self.calendar.select_month(month-1, year)
        self.calendar.select_day(day)
        spinhour = self.gi.get_object("hours")
        spinhour.set_value(hour)
        spinminute = self.gi.get_object("minutes")
        spinminute.set_value(minute)
        
        
    def run(self, data=None):
        result = self.w.run()
        return result

    def do_hide_calendar(self, calendarwindow):
        pass
        #print "Hiding calendar"
        # self.w.hide()
        
    def do_select_current(self, button):        
        #print "Current date choosen"
        self.date = datetime.datetime.now().replace(microsecond=0)
        self.w.hide()
        # return datetime.datetime.now().replace(microsecond=0)
                
    def do_select_none(self, button):
        #print "No date selected"
        self.date = None
        self.w.hide()
        # return 2

    def do_select_day(self, calendar):
        #print "Selecting day"
        value = self.gi.get_object("calendar1").get_date()
        hour = self.gi.get_object("hours").get_value_as_int()
        minute = self.gi.get_object("minutes").get_value_as_int()
        self.date = datetime.datetime(value[0], value[1]+1,value[2],hour,minute,0)
        self.w.hide()
        # return datetime.datetime(value[0], value[1]+1,value[2],hour,minute,0)

def main():
    CalendarWindow() 
    #print "through the main function"
    Gtk.main()
    

if __name__=='__main__':
    main()

