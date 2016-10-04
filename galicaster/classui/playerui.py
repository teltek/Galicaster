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


from gi.repository import GObject
from gi.repository import Gtk, Gdk
from gi.repository import Gst
import time
import threading

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict

from galicaster.utils.miscellaneous import get_footer
from galicaster.player import Player
from galicaster.core import context
from galicaster.classui.managerui import ManagerUI
from galicaster.classui import get_ui_path, message


Gdk.threads_init()

from galicaster.player.player import INIT
from galicaster.player.player import READY
from galicaster.player.player import PLAYING
from galicaster.player.player import PAUSED
from galicaster.player.player import STOPPED
from galicaster.player.player import ERRORED

log = context.get_logger()

class PlayerClassUI(ManagerUI):
    """
    Graphic User Interface for Listing Player and Player Alone
    """
    __gtype_name__ = 'PlayerClass'


    def __init__(self,package=None):
        ManagerUI.__init__(self,1)
        builder = Gtk.Builder()
        builder.add_from_file(get_ui_path('player.glade'))
        release = builder.get_object("release_label")
        release.set_label(get_footer())

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
        self.seek_bar=self.gui.get_object("seekbar")
        self.seek_bar.add_events(Gdk.EventMask.SCROLL_MASK)
        self.seek_bar.connect("change-value", self.on_seek)

        # VUMETER

        self.vumeterL = builder.get_object("progressbarL")
        self.vumeterR = builder.get_object("progressbarR")
        self.label_channels_player = builder.get_object("label_channels_player")
        self.rangeVum = 50
        self.stereo = True

        # STATUSBAR
        self.statusbar = builder.get_object("statusbar")
        self.status=builder.get_object("status")
        self.timer=builder.get_object("timer")
        self.video=builder.get_object("video")
        self.presenter=builder.get_object("presenter")

        self.playerui.pack_start(self.strip,False,False,0)
        self.playerui.reorder_child(self.strip,0)
        self.pack_start(self.playerui,True,True,0)

        self.status=INIT
        self.previous=None
        self.change_state(INIT)
        self.mediapackage=None # The Mediapackage being reproduced

        self.thread_id=None
        builder.connect_signals(self)

        self.dispatcher.connect_ui("player-vumeter", self.set_vumeter)
        self.dispatcher.connect("player-status", self.change_state_bypass)
        self.dispatcher.connect_ui('play-list', self.play_from_list)
        self.dispatcher.connect_ui("view-changed", self.event_change_mode)
        self.dispatcher.connect_ui("quit", self.close)


#-------------------------- INIT PLAYER-----------------------
    def init_player(self, element, mp):
        """Send absolute file names and Drawing Areas to the player."""
        if (self.mediapackage != mp):
            if self.status == PAUSED:
                self.on_stop_clicked()
                self.clear_timer()

            self.mediapackage = mp

            tracks = OrderedDict()
            videos = OrderedDict()

            index = 0

            for t in mp.getTracks():
                if not t.getFlavor().count('other') and not t.getFlavor().count("delivery") and not t.getFlavor().count("composition"):
                    tracks[t.getIdentifier()] = t.getURI()

                    if t.getMimeType().count("video") and t.getFlavor().count("source"):
                        index+=1
                        videos[t.getIdentifier()] = index

            areas = self.create_drawing_areas(videos)

            self.seek_bar.set_value(0)
            if self.player:
                self.player.quit()

            self.player = Player(tracks, areas)
            self.change_state(READY)

            self.setVideo(None, self.mediapackage.title)
            self.setPresenter(None, self.mediapackage.getCreator())

        self.on_play_clicked(None)

    def play_from_list(self, origin, package):
        """Takes a MP from the listing area and plays it"""
        self.dispatcher.emit("action-view-change", 2)
        self.init_player(None, package)


#------------------------- PLAYER ACTIONS ------------------------

    def on_play_clicked(self, button=None):
        """Starts the reproduction"""
        self.change_state(PLAYING)
        self.player.play()
        self.init_timer()
        return True

    def init_timer(self):
        """Starts the thread handling the timer for visualiztion and seeking feature"""
        self.timer_thread = threading.Thread(target=self.timer_launch_thread)
        self.thread_id = 1
        self.timer_thread.daemon = True
        self.timer_thread.start()

    def on_pause_clicked(self, button=None):
        """Pauses the reproduction"""
        if not button or button.get_active():
            self.player.pause()
            self.change_state(PAUSED)
        else:
            self.on_play_clicked()
        return True

    def on_stop_clicked(self, button=None):
        """Stops the reproduction and send the seek bar to the start"""
        self.thread_id = None
        self.player.stop()
        self.seek_bar.set_value(0)
        self.set_timer(0,self.duration)
        self.change_state(STOPPED)
        return True

    def on_quit_clicked(self, button):
        """Stops the preview and close the player"""
        gui = Gtk.Builder()
        gui.add_from_file(get_ui_path("quit.glade"))
        dialog = gui.get_object("dialog")
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            dialog.destroy()
            if self.status > 0:
                self.player.quit()
            self.change_state(ERRORED)
            self.emit("delete_event", Gdk.Event(Gdk.DELETE))
        else:
            dialog.destroy()
        return True

    def focus_out(self, button, event):
        """Stop the player when focus is lost"""
        self.player.pause()
        self.change_state(STOPPED)

    def on_seek(self, button, scroll_type, new_value):
        """Move to the new position"""
        if new_value>100:
            new_value=100;
        temp=new_value*self.duration*Gst.SECOND/100 # FIXME get_duration propertly

        if scroll_type == Gtk.ScrollType.JUMP:
            self.seeking = True
            if self.player.is_playing():
                self.player.pause()
            value=new_value * self.duration // 100
            self.set_timer(value,self.duration)
            self.jump=temp
            if not self.jump_id:
                log.warning("Handling Seek Jump")
                self.jump_id=self.seek_bar.connect("button-release-event",self.on_seek,0)# FIXME ensure real release, not click

        if scroll_type != Gtk.ScrollType.JUMP: # handel regular scroll
            if scroll_type ==  Gtk.ScrollType.PAGE_FORWARD or scroll_type ==  Gtk.ScrollType.PAGE_BACKWARD:
                self.player.seek(temp, False)

            else: # handle jump
                self.player.seek(self.jump, True) # jump to the position where the cursor was released
                self.seek_bar.disconnect(self.jump_id)
                self.jump_id=0 # jump finished and disconnected
                self.seeking= False


    def create_drawing_areas(self, source): # TODO refactorize, REC
        """Creates the preview areas depending on the video tracks of a mediapackage"""
        main = self.main_area
        for child in main.get_children():
            main.remove(child)
            child.destroy()
        areas = dict()
        for key in source.keys():
            new_area = Gtk.DrawingArea()
            new_area.set_name("playerarea "+str(key))
            areas[key]=new_area
            areas[key].modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("black"))
            main.pack_start(new_area,True,True,3)#TODO editable padding=3

        for child in main.get_children():
            child.show()

        return areas


#------------------------- PACKAGE ACTIONS ------------------------

    def on_edit_meta(self,button):
        """Pop ups the Medatada Editor for the current Mediapackage"""
        key = self.mediapackage.identifier
        self.edit(key)
        self.setVideo(None, self.mediapackage.title)
        self.setPresenter(None, self.mediapackage.getCreator())
        return True

    def on_question(self,button):
        """Pops up a dialog with the available operations"""
        package = self.mediapackage
        self.ingest_question(package)

    def on_delete(self, button):
        """ Pops up a dialog.
        If response is positive the mediapackage is deleted and the focus goes to the previous area"""
        key = self.mediapackage.identifier
        self.delete(key,self.create_delete_dialog_response(key))

        return True

    def create_delete_dialog_response(self, key):

        def on_delete_dialog_response(response_id, **kwargs):
            if response_id in message.POSITIVE:
                self.repository.delete(self.repository.get(key))
                self.thread_id = None
                self.player.stop()
                self.setVideo(None, "")
                self.setPresenter(None, "")
                self.clear_timer()
                self.change_state(INIT)
                self.mediapackage = None
                self.dispatcher.emit("action-view-change", 1)


        return on_delete_dialog_response


#-------------------------- UI ACTIONS -----------------------------

    def timer_launch_thread(self):
        """Thread handling the timer, provides base time for seeking"""
        thread_id= self.thread_id
        self.initial_time=self.player.get_time()
        self.duration = self.player.get_duration()
        GObject.idle_add(self.set_timer, 0, self.duration)

        while thread_id == self.thread_id:
            if not self.seeking :
                if not self.duration:
                    actual_time=self.player.get_time()
                    timer=(actual_time-self.initial_time)/Gst.SECOND
                else:
                    try:
                        format_type, actual_time =self.player.get_position()
                    except:
                            actual_time = 0
                            log.warning("Query position failed")

                    timer = actual_time / Gst.SECOND
                    self.seek_bar.set_value(timer*100/self.duration)
                if thread_id==self.thread_id:
                    GObject.idle_add(self.set_timer, timer, self.duration)

            time.sleep(0.2)
        return True

    def resize(self):
        """Adapts GUI elements to the screen size"""
        buttonlist = ["playbutton", "pausebutton", "stopbutton"]
        secondarylist = ["editbutton", "ingestbutton", "deletebutton"]
        self.do_resize(buttonlist, secondarylist)
        calign = self.gui.get_object("c_align")

        k = self.proportion
        calign.set_padding(int(k*20),int(k*10),0,0)

        return True

    def event_change_mode(self, orig, old_state, new_state):
        """Pause a recording in the event of a change of mode"""
        if old_state == 2 and self.status == PLAYING:
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

        if state==INIT:
            play.set_sensitive(False)
            pause.set_sensitive(False)
            stop.set_sensitive(False)
            editb.set_sensitive(False)
            deleteb.set_sensitive(False)

        if state==READY:
            play.set_sensitive(True)
            pause.set_sensitive(False)
            stop.set_sensitive(False)
            editb.set_sensitive(True)
            deleteb.set_sensitive(True)

        if state==PLAYING:
            play.set_sensitive(False)
            pause.set_sensitive(True)
            pause.set_active(False)
            stop.set_sensitive(True)

        if state==PAUSED:
            play.set_sensitive(True)
            pause.set_sensitive(True)
            stop.set_sensitive(True)

        if state==STOPPED:
            play.set_sensitive(True)
            pause.set_sensitive(False)
            stop.set_sensitive(False)

        if state==ERRORED:
            play.set_sensitive(False)
            pause.set_sensitive(False)
            stop.set_sensitive(False)

    def close(self, signal):
        """Close player UI, stopping threads and reproduction"""
        self.thread_id=None
        if self.status in [PLAYING, PAUSED]:
            self.player.quit()
        return True

#-------------------------- AUDIOBAR -----------------------------

    def set_vumeter(self,element,data, data2, stereo):
        value,value2 = self.scale_data(data,data2)
        self.vumeterL.set_fraction(value)
        self.vumeterR.set_fraction(value2)

        if not stereo and self.stereo:
            self.stereo = False
            self.label_channels_player.set_text("Mono")
        elif stereo and not self.stereo:
            self.stereo = True
            self.label_channels_player.set_text("Stereo")

    def scale_data(self,data,data2):

        if data == "Inf":
            data = -200
        if data2 == "Inf":
            data2 = -200

        if data < -100:
            valor = 1
        else:
            valor=1 - ((data + self.rangeVum)/float(self.rangeVum))

        if data2 < -100:
            valor2 = 1
        else:
            valor2=1 - ((data2 + self.rangeVum)/float(self.rangeVum))

        return valor, valor2

#-------------------------- STATUSBAR -----------------------------

    def clear_timer(self):
        """Empties the timer"""
        self.timer.set_text("")

    def setVideo(self, element, value = None):
        if value != None:
            self.video.set_text(value)
            self.video.set_property("tooltip-text",value)

    def setPresenter(self,element, value):
        self.presenter.set_text(value or '')
        self.presenter.set_property("tooltip-text",value or '')

    def set_timer(self,value,duration):
        """Sets the timer on reproduction environments"""
        self.timer.set_text(self.time_readable2(value,duration))

    def time_readable(self,seconds):
        """ Generates date hour:minute:seconds from seconds"""
        iso = int(seconds)
        return "{}:{:02d}:{:02d}".format(iso/3600, (iso%3600)/60, iso%60)

    def time_readable2(self,s1,s2):
        """ Generates date hour:minute:seconds from seconds """
        t1=self.time_readable(s1)
        t2=self.time_readable(s2)
        timing = t1+" / "+t2
        return timing

GObject.type_register(PlayerClassUI)
