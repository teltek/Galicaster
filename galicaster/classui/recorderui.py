# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/classui/recorderui
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
import gst
import gtk
import time
import datetime
import logging
from threading import Thread as thread
import pango

from galicaster.mediapackage import mediapackage
from galicaster.recorder import Recorder
from galicaster.classui.metadata import MetadataClass as Metadata
from galicaster.core import context
from galicaster.classui.statusbar import StatusBarClass
from galicaster.classui.audiobar import AudioBarClass
from galicaster.classui.events import EventManager
from galicaster.classui import message
from galicaster.classui import get_ui_path, get_image_path

gtk.gdk.threads_init()
log = logging.getLogger()


#ESTADOS
GC_EXIT = -1
GC_INIT = 0
GC_READY = 1
GC_PREVIEW = 2
GC_PRE2 = 8 #Waiting
GC_RECORDING = 3
GC_REC2 = 4
GC_PAUSED = 5
GC_STOP = 6
GC_BLOCKED = 7


STATUS = [  ["Initialization","#F7F6F6"],
            ["Ready","#F7F6F6"],
            ["Preview","#F7F6F6"],
            ["Recording","#FF0000"],
            ["Recording","#F7F6F6"],
            ["Paused","#F7F6F6"],
            ["Stopped","#F7F6F6"],
            ["Blocked","#F7F6F6"],
            ["Waiting","#F7F6F6"],
            ]


TIME_BLINK_START = 20
TIME_BLINK_STOP = 20
TIME_RED_START = 50
TIME_RED_STOP = 50
TIME_UPCOMING = 60


class RecorderClassUI(gtk.Box):
    """
    Graphic User Interface for Record alone
    """

    __gtype_name__ = 'RecorderClass'

    def __init__(self, package=None): 
  
        log.info("Creating Recording Area")
        gtk.Box.__init__(self)
	builder = gtk.Builder()
        builder.add_from_file(get_ui_path('recorder.glade'))
       
        self.repo = context.get_repository()
        self.dispatcher = context.get_dispatcher()
        self.current_mediapackage = None
        self.current = None
        self.next = None
        self.restarting = False
        self.normal_style = None
        self.font = None
        self.scheduled_recording = False
        self.focus_is_active = False

        # BUILD
        self.recorderui = builder.get_object("recorderbox")
        self.area1 = builder.get_object("videoarea1")
        self.area2 = builder.get_object("videoarea2")
        self.area1.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        self.area2.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))

        self.vubox = builder.get_object("vubox")
        self.gui = builder

        # BIG STATUS
        big_status = builder.get_object("bg_status")
        self.view = self.set_status_view()
        big_status.add(self.view)

        # STATUS BAR
        self.statusbar=StatusBarClass()
        self.dispatcher.connect("update-rec-status", self.statusbar.SetStatus)
        self.dispatcher.connect("update-video", self.statusbar.SetVideo)
        
        self.statusbar.SetTimer(0)

        # VUMETER
        self.audiobar=AudioBarClass()

        # UI
        self.vubox.add(self.audiobar.bar)
        self.pack_start(self.recorderui,True,True,0)

        # Event Manager
        self.dispatcher.connect("start-before", self.on_start_before)
        self.dispatcher.connect("restart-preview", self.on_restart_preview)
        self.dispatcher.connect("galicaster-status", self.event_change_mode)
        self.dispatcher.connect("update-rec-vumeter", self.audiobar.SetVumeter)
        self.dispatcher.connect("galicaster-notify-quit", self.close)

        # STATES
        self.status = GC_INIT
        self.previous = None
        self.change_state(GC_INIT)

        # PERMISSIONS
        self.conf = context.get_conf()
        self.allow_pause = self.conf.get_permission("pause")
        self.allow_start = self.conf.get_permission("start")
        self.allow_stop = self.conf.get_permission("stop")
        self.allow_manual = self.conf.get_permission("manual")
        self.allow_overlap = self.conf.get_permission("overlap")
     
        # OTHER
        builder.connect_signals(self)

        self.change_state(GC_READY)

        self.on_start()

        # SCHEDULER FEEDBACK
        self.scheduler_thread_id = 1
        self.clock_thread_id = 1
        self.start_thread_id = None

        self.scheduler_thread = thread(target=self.scheduler_launch_thread)
        self.clock_thread = thread(target=self.clock_launch_thread)
        self.scheduler_thread.daemon = True
        self.clock_thread.daemon = True
        self.scheduler_thread.start()
        self.clock_thread.start() 


    def select_devices(self):
        log.info("Setting Devices")
        self.mediapackage = self.repo.get_new_mediapackage()
        self.mediapackage.setTitle("Recording started at "+ datetime.datetime.now().replace(microsecond = 0).isoformat())
        bins = self.conf.getBins(self.repo.get_attach_path())
        areas = { self.conf.get("screen", "left") : self.area1, 
                  self.conf.get("screen","right") : self.area2 }             

        self.record = Recorder(bins, areas) 
        self.record.mute_preview(not self.focus_is_active)


#------------------------- PLAYER ACTIONS ------------------------


    def on_start(self, button=None):
        """Preview at start"""
        log.info("Starting Preview")
        self.conf.reload()
        self.select_devices()
        self.record.preview()
        self.change_state(GC_PREVIEW)
        return True


    def on_restart_preview(self, button=None, element=None): 
        """Restarting preview, commanded by record""" 
        log.info("Restarting Preview")
        self.conf.reload()
        self.select_devices()
        self.record.preview()
        self.change_state(GC_PREVIEW)
        self.restarting = False
        return True


    def on_rec(self,button=None): 
        """Manual Recording """
        log.info("Recording")
        self.dispatcher.emit("starting-record")
        self.record.record()
        self.mediapackage.status=mediapackage.RECORDING
        self.mediapackage.setDate(datetime.datetime.utcnow().replace(microsecond = 0))
        self.clock=self.record.get_clock()
        self.timer_thread_id = 1
        self.timer_thread = thread(target=self.timer_launch_thread) #TODO timer thread
        self.timer_thread.daemon = True
        self.timer_thread.start()
        self.change_state(GC_RECORDING)
        return True  


    def on_start_before(self, origin, key):
        """ Start a recording before its schedule """
        log.info("Start recording before schedule")
        self.mediapackage = self.repo.get(key)
        self.mediapackage.manual = True      
        self.on_rec()
        return True            


    def on_pause(self,button):
        if self.status == GC_PAUSED:
            log.debug("Resuming Recording")
            self.change_state(GC_RECORDING)
            self.record.resume()
        elif self.status == GC_RECORDING:
            log.debug("Pausing Recording")
            self.change_state(GC_PAUSED)
            self.record.pause()
            gui = gtk.Builder()
            gui.add_from_file(get_ui_path("paused.glade"))
            dialog = gui.get_object("dialog") 
            self.pause_dialog=dialog
            image = gui.get_object("image") 
            button = gui.get_object("button") 
            dialog.set_transient_for(self.get_toplevel())
    
            response = dialog.run()
            if response == 1:
                self.on_pause(None)
                #log.debug("Resuming Recording")
                #self.change_state(GC_RECORDING)
                #self.record.resume()
            dialog.destroy()                

            
    def on_stop(self,button):
        text = {"title" : "Stop",
              "main" : "Are you sure you want to\nstop the recording?",
			}
        buttons = ( "Stop", gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
        window=gtk.gdk.get_default_root_window()
        size = [ window.get_screen().get_width(), window.get_screen().get_height() ]
        warning = message.PopUp(message.WARNING, text, size, 
					self.get_toplevel(), buttons)

        if warning.response in message.POSITIVE:
            if self.scheduled_recording:
                self.current_mediapackage = None
                self.current = None
                self.scheduled_recording = False
            self.close_recording() 


    def close_recording(self):
        """
        Set the final data on the mediapackage, stop the record and restart the preview
        """
        close_duration = (self.clock.get_time()-self.initial_time)*1000/gst.SECOND  
        self.record.stop_record_and_restart_preview()
        self.change_state(GC_STOP)

        if self.conf.get('ingest', 'active') == "True" and self.conf.get('ingest', 'default') == "True":
            self.mediapackage.status = mediapackage.PENDING
            log.info("Stop and Ingest Recording")
        else:
            self.mediapackage.status = mediapackage.RECORDED
            log.info("Stop Recording")

        self.repo.add_after_rec(self.mediapackage, self.record.bins_desc, close_duration)
        self.timer_thread_id = None


    def on_scheduled_start(self, source, identifier):
        log.info("Scheduled Start")
        self.conf.reload()
        self.current_mediapackage = identifier
        self.scheduled_recording = True
        a=thread(target=self.start_thread, args=(identifier,))
        a.daemon = False
        a.start()


    def start_thread(self,identifier):
        self.start_thread_id = 1

        if self.status == GC_PREVIEW: # Record directly
            self.mediapackage = self.repo.get(self.current_mediapackage)
            self.on_rec() 
        
        elif self.status in [ GC_RECORDING, GC_PAUSED ] :

            if self.allow_overlap:
                pass
                # TODO: dont stop and extend recording until the end of the new interval
                # In case of stop, restart with the overlapped job

            else: # Stop current recording, wait until prewiew restarted and record
                self.restarting = True
                self.close_recording()                
                while self.restarting:
                    time.sleep(0.1) 
                    if self.start_thread_id == None:
                        return
                self.mediapackage = self.repo.get(self.current_mediapackage)   
                self.on_rec()       
                      
        elif self.status == GC_INIT:  # Start Preview and Record
            self.on_start()
            while self.record.get_status() != gst.STATE_PLAYING:
                time.sleep(0.2)
                if self.start_thread_id == None:
                    return
            self.mediapackage = self.repo.get(self.current_mediapackage)
            self.on_rec()

        title = self.repo.get(identifier).title
        self.dispatcher.emit("update-video", title)
        
        return None

    def on_scheduled_stop(self,source,identifier):
        log.info("Scheduled Stop")
        self.current_mediapackage = None
        self.current = None
        self.close_recording()
        self.scheduled_recording = False


    def reload_state_and_permissions(self):
        """
        Force a state review in case permissions had changed
        """
        self.conf.reload()
        self.allow_pause = self.conf.get_permission("pause")
        self.allow_start = self.conf.get_permission("start")
        self.allow_stop = self.conf.get_permission("stop")
        self.allow_manual = self.conf.get_permission("manual")
        self.allow_overlap = self.conf.get_permission("overlap")
        self.change_state(self.status)

    def reload_state(self):
        """
        Force a state review in case situation had changed
        """
        self.change_state(self.status)



    def on_help(self,button):
        log.info("Help requested")   

        text = {"title" : "Help",
                "main" : " Visit galicaster.teltek.es",
                "text" : " ...or contact us on our community list."
			}
        # buttons = (gtk.STOCK_OK, gtk.RESPONSE_OK)
        buttons = None
        window=gtk.gdk.get_default_root_window()
        size = [ window.get_screen().get_width(), window.get_screen().get_height() ]
        warning = message.PopUp(message.INFO, text, size, 
                                self.get_toplevel(), buttons)

    def restart(self): # FIXME name confusing cause on_restart_preview
        """
        Called by Core, if in preview, reload configuration and restart preview
        """
        if self.status == GC_STOP:
            self.on_start()
            
        elif self.status == GC_PREVIEW:
            self.change_state(GC_STOP)
            self.record.just_restart_preview()
        else:
            log.warning("Restart preview called while Recording")

        return True
        

    def on_quit(self,button=None): 
        gui = gtk.Builder()
        gui.add_from_file(get_ui_path("quit.glade"))
        dialog = gui.get_object("dialog")
        dialog.set_transient_for(self.get_toplevel())

        response =dialog.run()
        if response == gtk.RESPONSE_OK:   
            dialog.destroy()
            if self.status >= GC_PREVIEW:
                self.record.stop_preview()

            self.change_state(GC_EXIT)
            log.info("Closing Clock and Scheduler")

            self.scheduler_thread_id = None
            self.clock_thread = None 
            # threads closed for sure            
            self.emit("delete_event", gtk.gdk.Event(gtk.gdk.DELETE))    
        else:
            dialog.destroy()            
        return True

#------------------------- THREADS ------------------------------
 

    def timer_launch_thread(self):
        """
        Based on: http://pygstdocs.berlios.de/pygst-tutorial/seeking.html
        """
        thread_id= self.timer_thread_id
        self.initial_time=self.clock.get_time()
        self.initial_datetime=datetime.datetime.utcnow().replace(microsecond = 0)
        gtk.gdk.threads_enter()
        self.statusbar.SetTimer(0)
        gtk.gdk.threads_leave()
              
        while thread_id == self.timer_thread_id:            
        #while True:
            actual_time=self.clock.get_time()               
            timer=(actual_time-self.initial_time)/gst.SECOND
            if thread_id==self.timer_thread_id:
                gtk.gdk.threads_enter()
                self.statusbar.SetTimer(timer)
                
                gtk.gdk.threads_leave()
            time.sleep(0.2)          
        return True

    def scheduler_launch_thread(self):
        """
        Based on: http://pygstdocs.berlios.de/pygst-tutorial/seeking.html
        """
        thread_id= self.scheduler_thread_id
        event_type = self.gui.get_object("nextlabel")
        title = self.gui.get_object("titlelabel")
        status = self.gui.get_object("eventlabel")
        frame = self.gui.get_object("framebox")
        frame2 = self.gui.get_object("framebox2")
        frame.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_from_hsv(0,0,0.73))
        frame2.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_from_hsv(0,0,0.73))


        self.check_schedule()
        parpadeo = True
        changed = False
        signalized = False

        if self.font == None:
            anchura = self.get_toplevel().get_screen().get_width()
            if anchura not in [1024,1280,1920]:
                anchura = 1920            
            k1 = anchura / 1920.0
            self.font = pango.FontDescription("bold "+str(k1*42))       
        
        bold = pango.AttrWeight(700, 0, -1)
        red = pango.AttrForeground(65535, 0, 0, 0, -1)
        black = pango.AttrForeground(17753, 17753, 17753, 0, -1)
        font=pango.AttrFontDesc(self.font, 0, -1)

        attr_red = pango.AttrList()
        attr_black = pango.AttrList()

        attr_red.insert(red)
        attr_red.insert(font)
        attr_red.insert(bold)

        attr_black.insert(black)
        attr_black.insert(font)
        attr_black.insert(bold)

        status.set_property("attributes",attr_black)
        one_second=datetime.timedelta(seconds=1)
        while thread_id == self.scheduler_thread_id:  
            if self.current:
                start = self.current.getLocalDate()
                duration = self.current.getDuration() / 1000
                end = start + datetime.timedelta(seconds=duration)
                dif = end - datetime.datetime.now()
                dif2 = datetime.datetime.now() - start
                if dif < datetime.timedelta(0,0): # Checking for malfuntions
                    self.current = None
                    self.current_mediapackage = None
                    status.set_text("")
                else:
                    status.set_text("Stopping on "+self.time_readable(dif+one_second))
                    if event_type.get_text() != "Current REC:":
                        event_type.set_text("Current REC:") 
                    if title.get_text() != self.current.title:
                        title.set_text(self.current.title)
                    if dif < datetime.timedelta(0,TIME_RED_STOP):
                        if not changed:
                            status.set_property("attributes",attr_red)
                            changed = True
                    elif changed:
                        status.set_property("attributes",attr_black)
                        changed = False
                    if dif < datetime.timedelta(0,TIME_BLINK_STOP):
                        parpadeo = False if parpadeo else True
                # Timer(diff,self.check_schedule)

            elif self.next:
                start = self.next.getLocalDate()
                dif = start - datetime.datetime.now()
                if event_type.get_text != "Next REC:":
                    event_type.set_text("Next REC:")
                if title.get_text() != self.next.title:
                    title.set_text(self.next.title)
                status.set_text("Starting on " + self.time_readable(dif))

                if dif < datetime.timedelta(0,TIME_RED_START):
                    if not changed:
                        status.set_property("attributes",attr_red)
                        changed = True
                elif changed:
                    status.set_property("attributes",attr_black)
                    changed = False

                if dif < datetime.timedelta(0,TIME_UPCOMING):
                    if not signalized:
                        self.dispatcher.emit("upcoming-recording")
                        signalized = True
                elif signalized:
                    signalized = True                   

                if dif < datetime.timedelta(0,TIME_BLINK_START):
                    if parpadeo:
                        status.set_text("")
                        parpadeo =  False
                    else:
                        parpadeo = True
                # Timer(60,self.check_schedule)

            else: # Not current or pending recordings
                if event_type.get_text():                
                    event_type.set_text("")
                if status.get_text():
                    status.set_text("")
                if title.get_text() != "No upcoming events":
                    title.set_text("No upcoming events")
                
            time.sleep(0.5)
            self.check_schedule()            
        return True


    def clock_launch_thread(self):
        """
        Based on: http://pygstdocs.berlios.de/pygst-tutorial/seeking.html
        """
        thread_id= self.clock_thread_id
        clock = self.gui.get_object("local_clock")

        while thread_id == self.clock_thread_id:            
            if thread_id==self.clock_thread_id:
                clocktime = datetime.datetime.now().time().strftime("%H:%M")
                clock.set_label(clocktime)           
            time.sleep(1)          
        return True


    def time_readable(self, timedif):
        """
        Take a timedelta and return it formatted
        """       
           
        if timedif < datetime.timedelta(0,300): # 5 minutes tops
            formatted = "{minutes:02d}:{seconds:02d}".format( 
                            minutes = timedif.seconds // 60, 
                            seconds = timedif.seconds % 60 )
        elif timedif < datetime.timedelta(1,0): # 24 hours
            formatted = "{hours:02d}:{minutes:02d}:{seconds:02d}".format(
                hours =  timedif.days*24 + timedif.seconds // 3600, 
                minutes = timedif.seconds % 3600 // 60 ,
                seconds = timedif.seconds % 60 
                )
        else: # days
            today = datetime.datetime.now()
            then = today + timedif
            dif = then.date() - today.date()
            formatted = "{days} day{plural}".format(
                days =  dif.days,
                plural = 's' if dif.days >1 else '')

        return formatted
    
   
    def check_schedule(self):
        previous1 = self. current
        previous2 = self.next
        if self.current_mediapackage == None:
            self.current = None
        else:
            self.current = self.repo.get(self.current_mediapackage)
        previous2 = self.next
        self.next = self.repo.get_next_mediapackage() # could be None
        if previous2 != self.next:
            self.reload_state()

#------------------------- POPUP ACTIONS ------------------------

    def on_edit_meta(self,button):
        self.change_state(GC_BLOCKED)
        if not self.scheduled_recording:
            meta=Metadata(self.mediapackage, parent=self)
            self.statusbar.SetVideo(None,self.mediapackage.metadata_episode['title'])
            self.statusbar.SetPresenter(None,self.mediapackage.creators)
        self.change_state(self.previous)  
        return True 

    def show_next(self,button=None,tipe = None):   
        eventm=EventManager(parent=self)
        return True

    def show_about(self,button=None,tipe = None):
        gui = gtk.Builder()
        gui.add_from_file(get_ui_path('about.glade'))
        dialog = gui.get_object("dialog")
        dialog.set_transient_for(self.get_toplevel())
    
        response = dialog.run()
        if response:
            dialog.destroy()
        else:
            dialog.destroy()
        return True

    
#-------------------------- UI ACTIONS -----------------------------

    def event_change_mode(self, orig, old_state, new_state):
        if new_state == 0: 
            self.focus_is_active = True
            self.record.mute_preview(False)

        if old_state == 0:
            self.focus_is_active = False
            self.record.mute_preview(True)


    def change_mode(self, button):
        self.dispatcher.emit("change-mode", 3) # FIXME use constant


    def set_status_view(self):
        l = gtk.ListStore(str,str)
        for i in STATUS:
            l.append(i)

        v = gtk.CellView()
        v.set_model(l)

        r = gtk.CellRendererText()
        r.set_alignment(0.5,0.5)

        window=gtk.gdk.get_default_root_window()
        size = [ window.get_screen().get_width(), window.get_screen().get_height() ]
        k1 = size[0] / 1920.0
        k2 = size[1] / 1080.0
        font = pango.FontDescription("bold "+ str(int(k2*48)))
        r.set_property('font-desc', font)
        r.set_padding(int(k1*100),0)
        self.renderer = r
        v.pack_start(r,True)
        v.add_attribute(r, "text", 0)
        v.add_attribute(r, "background", 1)
        v.set_displayed_row(0)
        return v


    def resize(self,size):
        altura = size[1]
        anchura = size[0]
        
        k1 = anchura / 1920.0 # we assume 16:9
        k2 = altura / 1080.0
        self.proportion = k1

        #Recorder
        clock = self.gui.get_object("local_clock")#4
        logo = self.gui.get_object("classlogo")       
        next = self.gui.get_object("nextlabel")#2.8
        more = self.gui.get_object("morelabel")#3.5
        title = self.gui.get_object("titlelabel")#2.5
        eventl = self.gui.get_object("eventlabel")#3.5
        align2r = self.gui.get_object("top_align")
        pbox = self.gui.get_object("prebox")
        
        def relabel(label,size,bold):           
            if bold:
                modification = "bold "+str(size)
            else:
                modification = str(size)
            label.modify_font(pango.FontDescription(modification))


        def relabel_updating_font(label,size,bold):           
            if bold:
                modification = "bold "+str(size)
            else:
                modification = str(size)
            self.font = pango.FontDescription(modification)     
            label.modify_font(self.font)
            
        relabel(clock,k1*25,False)
        font = pango.FontDescription("bold "+str(int(k2*48)))
        self.renderer.set_property('font-desc', font)
        self.renderer.set_padding(int(k1*100),0)
        image=gtk.gdk.pixbuf_new_from_file(get_image_path("logo"+str(anchura)+".png"))
        logo.set_from_pixbuf(image)
        relabel(next,k1*28,True)
        relabel(more,k1*25,True)
        relabel(title,k1*33,True)
        relabel_updating_font(eventl,k1*28,True)

        for name  in ["recbutton","pausebutton","stopbutton","helpbutton", ]:
            button = self.gui.get_object(name)
            button.set_property("width-request", int(k1*100) )
            button.set_property("height-request", int(k1*100) )

            image = button.get_children()
            if type(image[0]) == gtk.Image:
                image[0].set_pixel_size(int(k1*80))   
            elif type(image[0]) == gtk.VBox:
                for element in image[0].get_children():
                    if type(element) == gtk.Image:
                        element.set_pixel_size(int(k1*46))
            else:
                relabel(image[0],k1*28,False)

        for name  in ["previousbutton"]:
            button = self.gui.get_object(name)
            button.set_property("width-request", int(k1*70) )
            button.set_property("height-request", int(k1*70) )

            image = button.get_children()
            if type(image[0]) == gtk.Image:
                image[0].set_pixel_size(int(k1*56))  
                image[0].set_padding(int(k1*50),0)


        button = self.gui.get_object("top_align")
        button.set_padding(int(k1*20),int(k1*40),int(k1*50),int(k1*50))
        button = self.gui.get_object("control_align")
        button.set_padding(int(k1*10),int(k1*30),int(k1*50),int(k1*50))
        button = self.gui.get_object("vubox")
        button.set_padding(int(k1*20),int(k1*10),int(k1*40),int(k1*40))         
        align2r.set_padding(int(k1*10),int(k1*30),int(k1*120),int(k1*120))
        pbox.set_property("width-request", int(k1*225) )
        return True

        
    def change_state(self, state):
        record = self.gui.get_object("recbutton")
        pause = self.gui.get_object("pausebutton")
        stop = self.gui.get_object("stopbutton")
        helpb = self.gui.get_object("helpbutton")
        editb = self.gui.get_object("editbutton")
        prevb = self.gui.get_object("previousbutton")
  
        if state != self.status:
            self.previous,self.status = self.status,state

        if state != GC_RECORDING:
            if self.normal_style != None:
                bgstatus.set_style(self.normal_style)

        if state == GC_INIT:
            record.set_sensitive(False)
            pause.set_sensitive(False)
            stop.set_sensitive(False)
            helpb.set_sensitive(True)
            prevb.set_sensitive(True)
            editb.set_sensitive(False)
            self.dispatcher.emit("update-rec-status", "Initialization")            

        elif state == GC_PREVIEW:    
            record.set_sensitive( (self.allow_start or self.allow_manual) )
            pause.set_sensitive(False)
            pause.set_active(False)
            stop.set_sensitive(False)
            helpb.set_sensitive(True)
            prevb.set_sensitive(True)
            editb.set_sensitive(False)
            if self.next == None:
                self.dispatcher.emit("update-rec-status", "Idle")            
            else:
                self.dispatcher.emit("update-rec-status", "Waiting")     

        elif state == GC_RECORDING:
            record.set_sensitive(False)
            pause.set_sensitive(self.allow_pause and self.record.is_pausable()) 
            stop.set_sensitive( (self.allow_stop or self.allow_manual) )
            helpb.set_sensitive(True)
            prevb.set_sensitive(False)
            editb.set_sensitive(True and not self.scheduled_recording)    
            self.dispatcher.emit("update-rec-status", "  Recording  ")
       
        elif state == GC_PAUSED:
            record.set_sensitive(False)
            pause.set_sensitive(False) 
            stop.set_sensitive(False)
            prevb.set_sensitive(False)
            helpb.set_sensitive(False)
            editb.set_sensitive(True and not self.scheduled_recording)
  
            self.dispatcher.emit("update-rec-status", "Paused")
            
        elif state == GC_STOP:
            if self.previous == GC_PAUSED:
                self.pause_dialog.destroy()
            record.set_sensitive(False)
            pause.set_sensitive(False)
            stop.set_sensitive(False)
            helpb.set_sensitive(True)
            prevb.set_sensitive(True)
            editb.set_sensitive(False)
            self.dispatcher.emit("update-rec-status", "Stopped")            

        elif state == GC_BLOCKED: # FIXME not necessary
            record.set_sensitive(False)
            pause.set_sensitive(False)
            stop.set_sensitive(False)
            helpb.set_sensitive(False)   
            prevb.set_sensitive(False)
            editb.set_sensitive(False)

        if self.next == None and state == GC_PREVIEW:
            self.view.set_displayed_row(GC_PRE2)
        else:
            self.view.set_displayed_row(state)


    def block(self):
        prev = self.gui.get_object("prebox")
        prev.set_child_visible(False)
        self.focus_is_active = True
        self.event_change_mode(None, 3, 0)

        # Show Help or Edit_meta
        helpbutton = self.gui.get_object("helpbutton")
        helpbutton.set_visible(True)
        editbutton = self.gui.get_object("editbutton")
        editbutton.set_visible(False)

 
    def close(self, signal):
        if self.status in [GC_RECORDING]:
            self.close_recording() 
        self.scheduler_thread_id = None
        self.clock_thread_id = None
        self.start_thread_id = None
        if self.status in [GC_PREVIEW]:
            self.record.stop_preview()        
        return True        


gobject.type_register(RecorderClassUI)
