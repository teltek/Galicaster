# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/classcore
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


import pygtk
pygtk.require('2.0')


import os
import sys
import types 
import shutil 
import glib
import logging

import gobject
gobject.threads_init()
import pygst
pygst.require('0.10')
import gst
import gst.interfaces
import gtk
import pango
gtk.gdk.threads_init() 

from galicaster.classui.recorderui import RecorderClassUI
from galicaster.classui.listing import ListingClassUI
from galicaster.classui.playerui import PlayerClassUI
from galicaster.classui.confui import ConfUI
from galicaster.classui.deviceui import DeviceUI
from galicaster.scheduler.scheduler import Scheduler
from galicaster.mediapackage import deserializer
from galicaster import context
from galicaster import __version__
from galicaster.classui import message

# TODO Pasar constantes a outro arquivo?
basic = [ "repository", "zip", "pipe"]
ingest = [ "host", "username", "password", "workflow" ] # FIXME take names from INI keys
screen = [ "player"]

log = logging.getLogger()

GC_EXIT=-1  # FIXME change to enum ask gtk constants
GC_INIT=0
GC_READY=1
GC_PREVIEW=2
GC_REC=3
GC_STOP=4
GC_BLOCKED=5

REC= 0
PLA= 2
MMA= 1
DIS= 3 # put distributor as 0

class Class():
    __def_win_size__ = (1024, 768)
    GC_INIT = 0  # TODO 
    GC_QUIT = -1 
    GC_OK = 1
    GC_ERROR = -2

    GC_RECORDER = 0 
    GC_PLAYER = 1
    GC_LISTING = 2

    def __init__(self):
        """
        Core class
        """
        self.status = GC_INIT
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_size_request(*self.__def_win_size__) #FIXME make it unchangable
        self.window.set_title("GaliCASTER Class " + __version__ );        
        self.window.connect('delete_event', lambda *x: self.on_delete_event())
        #self.window.connect('check-resize',self.resize)

        #vbox = gtk.VBox()
        self.nbox = gtk.Notebook()
        self.nbox.set_show_tabs(False)
        self.window.add(self.nbox)
        #self.window.add(vbox)

        self.function = self.GC_RECORDER
        
        #signals and location
        self.conf = context.get_conf() #FIXME its a singleton, trait it like that
        self.dispatcher = context.get_dispatcher()

        #GUI
        # Distribution
        dbuilder= gtk.Builder()
	guifile = os.path.join(os.path.dirname(os.path.abspath(__file__)),'classui', 'distrib.glade')
        dbuilder.add_from_file(guifile)
        dbox = dbuilder.get_object("distbox")
        br = dbuilder.get_object("button1")
        bm = dbuilder.get_object("button2")
        bq =  dbuilder.get_object("button3")
        br.connect("clicked", self.change_mode, REC)
        bm.connect("clicked", self.change_mode, MMA)
        bq.connect("clicked", self.quit)
        self.dbuilder=dbuilder
        about = dbuilder.get_object("aboutevent")
        about.connect("button-press-event", self.show_about)


        lbox3 = gtk.VBox()
        lbox3 .pack_start(dbox,True,True,0)

        self.recorder = RecorderClassUI()
        self.listing  = ListingClassUI()
        if self.conf.get("ingest", "active") == "True":
            self.scheduler = Scheduler()

        self.dispatcher.connect("start-record", self.recorder.on_scheduled_start)
        self.dispatcher.connect("stop-record", self.recorder.on_scheduled_stop)
        self.dispatcher.connect("change-mode", self.change_mode)
        self.dispatcher.connect("play-list", self.play_mp)

        #StripL
	guifile = os.path.join(os.path.dirname(os.path.abspath(__file__)),'classui', 'strip.glade')
        builder = gtk.Builder()
        builder.add_from_file(guifile)
        self.builder=builder
        self.strip=builder.get_object("stripbox")
        button = builder.get_object("previousbutton")
        about = builder.get_object("aboutevent")
        about.connect("button-press-event", self.show_about)
        
        lbox = gtk.VBox()

        lbox.pack_start(self.strip,False,False,0)
        lbox.pack_start(self.listing,True,True,0)
        button.connect("clicked", self.change_mode, DIS) # should be DIS

        #Player
        self.player = PlayerClassUI()
        
        #StripP
	guifile2 = os.path.join(os.path.dirname(os.path.abspath(__file__)),'classui', 'strip.glade')
        builder2 = gtk.Builder()
        builder2.add_from_file(guifile2)
        self.builder2=builder2
        self.strip2=builder2.get_object("stripbox")
        button = builder2.get_object("previousbutton")
        about = builder2.get_object("aboutevent")
        about.connect("button-press-event", self.show_about)
        lbox2 = gtk.VBox()

        lbox2.pack_start(self.strip2,False,False,0)
        lbox2.pack_start(self.player,True,True,0)
        button.connect("clicked", self.change_mode, MMA)

        #Notebook
        self.nbox.insert_page(self.recorder, gtk.Label("REC"), 0)        
        self.nbox.insert_page(lbox, gtk.Label("LIST"), 1) #FIXME add the listing object itself
        self.nbox.insert_page(lbox2, gtk.Label("PLAYER"), 2) 
        self.nbox.insert_page(lbox3, gtk.Label("DISTRIBUTION"), 3)     

        adminbar = self.create_admin_bar() # FIXME dont create it if not packed
        #vbox.pack_start(adminbar,False,False,0)
        #vbox.pack_start(self.recorder,True,True,0)
        
        #EN DEV.
        if self.conf.get("screen","cursor") == "False" :
            self.hide_cursor()# FIXME save the current cursor
        self.window.fullscreen()
        self.window.show_all()
        self.resize(0)
        self.fullscreen=True
        
        self.window.add_events(gtk.gdk.KEY_PRESS_MASK)
        self.window.connect("key-press-event",self.check_key)

        if self.conf.get("basic","admin") == "True":
            #self.dispatcher.emit("change-mode",DIS)
            self.nbox.set_current_page(DIS)
            #self.recorder.mute_preview(True)
        else: # if None or False
            self.nbox.set_current_page(REC)
            #self.dispatcher.emit("change-mode",REC)
            self.recorder.block()      
            #self.recorder.mute_preview(False)
     
    def on_delete_event(self):
        log.debug("Delete Event Received")
        self.quit("Main Window Quit")

################################# KEYS AND CURSOR #########################

    def check_key(self,source,event): # TODO
        """
        Filter Ctrl combinations for quit,restart and configuration 
        """
        if ((event.state & gtk.gdk.SHIFT_MASK and event.state & gtk.gdk.CONTROL_MASK) 
            and event.state & gtk.gdk.MOD2_MASK and
            (event.keyval in [gtk.gdk.keyval_from_name('q'), gtk.gdk.keyval_from_name('Q')])):
            self.quit(source)

        if ((event.state & gtk.gdk.CONTROL_MASK)  and
            (event.keyval in [gtk.gdk.keyval_from_name('r'), gtk.gdk.keyval_from_name('R')])):
            self.restart_preview(source)

        if ((event.state & gtk.gdk.CONTROL_MASK)  and
            (event.keyval in [gtk.gdk.keyval_from_name('d'), gtk.gdk.keyval_from_name('D')])):
            self.devices(source)

        if ((event.state & gtk.gdk.CONTROL_MASK)  and
            (event.keyval in [gtk.gdk.keyval_from_name('m'), gtk.gdk.keyval_from_name('M')])):
            self.on_metadata(source)

        if ((event.state & gtk.gdk.CONTROL_MASK)  and
            (event.keyval in [gtk.gdk.keyval_from_name('o'), gtk.gdk.keyval_from_name('O')])):
            #print "Opening File"
            filename=self.select_file()
            if filename != None:
                self.open_file(filename)
        else:
                pass
                #print "Folder Selection Canceled" 
            # if recorder is not recording open FileChooser in Repository
            # If the context its changed pause/stop the reproduction
            # 

        if ((event.state & gtk.gdk.CONTROL_MASK)  and
            (event.keyval in [gtk.gdk.keyval_from_name('p'), gtk.gdk.keyval_from_name('P')])):
            self.change_mode(None, PLA)

        if ((event.state & gtk.gdk.CONTROL_MASK)  and
            (event.keyval in [gtk.gdk.keyval_from_name('l'), gtk.gdk.keyval_from_name('L')])):
            self.change_mode(None, MMA)

        if ((event.state & gtk.gdk.CONTROL_MASK)  and
            (event.keyval in [gtk.gdk.keyval_from_name('k'), gtk.gdk.keyval_from_name('K')])):
               self.change_mode(None, REC)


        if ((event.state & gtk.gdk.CONTROL_MASK)  and
            event.keyval == gtk.gdk.keyval_from_name('Return') ):
            self.toggle_fullscreen(None)

        if ((event.state & gtk.gdk.CONTROL_MASK)  and
            (event.keyval in [gtk.gdk.keyval_from_name('1')])) :
            name = self.conf.get("screen","left")
            for track in self.conf.conf.sections():
                if track.count("track"):                    
                    if self.conf.get(track,"name") == name :
                        kind = self.conf.get(track,"device")
                        if kind == "mjpeg" or kind == "v4l2" :
                            self.video_control(None,self.conf.get(track,"location"))

        if ((event.state & gtk.gdk.CONTROL_MASK)  and
            (event.keyval in [gtk.gdk.keyval_from_name('2')])) :
            name = self.conf.get("screen","right")
            for track in self.conf.conf.sections():
                if track.count("track"):                    
                    if self.conf.get(track,"name") == name :
                        kind = self.conf.get(track,"device")
                        if kind == "mjpeg" or kind == "v4l2" :
                            self.video_control(None,self.conf.get(track,"location"))
        

        if ((event.state & gtk.gdk.CONTROL_MASK)  and
            (event.keyval in [gtk.gdk.keyval_from_name('3')])) :
            for track in self.conf.conf.sections():
                if track.count("track"):
                    kind = self.conf.get(track,"device")
                    if kind == "pulse":
                        active = self.conf.get(track,"active")
                        if active == "True":
                            self.volume_control(None)

        # TODO set a configurator for every device even for audio

        return True                                   

    def on_delete_event(self):
        log.debug("Delete Event Received")
        self.quit("Main Window Quit")

    def get_state(self, timeout=1): # NOT IN USE
        return self.pipeline.get_state(timeout=timeout)

    def hide_cursor(self): # 
        pixmap = gtk.gdk.Pixmap(None, 1, 1, 1)
        color = gtk.gdk.Color()
        invisible = gtk.gdk.Cursor(pixmap, pixmap, color, color, 0, 0)
        window=gtk.gdk.get_default_root_window()
        window.set_cursor(invisible)

    def show_cursor(self):
        window=gtk.gdk.get_default_root_window()
        window.set_cursor(gtk.gdk.Cursor(gtk.gdk.ARROW)) #FIXME recover regular cursor, store the cursor used before
      

################################# CONTROL ###############################


    def change_mode(self, origin, page):
        self.dispatcher.emit("galicaster-status", 
                             self.nbox.get_current_page(), page)
        self.nbox.set_current_page(page)
        


    def preferences(self,button):
        log.info('Configuration Window')
        novo = ConfUI(parent=self.window)
        self.recorder.reload_state_and_permissions()
        #self.conf.reload()

    def devices(self,button):
        log.info('Device Configuration Window')
        self.novo = DeviceUI(parent=self.window)
        # TODO connect to a signal that shifts the videos in realtime
        # FIXME if Save make changes permanents, if not reload conf as it was before       

        #self.recorder.reload_state_and_permissions()        
        #self.conf.reload() 


    def shift_videos(self,button): # usefull to core, in class done by DeviceUI, carefull with function
        if self.function == self.GC_PLAYER:
            # self.player.shift() this function also change the values in conf
            pass
        elif self.function == self.GC_RECORDER:
            # self.recorder.shift()
            pass
        elif self.function == self.GC_LISTING:
            # self.list_player.shift()
            pass
        
        # TODO shift videos inmediatly (and change the ini too)
        # Emit a signal to be catched by the active option (recorder,player) and change windows

    def quit(self,source,kind=None): #FIXME close pipes
        """Regulates program exit"""

#        if (self.function == self.GC_RECORDER and
#            self.statusbar.GetStatus() == "Recording"):            
#            print "# FIXME show warning dialog"
#            return True

        if type(kind) == gtk.gdk.Event:  # FIXME filter gtk.gdk.Event DELETE
            log.debug("Quit Galicaster on request")
            self.status = self.GC_QUIT 
            self.dispatcher.emit("galicaster-quit")
            self.show_cursor()
            gtk.main_quit()            
            gst.info("Quit Galicaster")

        else: 
            text = {"title" : "Galicaster",
                    "main" : "Are you sure you want to QUIT? ", 
                    }
            if self.recorder.status == GC_REC:
                text["text"] = "There is an ongoing recording"
            buttons = ( gtk.STOCK_QUIT, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
            size = [ self.window.get_screen().get_width(), self.window.get_screen().get_height() ]
            warning = message.PopUp(message.WARNING, text, size, 
                                     self.window, buttons)
            if warning.response in message.POSITIVE:

                log.info("Quit Galicaster")
                self.status = self.GC_QUIT   

                self.dispatcher.emit("galicaster-quit")
                #self.player.close() # NEW
                #self.recorder.close() # NEW

                self.show_cursor()
                gtk.main_quit()            
                gst.info("Quit Galicaster")
            else:
                log.info("Cancel Quit")
                #dialog.destroy()

    def volume_control(self,button):
        gvc_path=glib.find_program_in_path('gnome-volume-control')  # FIXME makes a segmentation fault if 'program' is wrong
        glib.spawn_async([gvc_path])       
        return True

    def video_control(self,button,device):
        log.info("guvcView executed")
        #print "GUVCVIEW EXECUTED"
        guvc_path=glib.find_program_in_path('guvcview')  # FIXME makes a segmentation fault if 'program' is wrong
        # Warning: New Dependency
        glib.spawn_async([guvc_path,'-o','-d',device])       
        return True

    def select_file(self):
        guifile = os.path.join(os.path.dirname(os.path.abspath(__file__)),'classui',"openfile.glade")
        gui = gtk.Builder()
        gui.add_from_file(guifile)     
        dialog = gui.get_object("dialog") 
        dialog.set_transient_for(self.window)
        response = dialog.run()    
        if response == 1 :
            filename = dialog.get_filename()
            #print filename
            dialog.destroy()          
            return filename
        else:
            dialog.destroy()
            return None           

        
    def open_file(self,filename): # REVIEW name, also checks if we should import it to the main repository
        """
        Open a single file for playing and editing
        """
        
        # shift to player if neccessary
        log.info("Opening a file")
        self.change_mode(None, PLA)

        # open dialog
        if os.path.isdir(filename):
            uri=os.path.join(filename,"manifest.xml")
        else:
            uri=os.path.join(os.path.abspath(filename),"manifest.xml")

        #print uri
        
        if not os.path.isfile(uri):            
            log.warn("Manifest doesnt exist")
            #raise TypeError, "Manifest doesnt exist"
            #print "Manifest doesnt exist"
            # try to play wathever it is (2 videos and 1 audio)
        else:
            mp=deserializer.fromXML(uri)
            self.dispatcher.emit("play-list", mp)

    def play_mp(self,origin, mediapackage): # REVIEW name, also checks if we should import it to the main repository
        """
        Plays a mediapackage
        """
        self.player.play_from_list(mediapackage)
        self.change_mode(None, PLA)


######################### DEVELOPER BAR #######################

    def create_admin_bar(self): #Use this for developing purposes
	builder = gtk.Builder()
        builder.add_from_file(os.path.join(os.path.dirname(os.path.abspath(__file__)),'classui','adminbar.glade'))  
        builder.connect_signals(self)
        return builder.get_object("adminbar")

    def show_about(self,button=None,tipe = None):
        gui = gtk.Builder()
        gui.add_from_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'classui', 'about.glade'))
        dialog = gui.get_object("dialog")
        dialog.set_transient_for(self.window)        

        response = dialog.run()
        if response:
            dialog.destroy()
        else:
            dialog.destroy()
        return True


    def toggle_fullscreen(self,button): 
        if not self.fullscreen:
            self.window.fullscreen()            
            self.fullscreen=True
            self.resize(0)
        elif self.fullscreen:
            self.window.unfullscreen()
            self.fullscreen=False
            self.resize(1)
        return True

    def restart_preview(self,button): 
        #print "TODO check if restart is avaliable and do it"
        self.recorder.restart()
        return True

    def on_metadata(self,button): # FIXME dont give focus to the new window, to avoid losing fullscreen
        self.recorder.on_edit_meta(None)    

    def resize(self,elemente,event=None): 

        #builder = gtk.Builder()
        #builder.add_from_file(os.path.join(os.path.dirname(os.path.abspath(__file__)),"classui", 'strip.glade'))

	def relabel(label,size,bold):           
            if bold:
                modification = "bold "+str(size)
            else:
                modification = str(size)
            label.modify_font(pango.FontDescription(modification))


        if elemente==0:
            screen=self.window.get_screen()
            anchura = screen.get_width()
            if anchura not in [1024,1280,1920]:
                anchura = 1920
            self.recorder.resize([anchura, screen.get_height()])   
            self.listing.resize([anchura, screen.get_height()])   
            self.player.resize([anchura, screen.get_height()])   

        elif elemente == 1:
            anchura = 1024
            self.recorder.resize([anchura,768])
            self.listing.resize([anchura,768])
            self.player.resize([anchura,768])
    
   
        else:
            self.recorder.resize(self.window.get_size()) # NEVER CALLED
            self.listing.resize(self.window.get_size()) # NEVER CALLED
        k= anchura / 1920.0
        image=gtk.gdk.pixbuf_new_from_file(os.path.join(os.path.dirname(os.path.abspath(__file__)),"classui", "logo"+str(anchura)+".png"))

        # Strip
        align2 = self.builder.get_object("top_align")
        align2p = self.builder2.get_object("top_align")
        logo2 = self.builder.get_object("logo2")
        logo2p = self.builder2.get_object("logo2")

        logo2.set_from_pixbuf(image)
        logo2p.set_from_pixbuf(image)
        align2.set_padding(int(k*55),int(k*31),int(k*120),int(k*120))
        align2p.set_padding(int(k*55),int(k*31),int(k*120),int(k*120))

        for name  in ["previousbutton"]:
            button = self.builder.get_object(name)
            button.set_property("width-request", int(k*70) )
            button.set_property("height-request", int(k*70) )
            
            image = button.get_children()
            if type(image[0]) == gtk.Image:
                image[0].set_pixel_size(int(k*56))

        for name  in ["previousbutton"]:
            button = self.builder2.get_object(name)
            button.set_property("width-request", int(k*70) )
            button.set_property("height-request", int(k*70) )
            
            image = button.get_children()
            if type(image[0]) == gtk.Image:
                image[0].set_pixel_size(int(k*56))  

        # Distribution
        logos = self.dbuilder.get_object("logo_align")
        logos.set_padding(int(k*56),int(k*45),int(k*120),int(k*120))
        disal = self.dbuilder.get_object("dis_align")
        disal.set_padding(int(k*25),int(k*25),int(k*50),int(k*50))

        l1 = self.dbuilder.get_object("reclabel")
        l2 = self.dbuilder.get_object("mmlabel")
        i1 = self.dbuilder.get_object("recimage")
        i2 = self.dbuilder.get_object("mmimage")
        b1 = self.dbuilder.get_object("button1")
        b2 = self.dbuilder.get_object("button2")
	relabel(l1,k*48,True)
        relabel(l2,k*48,True)  
        i1.set_pixel_size(int(k*120))
        i2.set_pixel_size(int(k*120))
        b1.set_property("width-request", int(k*500) )
        b2.set_property("width-request", int(k*500) )
        b1.set_property("height-request", int(k*500) )
        b2.set_property("height-request", int(k*500) )
            

   
        lclass = self.dbuilder.get_object("logo2")
        lcompany = self.dbuilder.get_object("logo1")
        iclass=gtk.gdk.pixbuf_new_from_file(os.path.join(os.path.dirname(os.path.abspath(__file__)),"classui", "logo"+str(anchura)+".png"))
        icompany=gtk.gdk.pixbuf_new_from_file(os.path.join(os.path.dirname(os.path.abspath(__file__)),"classui", "teltek"+str(anchura)+".png"))
        lclass.set_from_pixbuf(iclass)
        lcompany.set_from_pixbuf(icompany)


        return True                   
