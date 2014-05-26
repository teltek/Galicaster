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
"""
Recording Area GUI
"""

import os
import gobject
import gst
import gtk
import gtk.glade
import pango
import re
import time
import datetime
from threading import Thread as thread

from galicaster.core import context
from galicaster.mediapackage import mediapackage
from galicaster.recorder import Recorder

from galicaster.utils import series
from galicaster.utils import readable
from galicaster.classui.metadata import MetadataClass as Metadata
from galicaster.classui.audiobar import Vumeter
from galicaster.classui.events import EventManager
from galicaster.classui.about import GCAboutDialog

from galicaster.classui import message
from galicaster.classui import get_ui_path, get_image_path
from galicaster.utils.resize import relabel, relabel_updating_font

from galicaster.utils.i18n import _

gtk.gdk.threads_init()

logger = context.get_logger()

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
GC_ERROR = 9

# No-op function for i18n
def N_(string): return string

STATUS = [  [N_("Initialization"),"#F7F6F6"],
            [N_("Ready"),"#F7F6F6"],
            [N_("Preview"),"#F7F6F6"],
            [N_("Recording"),"#FF0000"],
            [N_("Recording"),"#F7F6F6"],
            [N_("Paused"),"#F7F6F6"],
            [N_("Stopped"),"#F7F6F6"],
            [N_("Blocked"),"#F7F6F6"],
            [N_("Waiting"),"#F7F6F6"],
            [N_("Error"),"#FF0000"],
            ]


TIME_BLINK_START = 20
TIME_BLINK_STOP = 20
TIME_RED_START = 50
TIME_RED_STOP = 50
TIME_UPCOMING = 60

NEXT_TEXT = _("Upcoming")
CURRENT_TEXT = _("Current")


class RecorderClassUI(gtk.Box):
    """
    Graphic User Interface for Record alone
    """

    __gtype_name__ = 'RecorderClass'

    def __init__(self, package=None): 
  
        logger.info("Creating Recording Area")
        gtk.Box.__init__(self)
	builder = gtk.Builder()
        builder.add_from_file(get_ui_path('recorder.glade'))
       
        self.repo = context.get_repository()
        self.dispatcher = context.get_dispatcher()
        self.worker = context.get_worker()
        self.recorder = None
        self.current_mediapackage = None
        self.current = None
        self.next = None
        self.start_recording = False
        self.font = None
        self.scheduled_recording = False
        self.focus_is_active = False
        self.net_activity = None

        self.error_id = None
        self.error_text = None
        self.error_dialog = None
        self.ok_to_show = False
        self.swap_active = None
        self.swap = False

        # BUILD
        self.recorderui = builder.get_object("recorderbox")
        self.main_area = builder.get_object("videobox")
        self.vubox = builder.get_object("vubox")
        self.gui = builder

        # STATUS
        big_status = builder.get_object("bg_status")
        self.view = self.set_status_view()
        big_status.add(self.view)
        self.dispatcher.connect("galicaster-init", self.check_status_area)
        self.dispatcher.connect("galicaster-init", self.check_net)
        self.dispatcher.connect("restart-preview", self.check_status_area)
        self.dispatcher.connect("net-up", self.check_net, True)        
        self.dispatcher.connect("net-down", self.check_net, False)        

        # VUMETER
        self.audiobar=Vumeter()

        # UI
        self.vubox.add(self.audiobar)
        self.pack_start(self.recorderui,True,True,0)

        # Event Manager       
        self.dispatcher.connect("start-record", self.on_scheduled_start)
        self.dispatcher.connect("stop-record", self.on_stop)
        self.dispatcher.connect("start-before", self.on_start_before)
        self.dispatcher.connect("restart-preview", self.on_restart_preview)
        self.dispatcher.connect("update-rec-vumeter", self.audiobar.SetVumeter)
        self.dispatcher.connect("galicaster-status", self.event_change_mode)
        self.dispatcher.connect("galicaster-notify-quit", self.close)

        nb=builder.get_object("data_panel")
        pages = nb.get_n_pages()        
        for index in range(pages):
            page=nb.get_nth_page(index)
            nb.set_tab_label_packing(page, True, True,gtk.PACK_START)

        # STATES
        self.status = GC_INIT
        self.previous = None
        self.change_state(GC_INIT)

        self.dispatcher.connect("reload-profile", self.on_recover_from_error)

        # PERMISSIONS
        self.conf = context.get_conf()
        self.allow_pause = self.conf.get_permission("pause")
        self.allow_start = self.conf.get_permission("start")
        self.allow_stop = self.conf.get_permission("stop")
        self.allow_manual = self.conf.get_permission("manual")
        self.allow_overlap = self.conf.get_permission("overlap")
     
        # OTHER
        builder.connect_signals(self)
        self.net_activity = self.conf.get_boolean('ingest', 'active')

        self.change_state(GC_READY)

        self.proportion = 1
        self.on_start()

        # SCHEDULER FEEDBACK
        self.scheduler_thread_id = 1
        self.clock_thread_id = 1

        self.scheduler_thread = thread(target=self.scheduler_launch_thread)
        self.clock_thread = thread(target=self.clock_launch_thread)
        self.scheduler_thread.daemon = True
        self.clock_thread.daemon = True
        self.scheduler_thread.start()
        self.clock_thread.start() 

        # SHOW OR HIDE SWAP BUTTON
        if self.conf.get_boolean('basic', 'swapvideos'):
            self.swap_active = True
        else:
            self.swap_active = False

    # Handle for swap videos button
    def swap_videos(self, button=None):
        if self.swap:
            self.swap = False
        else:
            self.swap = True
        self.dispatcher.emit("reload-profile")
        self.audiobar.mute = False        

    def select_devices(self):
        """Loads the bins and creates the preview areas for the active profile, creating a new mediapacakge."""
        self.configure_profile()
        logger.info("Setting Devices the new way")
        now = datetime.datetime.now().replace(microsecond=0)
        self.mediapackage = mediapackage.Mediapackage(title=_("Recording started at {0}").format(now.isoformat()))

        context.get_state().mp = self.mediapackage.identifier

        if self.ok_to_show:
            self.init_recorder()
        return True



    #  ------------------------- PLAYER ACTIONS ------------------------


    def on_start(self, button=None):
        """Preview at start - Galicaster initialization"""
        logger.info("Starting Preview")
        self.conf.reload()
        self.select_devices()
        return True

    def on_start_button(self, button=None):
        """Triggers bin loading and start preview"""
        self.select_devices()

    def init_recorder(self):
        if self.error_dialog:
            if self.error_id:
                self.dispatcher.disconnect(self.error_id)
                self.error_id = None
            self.error_dialog.dialog_destroy()
            self.error_dialog = None
            self.error_text = None
        self.error_id = self.dispatcher.connect(
            "recorder-error",
            self.handle_pipeline_error)
        self.audiobar.ClearVumeter()
        context.get_state().is_error = False

        current_profile = self.conf.get_current_profile()
        bins = current_profile.tracks
        for objectbin in bins:
            objectbin['path'] = self.repo.get_rectemp_path()

        self.recorder = Recorder(bins) 
        self.recorder.mute_preview(not self.focus_is_active)   
        info = self.recorder.get_display_areas_info()
        if self.swap: 
            info.reverse()
        areas = self.create_drawing_areas(info)
        self.recorder.set_drawing_areas(areas)

        if self.start_recording:
            self.start_recording = False
            ok = self.recorder.preview_and_record()
            self.mediapackage = self.repo.get(self.current_mediapackage)
            # NOTE only call on_rec to update UI. Recorder is already recording.
            self.on_rec()
        else:
            ok = self.recorder.preview()
        if ok :
            if self.mediapackage.manual:
                self.change_state(GC_PREVIEW)
        else:
            logger.error("Restarting Preview Failed")
            context.get_state().is_error = True
            self.change_state(GC_ERROR)
            if self.scheduled_recording:
                self.on_failed_scheduled(self.current_mediapackage)    
            # TODO kill counter in case of error and scheduler

    def go_ahead(self):
        """Continue Recorder init create Record module and start_preview"""
        if not self.ok_to_show:
            self.init_recorder()
        self.ok_to_show = True

    def on_restart_preview(self, button=None, element=None): 
        """Restarting preview, commanded by record""" 
        logger.info("Restarting Preview")

        close_duration = self.recorder.get_recorded_time() / gst.MSECOND

        self.mediapackage.status = mediapackage.RECORDED
        self.mediapackage.properties['origin'] = self.conf.hostname
        self.repo.add_after_rec(self.mediapackage, self.recorder.get_bins_info(), 
                                close_duration, self.mediapackage.manual)
        
        code = 'manual' if self.mediapackage.manual else 'scheduled'
        if self.conf.get_lower('ingest', code) == 'immediately':
            self.worker.ingest(self.mediapackage)
        elif self.conf.get_lower('ingest', code) == 'nightly':
            self.worker.ingest_nightly(self.mediapackage)

        self.conf.reload()
        #self.configure_profile()
        self.select_devices()
        return True

    def configure_profile(self):
        profile = self.conf.get_current_profile()
        context.get_state().profile = profile
        if profile.execute:
            out = os.system(profile.execute)
            logger.info("Executing {0} with out {1}".format(profile.execute, out))
            if out:
                self.dispatcher.emit("recorder-error", "Error executing command configuring profile")


    def on_rec(self,button=None): 
        """Manual Recording """
        logger.info("Recording")
        self.dispatcher.emit("starting-record")
        self.recorder.record()
        self.mediapackage.status=mediapackage.RECORDING
        now = datetime.datetime.utcnow().replace(microsecond=0)
        self.mediapackage.setDate(now)
        self.timer_thread_id = 1
        self.timer_thread = thread(target=self.timer_launch_thread) 
        self.timer_thread.daemon = True
        self.timer_thread.start()
        self.change_state(GC_RECORDING)
        context.get_state().is_recording = True
        return True  


    def on_start_before(self, origin, key):
        """ Start a recording before its schedule or via rest """
        if key:
            logger.info("Start recording before schedule")
            self.mediapackage = self.repo.get(key)
            context.get_state().mp=self.mediapackage.identifier
        else:
            logger.info("Rest triggered recording")
        self.on_rec()
        return True            


    def on_pause(self,button):
        """Pauses or resumes a recording"""
        if self.status == GC_PAUSED:
            self.dispatcher.emit("enable-no-audio")
            logger.debug("Resuming Recording")
            self.change_state(GC_RECORDING)
            self.recorder.resume()
        elif self.status == GC_RECORDING:
            self.dispatcher.emit("disable-no-audio")
            logger.debug("Pausing Recording")
            self.change_state(GC_PAUSED)
            self.recorder.pause()
            gui = gtk.Builder()
            gui.add_from_file(get_ui_path("paused.glade"))
            self.pause_dialog = self.create_pause_dialog(self.get_toplevel())
    
            response = self.pause_dialog.run()
            if response == 1:
                self.on_pause(None)
            self.pause_dialog.destroy()     


    def create_pause_dialog(self, parent):
       
        gui = gtk.Builder()
        gui.add_from_file(get_ui_path("paused.glade"))
        dialog = gui.get_object("dialog") 
        dialog.set_transient_for(parent)
        dialog.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_TOOLBAR)
        dialog.set_modal(True)
        dialog.set_keep_above(False)
        dialog.set_skip_taskbar_hint(True)
        size = context.get_mainwindow().get_size()
        k2 = size[1] / 1080.0
        size= int(k2*150)
        dialog.set_default_size(size,size)
        button = gui.get_object("image")
        pixbuf = gtk.gdk.pixbuf_new_from_file(get_image_path('gc-pause.svg'))
        pixbuf = pixbuf.scale_simple(
            size,
            size,
            gtk.gdk.INTERP_BILINEAR)
        button.set_from_pixbuf(pixbuf)
        return dialog

            
    def on_ask_stop(self,button):
        """Stops preview or recording and closes the Mediapakage"""
        self.dispatcher.emit("disable-no-audio")
        if self.conf.get_boolean("basic", "stopdialog"):
            text = {"title" : _("Recorder"),
                    "main" : _("Are you sure you want to\nstop the recording?"),
            }
            buttons = ( gtk.STOCK_STOP, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
            warning = message.PopUp(message.WARNING, text,
              context.get_mainwindow(), buttons
            )
            self.dispatcher.emit("enable-no-audio")
            if warning.response not in message.POSITIVE:
                return False
            else:
                self.on_stop("UI","current")

    def on_stop(self,source,identifier): 
        """Close recording and clean schedule if neccesary"""
        if self.scheduled_recording:
            self.current_mediapackage = None
            self.current = None
            self.scheduled_recording = False
            logger.info("Scheduled Stop")
        else:
            logger.info("Stop recording")
        self.close_recording()  

    def close_recording(self):
        """Set the final data on the mediapackage, stop the record and restart the preview"""
        # To avoid error messages on stopping pipelines
        if self.error_dialog:
            if self.error_id:
                self.dispatcher.disconnect(self.error_id)
                self.error_id = None
            self.error_dialog.dialog_destroy()
            self.error_dialog = None
            self.error_text = None
        self.recorder.stop_record_and_restart_preview()
        self.change_state(GC_STOP)

        context.get_state().is_recording = False
        self.timer_thread_id = None

    def on_scheduled_start(self, source, identifier):
        """Starts a scheduled recording, replacing the mediapackage in use"""
        logger.info("Scheduled Start")
        self.conf.reload()
        self.current_mediapackage = identifier
        self.scheduled_recording = True

        if self.status == GC_PREVIEW: # Record directly
            self.mediapackage = self.repo.get(self.current_mediapackage)
            self.on_rec() 
        
        elif self.status in [ GC_RECORDING, GC_PAUSED ] :

            if self.allow_overlap:
                pass
                # TODO: dont stop and extend recording until the end of the new interval
                # In case of stop, restart with the overlapped job

            else: # Stop current recording, wait until prewiew restarted and record
                self.start_recording = True
                self.close_recording()                
                      
        elif self.status == GC_INIT:  # Start Preview and Record
            self.on_start_button()
            while self.recorder.get_status() != gst.STATE_PLAYING:
                time.sleep(0.2)
            self.mediapackage = self.repo.get(self.current_mediapackage)
            self.on_rec()

        title = self.repo.get(identifier).title
        self.dispatcher.emit("update-video", title)

    def on_scheduled_stop(self,source,identifier):
        """Updates the mediapackage information after a scheduled recoring."""
        logger.info("Scheduled Stop")
        self.current_mediapackage = None
        self.current = None
        self.close_recording()
        self.scheduled_recording = False

    def on_failed_scheduled(self, identifier):
        """Updates the mediapackage information after a scheduled recoring."""
        #TODO change MP status to failed 
        logger.info("Scheduled {0} failed on error".format(identifier))
        self.current_mediapackage = None
        self.current = None
        self.scheduled_recording = False

    def reload_state_and_permissions(self):
        """Force a state review in case permissions had changed."""
        self.conf.reload()
        self.allow_pause = self.conf.get_permission("pause")
        self.allow_start = self.conf.get_permission("start")
        self.allow_stop = self.conf.get_permission("stop")
        self.allow_manual = self.conf.get_permission("manual")
        self.allow_overlap = self.conf.get_permission("overlap")
        self.change_state(self.status)

    def reload_state(self):
        """Force a state review in case situation had changed"""
        self.change_state(self.status)



    def on_help(self,button):
        """Triggers a pop-up when Help button is clicked"""
        logger.info("Help requested")   

        text = {"title" : _("Help"),
                "main" : _(" Visit galicaster.teltek.es"),
                "text" : _(" ...or contact us on our community list.")
		}
        buttons = None
        message.PopUp(message.INFO, text,
                      context.get_mainwindow(), buttons)

    def restart(self): # FIXME name confusing cause on_restart_preview
        """Called by Core, if in preview, reload configuration and restart preview."""
        if self.status == GC_STOP:
            self.on_start()
            
        elif self.status == GC_PREVIEW:
            self.change_state(GC_STOP)
            self.recorder.just_restart_preview()
        else:
            logger.warning("Restart preview called while Recording")

        return True

    def handle_pipeline_error(self, origin, error_message):
        """ Captures a pipeline error.
        If the recording are is active, shows it
        """
        self.change_state(GC_ERROR)
        context.get_state().is_error = True
        self.recorder.stop_elements()
        context.get_state().is_recording = False
        if self.error_id:
            self.dispatcher.disconnect(self.error_id)
            self.error_id = None
            #TODO kill previous error if needed
        
        self.error_text = error_message
        if self.focus_is_active:
            self.launch_error_message(error_message)
        
    def launch_error_message(self, error_message):
        """Shows an active error message."""
        text = {
            "title" : _("Recorder"),
            "main" : _(" Please review your configuration \nor load another profile"),                
            "text" : error_message
			}
        self.error_dialog = message.PopUp(message.ERROR, text, 
                                context.get_mainwindow(), None)
        
        

    def on_recover_from_error(self, origin):
        """If an error ocurred, removes preview areas and disconnect error handlers."""   

        if self.error_id:
            self.dispatcher.disconnect(self.error_id)
            self.error_id = None
            self.error_dialog = None
            self.error_text = None
     
        if self.status in [GC_ERROR,GC_STOP]:
            main = self.main_area  
            for child in main.get_children():
                main.remove(child)
                child.destroy()   
            self.change_state(GC_INIT)
            self.on_start()

        elif self.status in [GC_PREVIEW, GC_PRE2]:
            #self.restart()
            self.recorder.stop_preview()
            self.change_state(GC_STOP)
            main = self.main_area  
            for child in main.get_children():
                main.remove(child)
                child.destroy()   
            self.change_state(GC_INIT)
            self.on_start()            
                
        elif self.status != GC_RECORDING:
            logger.debug("Won't recover from this status")
        else:
            logger.error("Profile changed on the middle of a recording")


    def on_quit(self,button=None): 
        """Close active preview or recoridng and destroys the UI"""
        gui = gtk.Builder()
        gui.add_from_file(get_ui_path("quit.glade"))
        dialog = gui.get_object("dialog")
        dialog.set_transient_for(self.get_toplevel())

        response =dialog.run()
        if response == gtk.RESPONSE_OK:   
            dialog.destroy()
            if self.status >= GC_PREVIEW:
                self.recorder.stop_preview()

            self.change_state(GC_EXIT)
            logger.info("Closing Clock and Scheduler")

            self.scheduler_thread_id = None
            self.clock_thread = None 
            # threads closed
            self.emit("delete_event", gtk.gdk.Event(gtk.gdk.DELETE))    
        else:
            dialog.destroy()            
        return True

    # ------------------------- THREADS ------------------------------
 

    def timer_launch_thread(self):
        """Thread handling the recording elapsed time timer."""
        thread_id= self.timer_thread_id
        rec_title = self.gui.get_object("recording1")
        rec_elapsed = self.gui.get_object("recording3")
             
        while thread_id == self.timer_thread_id:            
            gtk.gdk.threads_enter()
            if rec_title.get_text() != self.mediapackage.getTitle():
                rec_title.set_text(self.mediapackage.getTitle())
            msec = datetime.timedelta(microseconds=(self.recorder.get_recorded_time()/1000))
            rec_elapsed.set_text(_("Elapsed Time: ") + readable.long_time(msec))
            gtk.gdk.threads_leave()
            time.sleep(0.5)          
        return True

    def scheduler_launch_thread(self):
        """Thread handling the messages scheduler notification area."""
        # Based on: http://pygstdocs.berlios.de/pygst-tutorial/seeking.html
        thread_id= self.scheduler_thread_id
        event_type = self.gui.get_object("nextlabel")
        title = self.gui.get_object("titlelabel")
        status = self.gui.get_object("eventlabel")

        # Status panel
        # status_disk = self.gui.get_object("status1")
        # status_hours = self.gui.get_object("status2")
        # status_mh = self.gui.get_object("status3")

        gtk.gdk.threads_enter()
        self.check_schedule()
        gtk.gdk.threads_leave()
        parpadeo = True
        changed = False
        signalized = False
        
        if self.font == None:
            anchura = self.get_toplevel().get_screen().get_width()
            if anchura not in [1024,1280,1920]:
                anchura = 1920            
            k1 = anchura / 1920.0
            changing_font = pango.FontDescription("bold "+str(k1*42))       
            self.font = changing_font
        
        bold = pango.AttrWeight(700, 0, -1)
        red = pango.AttrForeground(65535, 0, 0, 0, -1)        
        black = pango.AttrForeground(17753, 17753, 17753, 0, -1)
        font = pango.AttrFontDesc(self.font, 0, -1)

        attr_red = pango.AttrList()
        attr_black = pango.AttrList()

        attr_red.insert(red)
        attr_red.insert(font)
        attr_red.insert(bold)

        attr_black.insert(black)
        attr_black.insert(font)
        attr_black.insert(bold)

        gtk.gdk.threads_enter()
        status.set_attributes(attr_black)
        gtk.gdk.threads_leave()

        one_second = datetime.timedelta(seconds=1)
        while thread_id == self.scheduler_thread_id: 
            gtk.gdk.threads_enter()
            if self.font != changing_font:
                attr_black.insert(pango.AttrFontDesc(self.font, 0, -1))
                attr_red.insert(pango.AttrFontDesc(self.font, 0, -1))
                changing_font = self.font
            if self.current:
                start = self.current.getLocalDate()
                duration = self.current.getDuration() / 1000
                end = start + datetime.timedelta(seconds=duration)
                dif = end - datetime.datetime.now()
                #dif2 = datetime.datetime.now() - start
                if dif < datetime.timedelta(0,0): # Checking for malfuntions
                    self.current = None
                    self.current_mediapackage = None
                    status.set_text("")
                else:
                    status.set_text(_("Stopping in {0}").format(readable.long_time(dif+one_second)))
                    if event_type.get_text() != CURRENT_TEXT:
                        event_type.set_text(CURRENT_TEXT) 
                    if title.get_text() != self.current.title:
                        title.set_text(self.current.title)             
                        
                    if dif < datetime.timedelta(0,TIME_RED_STOP):
                        if not changed:
                            status.set_attributes(attr_red)
                            changed = True
                    elif changed:
                        status.set_attributes(attr_black)
                        changed = False
                    if dif < datetime.timedelta(0,TIME_BLINK_STOP):
                        parpadeo = False if parpadeo else True
                # Timer(diff,self.check_schedule)

            elif self.next:
                start = self.next.getLocalDate()
                dif = start - datetime.datetime.now()
                if event_type.get_text != NEXT_TEXT:
                    event_type.set_text(NEXT_TEXT)
                if title.get_text() != self.next.title:
                    title.set_text(self.next.title)
                status.set_text(_("Starting in {0}").format(readable.long_time(dif)))

                if dif < datetime.timedelta(0,TIME_RED_START):
                    if not changed:
                        status.set_attributes(attr_red)
                        changed = True
                elif changed:
                    status.set_attributes(attr_black)
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
                if title.get_text() != _("No upcoming events"):
                    title.set_text(_("No upcoming events"))
            gtk.gdk.threads_leave()
                
            time.sleep(0.5)
            gtk.gdk.threads_enter()
            self.check_schedule()  
            gtk.gdk.threads_leave()          
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
                gtk.gdk.threads_enter()
                clock.set_label(clocktime)
                gtk.gdk.threads_leave()
            time.sleep(1)          
        return True
    
   
    def check_schedule(self):
        # previous1 = self. current
        previous2 = self.next
        if self.current_mediapackage == None:
            self.current = None
        else:
            self.current = self.repo.get(self.current_mediapackage)
        previous2 = self.next
        self.next = self.repo.get_next_mediapackage() # could be None
        if previous2 != self.next:
            self.reload_state()



    # ------------------------- POPUP ACTIONS ------------------------

    def on_edit_meta(self,button):
        """Pops up the  Metadata editor of the active Mediapackage"""
        self.dispatcher.emit("disable-no-audio")
        #self.change_state(GC_BLOCKED)
        if not self.scheduled_recording:
            Metadata(self.mediapackage, series.get_series(), parent=self)
            mp = self.mediapackage
            self.dispatcher.emit("enable-no-audio")
        #self.change_state(self.previous)  
        return True 

    def show_next(self,button=None,tipe = None):   
        """Pops up the Event Manager"""
        self.dispatcher.emit("disable-no-audio")
        EventManager()
        self.dispatcher.emit("enable-no-audio")
        return True

    def show_about(self,button=None,tipe = None):
        """Pops up de About Dialgo"""
        about_dialog = GCAboutDialog()
        self.dispatcher.emit("disable-no-audio")
        about_dialog.set_transient_for(context.get_mainwindow())
        about_dialog.set_modal(True)
        about_dialog.set_keep_above(False)
        about_dialog.show()
        about_dialog.connect('response', self.on_about_dialog_response)
    
    def on_about_dialog_response(self, origin, response_id):
        if response_id == gtk.RESPONSE_CLOSE or response_id == gtk.RESPONSE_CANCEL:
            self.dispatcher.emit("enable-no-audio") 
            origin.hide()


    # -------------------------- UI ACTIONS -----------------------------

    def create_drawing_areas(self, sources):
        """Create as preview areas as video sources exits"""
        main = self.main_area

        for child in main.get_children():
            main.remove(child)
            child.destroy()        

        areas = dict()
        for source in sources:
            new_area = gtk.DrawingArea()
            new_area.set_name(source)
            new_area.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
            areas[source] = new_area
            main.pack_start(new_area, True, True, int(self.proportion*3))

        for child in main.get_children():
            child.show()
         
        return areas


    def event_change_mode(self, orig, old_state, new_state):
        """Handles the focus or the Rercording Area, launching messages when focus is recoverde"""
        if new_state == 0: 
            self.focus_is_active = True
            if self.recorder:
                self.recorder.mute_preview(False)
            if self.error_text:            
                if self.status != GC_ERROR:
                    self.change_state(GC_ERROR)
                    context.get_state().is_error = True
                self.launch_error_message(self.error_text)            

        if old_state == 0:
            self.focus_is_active = False
            if self.recorder:
                self.recorder.mute_preview(True)

    def change_mode(self, button):
        """Launch the signal to change to another area"""
        self.dispatcher.emit("change-mode", 3) # FIXME use constant

    def set_status_view(self):
        """Set the message and color of the status pilot on the top bar"""

        size = context.get_mainwindow().get_size()
        # k1 = size[0] / 1920.0
        k2 = size[1] / 1080.0

        l = gtk.ListStore(str,str,str)

        main_window = context.get_mainwindow()
        main_window.realize()
        style=main_window.get_style()

        bgcolor = style.bg[gtk.STATE_PRELIGHT]  
        fgcolor = style.fg[gtk.STATE_PRELIGHT]  

        for i in STATUS:
            if i[0] in ["Recording", "Error"]:
                l.append([_(i[0]), i[1], fgcolor])
            else:            
                l.append([_(i[0]), bgcolor, fgcolor])

        v = gtk.CellView()
        v.set_model(l)


        r = gtk.CellRendererText()
        self.renderer=r
        r.set_alignment(0.5,0.5)
        r.set_fixed_size(int(k2*400),-1)


        # k1 = size[0] / 1920.0
        k2 = size[1] / 1080.0
        font = pango.FontDescription("bold "+ str(int(k2*48)))
        r.set_property('font-desc', font)
        v.pack_start(r,True)
        v.add_attribute(r, "text", 0)
        v.add_attribute(r, "background", 1)   
        v.add_attribute(r, "foreground", 2)   
        v.set_displayed_row(0)
        return v

    def check_status_area(self, origin, signal=None, other=None): 
        """Updates the values on the recording tab"""
        s1 = self.gui.get_object("status1")
        s2 = self.gui.get_object("status2")
        # s3 = self.gui.get_object("status3")
        s4 = self.gui.get_object("status4")
 
        freespace = self.repo.get_free_space()
        text_space = readable.size(freespace)
        
        s1.set_text(text_space)
        four_gb = 4000000000.0
        hours = int(freespace/four_gb)
        s2.set_text(_("{0} hours left").format(str(hours)))
        agent = context.get_state().hostname # TODO just consult it once
        if s4.get_text() != agent:
            s4.set_text(agent)

    def check_net(self, origin, status=None):
        """Update the value of the network status"""
        attr1= pango.AttrList()
        attr2= pango.AttrList()
        attr3= pango.AttrList()
        attr4= pango.AttrList()
        gray= pango.AttrForeground(20000, 20000, 20000, 0, -1)
        red = pango.AttrForeground(65535, 0, 0, 0, -1)
        green = pango.AttrForeground(0, 65535, 0, 0, -1)
        black= pango.AttrForeground(5000, 5000, 5000, 0, -1)
        attr1.insert(gray)
        attr2.insert(green)
        attr3.insert(red)
        attr4.insert(black)

        s3 = self.gui.get_object("status3")
        if not self.net_activity:
            s3.set_text("Disabled")
            s3.set_attributes(attr1)
        else:
            net = status
            try:
                if net:
                    s3.set_text("Up")
                    s3.set_attributes(attr2)
                else:
                    s3.set_text("Down")  
                    s3.set_attributes(attr3)
            except KeyError:
                s3.set_text("Connecting")
                s3.set_attributes(attr4)

    def resize(self):
        """Adapts GUI elements to the screen size"""
        size = context.get_mainwindow().get_size()
        altura = size[1]
        anchura = size[0]
        
        k1 = anchura / 1920.0
        k2 = altura / 1080.0
        self.proportion = k1

        #Recorder
        clock = self.gui.get_object("local_clock")
        logo = self.gui.get_object("classlogo")       
        nextl = self.gui.get_object("nextlabel")
        title = self.gui.get_object("titlelabel")
        # eventl = self.gui.get_object("eventlabel")
        pbox = self.gui.get_object("prebox")

        rec_title = self.gui.get_object("recording1")
        rec_elapsed = self.gui.get_object("recording3")
        status_panel = self.gui.get_object('status_panel')

        l1 = self.gui.get_object("tab1")
        l2 = self.gui.get_object("tab2")
        l3 = self.gui.get_object("tab3")
                    
        relabel(clock,k1*25,False)
        font = pango.FontDescription("bold "+str(int(k2*48)))
        self.renderer.set_property('font-desc', font)
        self.renderer.set_fixed_size(int(k2*400),-1)
        pixbuf = gtk.gdk.pixbuf_new_from_file(get_image_path('logo.svg'))  
        pixbuf = pixbuf.scale_simple(
            int(pixbuf.get_width()*k1),
            int(pixbuf.get_height()*k1),
            gtk.gdk.INTERP_BILINEAR)
        logo.set_from_pixbuf(pixbuf)

        modification = "bold "+str(k1*42)
        self.font = pango.FontDescription(modification)     
        relabel(nextl,k1*25,True)
        relabel(title,k1*33,True)

        # REC AND STATUS PANEL
        relabel(rec_title, k1*25, True)
        rec_title.set_line_wrap(True)
        rec_title.set_width_chars(40)
        relabel(rec_elapsed, k1*28, True)

        for child in status_panel.get_children():
            if type(child) is gtk.Label:
                relabel(child,k1*19,True)
        relabel(l1,k1*20,False)
        relabel(l2,k1*20,False)
        relabel(l3,k1*20,False)

        for name  in ["recbutton","pausebutton","stopbutton","editbutton","swapbutton","helpbutton"]:
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
        # change stop button
        for name in ["pause","stop"]:
            button = self.gui.get_object(name+"button")
            image = button.get_children()[0]
            pixbuf = gtk.gdk.pixbuf_new_from_file(get_image_path('gc-'+name+'.svg'))
            pixbuf = pixbuf.scale_simple(
                int(80*k1),
                int(80*k1),
                gtk.gdk.INTERP_BILINEAR)
            image.set_from_pixbuf(pixbuf)  

        for name  in ["previousbutton", "morebutton"]:
            button = self.gui.get_object(name)
            button.set_property("width-request", int(k1*70) )
            button.set_property("height-request", int(k1*70) )

            image = button.get_children()
            if type(image[0]) == gtk.Image:
                image[0].set_pixel_size(int(k1*56))  


        talign = self.gui.get_object("top_align")
        talign.set_padding(int(k1*10),int(k1*25),0,0)
        calign = self.gui.get_object("control_align")
        calign.set_padding(int(k1*10),int(k1*30),int(k1*50),int(k1*50))
        vum = self.gui.get_object("vubox")
        vum.set_padding(int(k1*20),int(k1*10),int(k1*40),int(k1*40))         
        pbox.set_property("width-request", int(k1*225) )        
        return True

        
    def change_state(self, state):
        """Activates or deactivates the buttons depending on the new state"""
        record = self.gui.get_object("recbutton")
        pause = self.gui.get_object("pausebutton")
        stop = self.gui.get_object("stopbutton")
        helpb = self.gui.get_object("helpbutton")
        editb = self.gui.get_object("editbutton")
        prevb = self.gui.get_object("previousbutton")
        swapb = self.gui.get_object("swapbutton")
        if not self.swap_active:
            swapb.hide()

        if state != self.status:
            self.previous,self.status = self.status,state

        if state == GC_INIT:
            record.set_sensitive(False)
            pause.set_sensitive(False)
            stop.set_sensitive(False)
            helpb.set_sensitive(True)
            prevb.set_sensitive(True)
            editb.set_sensitive(False)
            swapb.set_sensitive(False)
            self.dispatcher.emit("update-rec-status", "Initialization")            

        elif state == GC_PREVIEW:    
            record.set_sensitive( (self.allow_start or self.allow_manual) )
            pause.set_sensitive(False)
            pause.set_active(False)
            stop.set_sensitive(False)
            helpb.set_sensitive(True)
            prevb.set_sensitive(True)
            editb.set_sensitive(False)
            swapb.set_sensitive(True)
            if self.next == None:
                self.dispatcher.emit("update-rec-status", "Idle")            
            else:
                self.dispatcher.emit("update-rec-status", "Waiting")     

        elif state == GC_RECORDING:
            record.set_sensitive(False)
            pause.set_sensitive(self.allow_pause and self.recorder.is_pausable()) 
            stop.set_sensitive( (self.allow_stop or self.allow_manual) )
            helpb.set_sensitive(True)
            prevb.set_sensitive(False)
            swapb.set_sensitive(False)
            editb.set_sensitive(True and not self.scheduled_recording)    
            self.dispatcher.emit("update-rec-status", "  Recording  ")
       
        elif state == GC_PAUSED:
            record.set_sensitive(False)
            pause.set_sensitive(False) 
            stop.set_sensitive(False)
            prevb.set_sensitive(False)
            helpb.set_sensitive(False)
            editb.set_sensitive(False)
  
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

        elif state == GC_BLOCKED: 
            record.set_sensitive(False)
            pause.set_sensitive(False)
            stop.set_sensitive(False)
            helpb.set_sensitive(False)   
            prevb.set_sensitive(False)
            editb.set_sensitive(False)

        elif state == GC_ERROR:             
            record.set_sensitive(False)
            pause.set_sensitive(False)
            stop.set_sensitive(False)
            helpb.set_sensitive(True) 
            prevb.set_sensitive(True )
            editb.set_sensitive(False)


        context.get_state().status = STATUS[state][0]

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

        # Start Preview
        self.dispatcher.emit("start-preview")

 
    def close(self, signal):
        """Handles the area closure, stopping threads, mediapackage and preview"""
        if self.status in [GC_RECORDING]:
            self.close_recording() 
        self.scheduler_thread_id = None
        self.clock_thread_id = None
        if self.status in [GC_PREVIEW]:
            self.recorder.stop_preview()        
        return True        


gobject.type_register(RecorderClassUI)
