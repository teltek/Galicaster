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
"""
UI for the player area
"""


from os import path
import gobject
import gtk
import gst
import time
import logging
import threading

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict

from galicaster.classui.managerui import ManagerUI
from galicaster.player import Player
from galicaster.core import context
from galicaster.classui.statusbar import StatusBarClass
from galicaster.classui.audiobar import AudioBarClass
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

class PlayerClassUI(ManagerUI):
    """
    Graphic User Interface for Listing Player and Player Alone
    """
    __gtype_name__ = 'PlayerClass'
    
    
    def __init__(self,package=None):       
        ManagerUI.__init__(self,1)
	builder = gtk.Builder()
        builder.add_from_file(get_ui_path('player.glade'))
        self.gui=builder

        # BUILD GUI
        self.playerui = builder.get_object("playerbox")
        self.main_area = builder.get_object("videobox")
        self.player = None

        # Seek Bar
        self.duration = 0
        self.seeking = False
        self.jump=0 # seek value
        self.jump_id=0 # seek signal id
        self.correct=False # To correct SCROLL_JUMP, after release it
        self.seek_bar=self.gui.get_object("seekbar")
        self.seek_bar.add_events(gtk.gdk.SCROLL_MASK)
        self.seek_bar.connect("change-value", self.on_seek) 
      
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
      
        self.playerui.pack_start(self.strip,False,False,0)
        self.playerui.reorder_child(self.strip,0)
        self.pack_start(self.playerui,True,True,0)

        self.status=GC_INIT
        self.previous=None
        self.change_state(GC_INIT)
        self.mediapackage=None # The Mediapackage being reproduced

        self.thread_id=None
        builder.connect_signals(self)

        self.dispatcher.connect("update-play-vumeter", self.audiobar.SetVumeter)
        self.dispatcher.connect("play-stopped", self.change_state_bypass, GC_READY)
        self.dispatcher.connect("galicaster-status", self.event_change_mode)
        self.dispatcher.connect("galicaster-notify-quit", self.close)


#-------------------------- INIT PLAYER-----------------------
    def init_player(self,element,mp):
        """Send absolute file names and Drawing Areas to the player."""
        self.mediapackage = mp

        tracks = OrderedDict()
        videos = OrderedDict()

        index = 0
    
        for t in mp.getTracks(): 
            if not t.getFlavor().count('other'):
                tracks[t.getIdentifier()] = t.getURI()

            if (t.getMimeType().count("video") and not t.getFlavor().count('other')):
                index+=1
                videos[t.getIdentifier()] = index


        areas = self.create_drawing_areas(videos)
        
        self.seek_bar.set_value(0)
        if self.player:
            self.player.quit()
                  
        self.player = Player(tracks, areas)
        self.change_state(GC_READY)

        self.statusbar.SetVideo(None, self.mediapackage.title)
        self.statusbar.SetPresenter(None, self.mediapackage.getCreators())
        #self.dispatcher.emit

    def play_from_list(self,package):
        """Takes a MP from the listing area and plays it"""
        if self.status == GC_PAUSE:
            self.on_stop_clicked()
            self.statusbar.ClearTimer()            

        self.ready_id = self.dispatcher.connect('player-ready',self.on_player_ready)     
        self.init_player(None, package)          

    def on_player_ready(self, origin):
        """Auto-starts the player once ready"""
        self.dispatcher.disconnect(self.ready_id)
        self.init_timer()
        return True
        

#------------------------- PLAYER ACTIONS ------------------------

    def on_play_clicked(self,button):
        """Starts the reproduction"""
        self.player.play()
        self.init_timer()
        return True

    def init_timer(self):
        """Starts the thread handling the timer for visualiztion and seeking feature"""
        self.change_state(GC_PLAY)
        self.clock=self.player.get_clock()
        self.timer_thread = threading.Thread(target=self.timer_launch_thread)
        self.thread_id = 1
        self.timer_thread.daemon = True
        self.timer_thread.start()
        
    def on_pause_clicked(self, button=None):
        """Pauses the reproduction"""
        self.player.pause()
        self.change_state(GC_PAUSE)
        return True

    def on_stop_clicked(self, button=None):
        """Stops the reproduction and send the seek bar to the start"""
        self.thread_id = None
        self.player.stop()
        self.seek_bar.set_value(0)
        self.statusbar.SetTimer2(0,self.duration)
        self.change_state(GC_STOP)
        return True

    def on_quit_clicked(self,button):
        """Stops the preview and close the player"""
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
        """Stop the player when focus is lost"""
        self.player.pause()
        self.change_state(GC_STOP)

    def on_seek(self,button,scroll_type,new_value):
        """Move to the new position"""
        if new_value>100:
            new_value=100;
        temp=new_value*self.duration*gst.SECOND/100 # FIXME get_duration propertly

        if scroll_type == gtk.SCROLL_JUMP and not self.correct:
            self.seeking = True
            if self.player.is_playing():
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
        """Changes the player value"""
        new_value = 120 if new_value > 120 else 0 if new_value < 0 else new_value
        self.player.set_volume(new_value/100.0)

    def on_volume2(self, button, new_value):
        self.player.set_volume(new_value*2.0)

    def create_drawing_areas(self, source): # TODO refactorize, REC
        """Creates the preview areas depending on the video tracks of a mediapackage"""
        main = self.main_area

        for child in main.get_children():
            main.remove(child)
            child.destroy()        
        areas = None
        areas = dict()
        for key in source.keys():
            new_area = gtk.DrawingArea()
            new_area.set_name("playerarea "+str(key))
            areas[key]=new_area
            areas[key].modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
            main.pack_start(new_area,True,True,3)#TODO editable padding=3

        for child in main.get_children():
            child.show()
         
        return areas
        

#------------------------- PACKAGE ACTIONS ------------------------

    def on_edit_meta(self,button):
        """Pop ups the Medatada Editor for the current Mediapackage"""
        key = self.mediapackage.identifier
        self.edit(key)
        self.statusbar.SetVideo(None, self.mediapackage.title)
        self.statusbar.SetPresenter(None, self.mediapackage.getCreators())
        return True

    def on_zip(self,button):
        """Performs a zip operation over a MP"""
        key = self.mediapackage.identifier
        return self.zip(key)

    def on_question(self,button):
        """Pops up a dialog with the available operations"""
        package = self.mediapackage
        self.ingest_question(package)      

    def on_delete(self, button):
        """ Pops up a dialog.
        If response is positive the mediapackage is deleted and the focus goes to the previous area"""
        key = self.mediapackage.identifier
        response=self.delete(key)		
        if response:
            self.thread_id = None
            self.player.stop()
            self.statusbar.SetVideo(None, "")
            self.statusbar.SetPresenter(None, "")
            self.statusbar.ClearTimer()
            self.change_state(GC_INIT)
            self.mediapackage = None
            self.dispatcher.emit("change-mode", 1)
            
        return True
    
#-------------------------- UI ACTIONS -----------------------------

    def timer_launch_thread(self):
        """Thread handling the timer, provides base time for seeking"""
        thread_id= self.thread_id
        self.initial_time=self.clock.get_time()
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

    def resize(self):
        """Adapts GUI elements to the screen size"""
        size = context.get_mainwindow().get_size()
        
        buttonlist = ["playbutton", "pausebutton", "stopbutton"]
        secondarylist = ["editbutton", "ingestbutton", "deletebutton"]
        self.do_resize(buttonlist, secondarylist)
        vubox = self.gui.get_object("vubox")
        calign = self.gui.get_object("c_align")

        k = self.proportion
        vubox.set_padding(0,int(k*10),int(k*20),int(k*40))
        calign.set_padding(int(k*20),int(k*10),0,0)
  
        self.statusbar.resize(size)
        self.audiobar.resize(size)
        return True

    def event_change_mode(self, orig, old_state, new_state):
        """Pause a recording in the event of a change of mode"""
        if old_state == 2 and self.status == GC_PLAY:
            self.on_pause_clicked()        

    def change_state_bypass(self,origin,state):
        """To handles change state through signal"""
        self.change_state(state)
        return True

    def change_state(self,state):
        """Activates or deactivates the buttons depending on the new state"""
        play=self.gui.get_object("playbutton")
        pause=self.gui.get_object("pausebutton")
        stop=self.gui.get_object("stopbutton")
        editb=self.gui.get_object("editbutton")       
        deleteb=self.gui.get_object("deletebutton")       

        self.previous,self.status = self.status,state

        if state==GC_INIT:
            play.set_sensitive(False)
            pause.set_sensitive(False)
            stop.set_sensitive(False)
            editb.set_sensitive(False)
            deleteb.set_sensitive(False)

        if state==GC_READY:
            play.set_sensitive(True)
            pause.set_sensitive(False)
            stop.set_sensitive(False)
            editb.set_sensitive(True)
            deleteb.set_sensitive(True)

        if state==GC_PLAY:
            play.set_sensitive(False)
            pause.set_sensitive(True)
            stop.set_sensitive(True)

        if state==GC_PAUSE:
            play.set_sensitive(True)
            pause.set_sensitive(False)
            stop.set_sensitive(True)
            
        if state==GC_STOP:
            play.set_sensitive(True)
            pause.set_sensitive(False)
            stop.set_sensitive(False)

        if state==GC_BLOCKED:
            play.set_sensitive(False)
            pause.set_sensitive(False)
            stop.set_sensitive(False)

    def close(self, signal):
        """Close player UI, stopping threads and reproduction"""
        self.thread_id=None
        if self.status in [GC_PLAY, GC_PAUSE]:
            self.player.quit()
        return True        

gobject.type_register(PlayerClassUI)
