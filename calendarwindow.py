#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

import datetime,time
import gtk, gobject, pygtk


class CalendarWindow:
    date = None

    # DESTROY WITH PARENT
    # QUIT ON ESCAPE PRESSED (selected_none)
    # ORANGE HIGHLIGTHNING
    # Check focus-out-event
    #

    def __init__(self, initial_value=0, parent_window=None):
        print "Running CalendarWindow"
        self.gifile = "datetime.glade"
        self.gi = gtk.Builder()
        self.gi.add_from_file(self.gifile)
        self.gi.connect_signals(self)   

        self.w = self.gi.get_object("dialog1") 
        if parent_window:
            parent_window.set_transient_for(self) 
        self.w.connect("focus-out-event",self.do_hide_calendar) 
        self.calendar=self.gi.get_object("calendar1")
        year, month, day, hour, minute, second, dow, doy, isdst = time.localtime()
        self.calendar.select_month(month-1, year)
        self.calendar.select_day(day)
        
    def run(self, data=None):
        result = self.w.run()
        return result

    def do_hide_calendar(self, calendarwindow):
        print "Hiding calendar"
        # self.w.hide()
        
    def do_select_current(self, button):        
        print "Current date choosen"
        self.date = datetime.datetime.now().replace(microsecond=0)
        self.w.hide()
        # return datetime.datetime.now().replace(microsecond=0)
                
    def do_select_none(self, button):
        print "No date selected"
        self.date = None
        self.w.hide()
        # return 2

    def do_select_day(self, calendar):
        print "Selecting day"
        value = self.gi.get_object("calendar1").get_date()
        hour = self.gi.get_object("hours").get_value_as_int()
        minute = self.gi.get_object("minutes").get_value_as_int()
        self.date = datetime.datetime(value[0], value[1]+1,value[2],hour,minute,0)
        self.w.hide()
        # return datetime.datetime(value[0], value[1]+1,value[2],hour,minute,0)

def main():
    w =  CalendarWindow() 
    print "through the main function"
    gtk.main()
    

if __name__=='__main__':
    main()


