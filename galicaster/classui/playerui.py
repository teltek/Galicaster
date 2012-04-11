# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/ui/playerui
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


from os import path
import gobject
import gtk
import gst
import pango
import time
import logging
import threading

from galicaster.player import Player
from galicaster.core import context
from galicaster.classui.metadata import MetadataClass as Metadata
from galicaster.classui.statusbar import StatusBarClass
from galicaster.classui.audiobar import AudioBarClass
from galicaster.classui import message
from galicaster.classui import get_ui_path
from galicaster.mediapackage import mediapackage

gtk.gdk.threads_init()

GC_EXIT=-1
GC_INIT=0
GC_READY=1
GC_PLAY=2
GC_PAUSE=3
GC_STOP=4
GC_BLOCKED=5

log = logging.getLogger()

class PlayerClassUI(gtk.Box):
    """
    Graphic User Interface for Listing Player and Player Alone
    """
    __gtype_name__ = 'PlayerClass'


    def __init__(self,package=None):       
        gtk.Box.__init__(self)
	builder = gtk.Builder()
        builder.add_from_file(get_ui_path('player.glade'))

        # BUILD GUI
        self.playerui=builder.get_object("playerbox")
        #self.add(self.playerui)
        self.area1=builder.get_object("player_left")
        self.area2=builder.get_object("player_right")
        self.area1.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        self.area2.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        frame = builder.get_object("framebox")
        frame2 = builder.get_object("framebox2")
        frame.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_from_hsv(0,0,0.73))
        frame2.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_from_hsv(0,0,0.73))

        self.gui=builder

        # Seek Bar
        self.duration = 0
        self.seeking = False
        self.jump=0 # seek value
        self.jump_id=0 # seek signal id
        self.correct=False # To correct SCROLL_JUMP, after release it
        self.seek_bar=self.gui.get_object("seekbar")
        self.seek_bar.add_events(gtk.gdk.SCROLL_MASK)
        self.seek_bar.connect("change-value", self.on_seek) # FIXME connect only on playing/pause      
      
        # VUMETER
        self.audiobar=AudioBarClass(True)
        self.volume_bar = self.audiobar.volume
        self.volume_bar.connect("value-changed", self.on_volume2) 

        self.vubox = builder.get_object("vubox")
        self.vubox.add(self.audiobar.bar)

        # STATUSBAR
        self.statusbar= StatusBarClass()
        sbox = builder.get_object("statusbox")
        sbox.add(self.statusbar.bar)
      
        self.pack_start(self.playerui,True,True,0)

        self.status=GC_INIT
        self.previous=None
        self.change_state(GC_INIT)
        self.mediapackage=None # The Mediapackage being reproduced
        self.repository=context.get_repository() # FIXME what happens if you open a file not in the repository
        self.dispatcher = context.get_dispatcher()
        self.thread_id=None
        self.network=False
        builder.connect_signals(self)
        # CHANGE STATE??

        self.dispatcher.connect("update-play-vumeter", self.audiobar.SetVumeter)
        self.dispatcher.connect("play-stopped", self.change_state_bypass, GC_READY)
        self.dispatcher.connect("galicaster-status", self.event_change_mode)
        self.dispatcher.connect("galicaster-notify-quit", self.close)
        self.dispatcher.connect("net-up", self.network_status,True)
        self.dispatcher.connect("net-down", self.network_status,False)




#-------------------------- INIT PLAYER-----------------------
    def init_player(self,element,mp):
        """
        Send absolute file names and Drawing Areas to the player
        """
        # FIXME consultar configuracion de presenter,presentation left,right
        # FIXME mirar no mp que flavour ten cada video
        # TODO consider one track or more than two
        self.mediapackage = mp
        #videos = dict(zip(flavours,tracks)) # TODO ensure proper asignation

        videos = dict()
        areas = dict()
        for t in mp.getTracks():
            videos[t.getIdentifier()] = t.getURI()
            if (t.getMimeType().count("video")):
                if (t.getFlavor().count("presenter")):
                    areas[t.getIdentifier()] = self.area1
                if (t.getFlavor().count("presentation")):
                    areas[t.getIdentifier()] = self.area2

        self.seek_bar.set_value(0)
        self.player=Player(videos, areas)
        self.change_state(GC_READY)

        self.statusbar.SetVideo(None, self.mediapackage.title)
        self.statusbar.SetPresenter(None, self.mediapackage.getCreators())

    def play_from_list(self,mediapackage):

        if self.status == GC_PAUSE:
            self.on_stop_clicked()
            self.statusbar.ClearTimer()            

        self.init_player(None, mediapackage)
        self.duration = 0
        self.on_play_clicked(None) #autoplay

        

#------------------------- PLAYER ACTIONS ------------------------

    def on_play_clicked(self,button):
        self.player.play()
        self.clock=self.player.get_clock()#FIXME try to set clock on init
        #self.duration = self.player.get_duration()
        self.timer_thread = threading.Thread(target=self.timer_launch_thread)
        self.thread_id = 1
        self.timer_thread.daemon = True
        self.timer_thread.start()
        self.change_state(GC_PLAY)
        return True
        
    def on_pause_clicked(self, button=None):
        self.player.pause()
        self.change_state(GC_PAUSE)
        return True

    def on_stop_clicked(self, button=None):
        self.thread_id = None
        self.player.stop()
        self.seek_bar.set_value(0)
        self.statusbar.SetTimer2(0,self.duration)
        #self.duration = 0 # FIXME maybe wont work        
        self.change_state(GC_STOP)
        return True

    def on_quit_clicked(self,button):
        gui = gtk.Builder()
        gui.add_from_file(get_ui_path("quit.glade"))
        dialog = gui.get_object("dialog")
        response = dialog.run()
        if response == gtk.RESPONSE_OK:   
            dialog.destroy()
            if self.status > 0:
                self.player.quit()
            self.change_state(GC_EXIT)
            self.emit("delete_event", gtk.gdk.Event(gtk.gdk.DELETE))            
        else:
            dialog.destroy()
        return True

    def focus_out(self,button,event):
        self.player.pause()
        self.change_state(GC_STOP)

    def on_seek(self,button,scroll_type,new_value):
        """Move to the new position"""
        if new_value>100:
            new_value=100;
        temp=new_value*self.duration*gst.SECOND/100 # FIXME get_duration propertly
        #print "JUMP TO: "+str(new_value)

        if scroll_type == gtk.SCROLL_JUMP and not self.correct:
            self.seeking = True
            if self.player.get_status()[1] == gst.STATE_PLAYING:
                self.player.pause()
            value=new_value * self.duration // 100 
            self.statusbar.SetTimer2(value,self.duration)
            self.jump=temp
            if not self.jump_id:
                log.warning("Handling Seek Jump")
                self.jump_id=self.seek_bar.connect("button-release-event",self.on_seek,0)# FIXME ensure real release, not click                        
        if self.correct:
            self.correct=False            

        if scroll_type != gtk.SCROLL_JUMP: # handel regular scroll
            if scroll_type ==  gtk.SCROLL_PAGE_FORWARD or scroll_type ==  gtk.SCROLL_PAGE_BACKWARD:
                self.player.seek(temp, False)

            else: # handle jump
                self.player.seek(self.jump, True) # jump to the position where the cursor was released
                self.seek_bar.disconnect(self.jump_id)
                self.jump_id=0 # jump finished and disconnected
                self.correct=True # correction rutine activated
                self.seeking= False

    def on_volume(self, button, scroll_type, new_value):
        new_value = 120 if new_value > 120 else 0 if new_value < 0 else new_value
        self.player.set_volume(new_value/100.0)

    def on_volume2(self, button, new_value):
        self.player.set_volume(new_value*2.0)
        

#------------------------- PACKAGE ACTIONS ------------------------

    def on_edit_meta(self,button):
        meta=Metadata(self.mediapackage)
        context.get_repository().update(self.mediapackage)
        #self.change_state(self.previous)
        self.statusbar.SetVideo(None, self.mediapackage.title)
        self.statusbar.SetPresenter(None, self.mediapackage.getCreators())
        return True

    def on_zip(self,button): # UNUSED
        log.info("Export to a zip")
	builder = gtk.Builder() # create a module for dialogs
        builder.add_from_file(get_ui_path('save.glade'))
        dialog=builder.get_object("dialog")
        response = dialog.run()
        if response==1:
            #FIXME close dialog, open progress window, init thread
            self.repository.export_to_zip(self.mediapackage,dialog.get_filename())
            
            log.info("Mediapackage exported")  # FIXME include location on log
        elif response==0 :
            log.info("Export to zip canceled")
        dialog.destroy()
        return True

    def ingest(self,package):
        log.info("Ingest: " + package.identifier)
        if not self.network:
            text = {"title" : "Media Manager",
                    "main" : "No connection available with the\nMatterhorn Core available."}
            icon = message.WARNING
            buttons = ( gtk.STOCK_OK, gtk.RESPONSE_OK)

            size = [ self.window.get_screen().get_width(), 
                     self.window.get_screen().get_height() ]

            warning = message.PopUp(icon, text, size, 
                                    self.get_toplevel(), buttons)
   	elif self.repo.list_by_status(mediapackage.INGESTING):
            text = {"title" : "Media Manager",
                    "main" : "There is another recording being ingested.\nPlease wait until it's finished."}
            icon = message.WARNING
            buttons = ( gtk.STOCK_OK, gtk.RESPONSE_OK)
            
            size = [ self.window.get_screen().get_width(), 
                     self.window.get_screen().get_height() ]
            
            warning = message.PopUp(icon, text, size, 	         
                                    self.get_toplevel(), buttons)

        else:
            if package.status in [ mediapackage.RECORDED, mediapackage.PENDING, 
                                   mediapackage.INGESTED ]:
                context.get_worker().ingest(package)
            else:
                log.warning(package.identifier+" cant be ingest")
        return True

    def pending(self,package):
        
        if package.status in [ mediapackage.RECORDED, mediapackage.INGESTED ]:
            package.status= mediapackage.PENDING			
            self.repository.update(package)
        elif package.status == mediapackage.PENDING :
            package.status= mediapackage.RECORDED			
            self.repository.update(package)
            
       	else:
            log.warning(package.identifier+" cant be enqueued to Ingest")

    def old_on_question(self,button):

        package = self.mediapackage
        gui = gtk.Builder()
        if package.status == mediapackage.PENDING:
            gui.add_from_file(get_ui_path('ingest2.glade'))
        else:
            gui.add_from_file(get_ui_path('ingest.glade'))
                
        dialog = gui.get_object("dialog")
        dialog.set_transient_for(self.get_toplevel())
        
        text = gui.get_object("textlabel")	
            
        
        if package.status == mediapackage.INGESTED:
            text.set_text("This recording was already ingested.\n"+
                          "Do you want to enqueue for ingesting again?")
            
        elif package.status == mediapackage.PENDING:
            text.set_text("Do you wan to cancel the ingest,\n"+
                          "or do you want to ingest it now?")
		
        elif package.status == mediapackage.INGESTING:
            log.warning("#TODO: Send a warning, this package is already being ingested")

        elif package.status != mediapackage.RECORDED:
            log.warning(store[iterator][0]+" cant be ingested")
            return True

        response =dialog.run()
        if response == 1:
            self.pending(package)			
        elif response == 2:
            self.ingest(package)
        elif response == -1:
            self.pending(package)
        dialog.destroy()
        return True

    def on_question(self,button):
        package = self.mediapackage
        buttons = None


        if context.get_conf().get("ingest", "active") != "True":			
            text = {"title" : "Media Manager",
                    "main" : "The ingest service is disabled."}
            icon = message.WARNING
            buttons = ( gtk.STOCK_OK, gtk.RESPONSE_OK)

        elif package.status == mediapackage.PENDING:
            text = {"title" : "Media Manager",
                    "main" : "Do you wan to cancel the ingest,\n"+
                    "or do you want to ingest it now?"}
            
            buttons = ( "Cancel Ingest", gtk.RESPONSE_ACCEPT, 
                        "Ingest Now", gtk.RESPONSE_APPLY, 
                        gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT
				    )
            icon = message.QUESTION
			
        elif package.status in [ mediapackage.RECORDED, mediapackage.INGEST_FAILED ]:			
            text = {"title" : "Media Manager",
                    "main" : "Do you want to enqueue \n"+
                    "this recording for ingesting?"}

            buttons = ( "Ingest", gtk.RESPONSE_ACCEPT, 
                        "Ingest Now", gtk.RESPONSE_APPLY , 
                        gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT
                        )
            icon = message.QUESTION

        elif package.status == mediapackage.INGESTED:
			text = {"title" : "Media Manager",
				"main" : "This recording was already ingested.\n"+
				"Do you want to enqueue it again?"}

			buttons = ( "Ingest", gtk.RESPONSE_ACCEPT, 
				    "Ingest Now", gtk.RESPONSE_APPLY, 
				    gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT
				    )
			icon = message.WARNING

        elif package.status == mediapackage.INGESTING:
            text = {"title" : "Media Manager",
                    "main" : "This package is already being ingested."}
            icon = message.WARNING
            buttons = (gtk.STOCK_OK, gtk.RESPONSE_OK)


			
        else: 
            text = {"title" : "Media Manager",
                    "main" : "This recording can't be ingested."}
            icon = message.WARNING
            buttons = ( gtk.STOCK_OK, gtk.RESPONSE_OK)

        size = [ self.window.get_screen().get_width(), 
                 self.window.get_screen().get_height() ]

        warning = message.PopUp(icon, text, size, 
                                self.get_toplevel(), buttons)

        if warning.response == gtk.RESPONSE_OK: # Warning
            return True
        elif warning.response == gtk.RESPONSE_APPLY: # Force Ingest
            self.ingest(package)			
        elif warning.response == gtk.RESPONSE_ACCEPT: # Enqueue or cancel enqueue
            self.pending(package)

        return True
    

    def on_delete(self, button):
	log.info("Delete: "+self.mediapackage.title)
        t1 = "This action will remove the recording from the hard disk."
        t2 = 'Recording:  "' + self.mediapackage.title + '"'
        text = {"title" : "Delete",
                "main" : "Are you sure you want to delete?",
                "text" : t1+"\n\n"+t2
                }
        buttons = ( gtk.STOCK_DELETE, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
        size = [ self.window.get_screen().get_width(), self.window.get_screen().get_height() ]
        warning = message.PopUp(message.WARNING, text, size, 
                                self.get_toplevel(), buttons)

		
        if warning.response in message.POSITIVE:
            self.thread_id = None
            self.player.stop()
            self.statusbar.SetVideo(None, "")
            self.statusbar.SetPresenter(None, "")
            self.statusbar.ClearTimer()
            self.change_state(GC_INIT)
            self.repository.delete(self.mediapackage)
            self.mediapackage = None
            self.dispatcher.emit("change-mode", 1)
            
        return True
    
#-------------------------- UI ACTIONS -----------------------------

    def timer_launch_thread(self):
        thread_id= self.thread_id
        self.initial_time=self.clock.get_time()
        while not self.duration and self.duration == 0:
            self.duration = self.player.get_duration()
        gtk.gdk.threads_enter()
        self.statusbar.SetTimer2(0,self.duration)
        gtk.gdk.threads_leave()        
              
        self.volume_bar.set_value(0.5)

        while thread_id == self.thread_id:
            if not self.seeking :
                if not self.duration:
                    actual_time=self.clock.get_time()  
                    timer=(actual_time-self.initial_time)/gst.SECOND
                else:
                    try:
                        actual_time, format =self.player.get_position()
                    except:
                            actual_time = 0                        
                            log.warning("Query position failed")

                    timer = actual_time / gst.SECOND
                    self.seek_bar.set_value(timer*100/self.duration)
                if thread_id==self.thread_id:
                    gtk.gdk.threads_enter()
                    self.statusbar.SetTimer2(timer,self.duration)
                    gtk.gdk.threads_leave()
                    
            time.sleep(0.2)          
        return True

    def resize(self,size): # FIXME change alignments and 
        altura = size[1]
        anchura = size[0]
        
        # listl = self.gui.get_object("listlabel")
        # recl =  self.gui.get_object("reclabel")
        vubox = self.gui.get_object("vubox")
        calign = self.gui.get_object("c_align")
        sbox = self.gui.get_object("statusbox")
        k = anchura / 1920.0 # we assume 16:9 or 4:3?
        self.proportion = k

        def relabel(label,size,bold):           
            if bold:
                modification = "bold "+str(size)
            else:
                modification = str(size)
            label.modify_font(pango.FontDescription(modification))

        
        for name  in ["playbutton", "pausebutton", "stopbutton"]:
            button = self.gui.get_object(name) #100, 80
            button.set_property("width-request", int(k*100) )
            button.set_property("height-request", int(k*100) )
            
            image = button.get_children()
            if type(image[0]) == gtk.Image:
                image[0].set_pixel_size(int(k*80)) 

        for name  in ["editbutton", "ingestbutton", "deletebutton"]:
            button = self.gui.get_object(name) #100, 80
            button.set_property("width-request", int(k*85) )
            button.set_property("height-request", int(k*85) )
            
            image = button.get_children()            
            if type(image[0]) == gtk.Image:
                image[0].set_pixel_size(int(k*56))   

            elif type(image[0]) == gtk.VBox:
                for element in image[0].get_children():
                    if type(element) == gtk.Image:
                        element.set_pixel_size(int(k*46))              

        # relabel(listl,k*25,True)
        # relabel(recl,k*25,True)
        vubox.set_padding(0,int(k*10),int(k*20),int(k*40))
        calign.set_padding(int(k*20),int(k*10),int(k*20),int(k*20))
        sbox.set_padding(int(k*10),int(k*10),int(k*50),int(k*50))
  
        self.statusbar.resize(size)
        self.audiobar.resize(size)

        return True

    def event_change_mode(self, orig, old_state, new_state):
        if old_state == 2 and self.status == GC_PLAY:
            self.on_pause_clicked()
        

    def change_state_bypass(self,origin,state):
        self.change_state(state)
        return True

    def change_state(self,state):
        play=self.gui.get_object("playbutton")
        pause=self.gui.get_object("pausebutton")
        stop=self.gui.get_object("stopbutton")
        #out=self.gui.get_object("quitbutton")       

        editb=self.gui.get_object("editbutton")       
        #zipb=self.gui.get_object("zipbutton")       
        #ingestb=self.gui.get_object("ingestbutton")       
        deleteb=self.gui.get_object("deletebutton")       


        self.previous,self.status = self.status,state

        if state==GC_INIT:
            play.set_sensitive(False)
            pause.set_sensitive(False)
            stop.set_sensitive(False)
            #out.set_sensitive(True)
            editb.set_sensitive(False)
            #zipb.set_sensitive(False)
            #ingestb.set_sensitive(False)
            deleteb.set_sensitive(False)

        if state==GC_READY:
            play.set_sensitive(True)
            pause.set_sensitive(False)
            stop.set_sensitive(False)
            #out.set_sensitive(True)
            editb.set_sensitive(True)
            #zipb.set_sensitive(True)
            #if context.get_conf().get("ingest", "active") == "True":
            #    ingestb.set_sensitive(True)
            deleteb.set_sensitive(True)

        if state==GC_PLAY:
            play.set_sensitive(False)
            pause.set_sensitive(True)
            stop.set_sensitive(True)
            #out.set_sensitive(True)

        if state==GC_PAUSE:
            play.set_sensitive(True)
            pause.set_sensitive(False)
            stop.set_sensitive(True)
            #out.set_sensitive(True)
            
        if state==GC_STOP:
            play.set_sensitive(True)
            pause.set_sensitive(False)
            stop.set_sensitive(False)
            #out.set_sensitive(True)

        if state==GC_BLOCKED:
            play.set_sensitive(False)
            pause.set_sensitive(False)
            stop.set_sensitive(False)
            #out.set_sensitive(False)

    def network_status(self,signal,status):
        self.network = status


    def close(self, signal):
        self.thread_id=None
        if self.status in [GC_PLAY, GC_PAUSE]:
            self.player.quit()
        return True        

gobject.type_register(PlayerClassUI)
