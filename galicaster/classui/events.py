# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/ui/metadata
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


import gtk
import datetime
import pango
from os import path
import gobject
import datetime

from galicaster.mediapackage import mediapackage
from galicaster.core import context
from galicaster.classui import get_ui_path

HOW_MANY=5
RESOLUTION = [1920, 1080]
#PROPORTIONS = "16:9"


class EventManager(gtk.Widget):
    """
    Handle the event pop up
    """
    __gtype_name__ = 'EventManager'

    def __init__(self, number = None, size = None, parent = None): 

        if number == None:
            number = HOW_MANY
        
        if size == None:
            size = RESOLUTION
        if parent != None:
            screen=parent.get_toplevel().get_screen()
            size = [screen.get_width(), screen.get_height()]

        altura = size[1]
        anchura = size[0]
        
        k1 = anchura / 1920.0                                      
        k2 = altura / 1080.0
            
        self.size = int(k1*30)
        self.pater = parent

        gui = gtk.Builder()
        gui.add_from_file(get_ui_path('next.glade'))
        dialog = gui.get_object("dialog")
        table = gui.get_object("infobox")
        title = gui.get_object("titlelabel")
        okb = gui.get_object("okbutton")

        modification = "bold "+str(int(k2*35))+"px"        
        title.modify_font(pango.FontDescription(modification))

        # mediapackages
        mps=context.get_repository().get_next_mediapackages()
        row=1

        self.dialog=dialog
        if parent != None:
            dialog.set_transient_for(parent.get_toplevel())

                                        
        for mp in mps:           
            t = self.big_label(mp.title, self.size)
            t.set_width_chars(int(k1*50))
            t.set_line_wrap(True)
            allocation = t.get_allocation()
            t.set_size_request( int(k1* 500) , -1 ) # FIXEME
            #Hack by http://tadeboro.blogspot.com/2009/05/wrapping-adn-resizing-gtklabel.html

            rec_time = mp.getLocalDate()
            if rec_time.date() == datetime.date.today():
                upcoming = "Today"
            elif rec_time.date() == ( datetime.date.today()+datetime.timedelta(1) ):
                upcoming = "Tomorrow"
            else:
                upcoming = mp.getDate().strftime("%d %b %Y") 
                # day_number month_abr year full
                
            d = self.big_label(upcoming,self.size)
            d.set_width_chars(int(k1*20))

            h = self.big_label(rec_time.time().strftime("%H:%M"),self.size)
            h.set_width_chars(int(k1*12)) 

            #l = gtk.Label("Record Now") # set attributes
            b = gtk.Button("Record Now")
            b.set_alignment(0.5,0.5)
            b.set_property("tooltip-text","Record Now")
            b.connect("button-press-event",self.send_start, mp.identifier)
            b.set_property("width-request", int (k1*180))
            b.set_property("height-request", int (k2*70))

            table.attach(t,0,1,row-1,row,gtk.EXPAND|gtk.FILL,False,0,0)
            table.attach(d,1,2,row-1,row,gtk.EXPAND|gtk.FILL,False,0,0)
            table.attach(h,2,3,row-1,row,gtk.EXPAND|gtk.FILL,False,0,0)
            table.attach(b,3,4,row-1,row,gtk.EXPAND|gtk.FILL,False,0,0)
            t.show()
            h.show()
            d.show()
            b.show()
            row += 1
            if row >= number+1 :
                break  

        okb.connect("button-press-event",self.destroy)

        response = dialog.run()

        return None

    def send_start(self,origin, event, data):
        self.pater.dispatcher.emit("start-before", data)
        self.dialog.destroy()
        return True

    def big_label(self,text,size): # FIXME use this in more places
        label=gtk.Label(text)
        tamanho = pango.FontDescription(str(size)+"px")
        label.modify_font(tamanho)
        label.set_justify(gtk.JUSTIFY_LEFT)
        label.set_alignment(0,0)
        return label

    def resize(self,size): # FIXME change alignments and 
        altura = size[1]
        anchura = size[0]
    
        k1 = anchura / 1920.0 # we assume 16:9 or 4:3?
        k2 = altura / 1080.0
        self.proportion = k1

        title = self.gui.get_object("titlelabel")
        okl =  self.gui.get_object("oklabel")
        
        def relabel(label,size,bold):           
            if bold:
                modification = "bold "+str(size)+"px"
            else:
                modification = str(size)
            label.modify_font(pango.FontDescription(modification))

        relabel(title,int(k1*28),True)
        relabel(okl,int(k1*28),True)
        self.size = k1*20


       
        return True

    def destroy(self, button = None, event = None):
        self.dialog.destroy()
        return True

gobject.type_register(EventManager)
