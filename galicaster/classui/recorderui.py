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

TODO:
 * check_status_area timeout???
 * Si se quita de pausado (termina una grabacion agendada mientras está pausado) quita el pause
        elif state == GC_STOP:
            if self.previous == GC_PAUSED:
                self.pause_dialog.destroy()
 * Waiting vs Iddle en status
     if self.next == None and state == GC_PREVIEW:
            self.view.set_displayed_row(GC_PRE2)


"""

from gi.repository import GObject
from gi.repository import Gtk, Gdk, GdkPixbuf
#import Gtk.glade
from gi.repository import Pango
import datetime

from galicaster.utils.miscellaneous import get_footer
from galicaster.core import context

from galicaster.classui.metadata import MetadataClass as Metadata
from galicaster.classui import message
from galicaster.classui import get_ui_path, get_image_path
from galicaster.utils import readable
from galicaster.utils.resize import relabel, resize_button
from galicaster.utils.i18n import _

from galicaster.recorder.service import STATUSES
from galicaster.recorder.service import INIT_STATUS
from galicaster.recorder.service import PREVIEW_STATUS
from galicaster.recorder.service import RECORDING_STATUS
from galicaster.recorder.service import PAUSED_STATUS
from galicaster.recorder.service import ERROR_STATUS

from collections import OrderedDict

Gdk.threads_init()

logger = context.get_logger()
status_label_changed = True
status_label_blink = True
signalized = False

# No-op function for i18n
def N_(string): return string

TIME_BLINK_START = 20
TIME_BLINK_STOP = 20
TIME_RED_START = 50
TIME_RED_STOP = 50
TIME_UPCOMING = 60

NEXT_TEXT = _("Upcoming")
CURRENT_TEXT = _("Current")


class RecorderClassUI(Gtk.Box):
    """
    Graphic User Interface for Record alone
    """

    __gtype_name__ = 'RecorderClass'

    def __init__(self, package=None):
        logger.info("Creating Recording Area")
        Gtk.Box.__init__(self)

        builder = Gtk.Builder()
        builder.add_from_file(get_ui_path('recorder.glade'))
        release = builder.get_object("release_label")
        release.set_label(get_footer())

        # TEST
        self.repo = context.get_repository()
        self.dispatcher = context.get_dispatcher()
        self.worker = context.get_worker()
        self.conf = context.get_conf()
        self.recorder = context.get_recorder()
        self.recorder.set_create_drawing_areas_func(self.create_drawing_areas)
        self.start_recording = False
        self.font = None
        self.scheduled_recording = False
        self.focus_is_active = False
        self.net_activity = None
        self.error_dialog = None

        # BUILD
        self.recorderui = builder.get_object("recorderbox")
        self.main_area = builder.get_object("videobox")
        self.vubox = builder.get_object("vubox")
        self.gui = builder

        # VUMETER
        self.rangeVum = 50
        self.thresholdVum = self.conf.get_float('audio','min')
        self.mute = False
        self.stereo = True
        self.vumeterL = builder.get_object("progressbarL")
        self.vumeterR = builder.get_object("progressbarR")
        self.label_channels= builder.get_object("label_channels")

        # SWAP
        if not self.conf.get_boolean('basic', 'swapvideos'):
            self.gui.get_object("swapbutton").hide()
        self.swap = False

        # STATUS
        self.view = self.set_status_view()
        hbox1 = self.gui.get_object('hbox1')
        hbox1.add(self.view)
        self.dispatcher.connect_ui("init", self.check_status_area)
        self.dispatcher.connect_ui("init", self.check_net, None)
        self.dispatcher.connect_ui("opencast-status", self.check_net)

        # UI
        self.pack_start(self.recorderui,True,True,0)

        # Event Manager
        self.dispatcher.connect_ui("recorder-vumeter", self.set_vumeter)
        self.dispatcher.connect_ui("view-changed", self.event_change_mode)
        self.dispatcher.connect_ui("recorder-status", self.handle_status)
        self.dispatcher.connect_ui("recorder-ready", self.reset_mute)

        #nb=builder.get_object("data_panel")
        # pages = nb.get_n_pages()
        # for index in range(pages):
        #     page=nb.get_nth_page(index)
        #     nb.set_tab_label_packing(page, True, True,Gtk.PackType.START)

        # STATES
        self.previous = None

        # PERMISSIONS
        self.allow_pause = self.conf.get_permission("pause")
        self.allow_start = self.conf.get_permission("start")
        self.allow_stop = self.conf.get_permission("stop")
        self.allow_manual = self.conf.get_permission("manual")
        self.allow_overlap = self.conf.get_permission("overlap")

        self.help_main_str = self.conf.get('help', 'main')
        self.help_text_str = self.conf.get('help', 'text')
        
        # OTHER
        builder.connect_signals(self)
        self.net_activity = self.conf.get_boolean('ingest', 'active')

        self.proportion = 1

        #TIMEOUTS
        deps = self.update_scheduler_deps()
        GObject.timeout_add(500, self.update_scheduler_timeout, *deps)
        self.update_clock_timeout(self.gui.get_object("local_clock"))
        GObject.timeout_add(10000, self.update_clock_timeout, self.gui.get_object("local_clock"))


    # VUMETER
    def set_vumeter(self,element, data, data2, stereo):
        value, value2 = self.scale_data(data, data2)
        self.vumeterL.set_fraction(value)
        self.vumeterR.set_fraction(value2)
        if not stereo and self.stereo:
            self.stereo = False
            self.label_channels.set_text("Mono")
        elif stereo and not self.stereo:
            self.stereo = True
            self.label_channels.set_text("Stereo")


    def clear_vumeter(self):
        self.vumeterL.set_fraction(0)
        self.vumeterR.set_fraction(0)

    def scale_data(self,data, data2):
        if data == "Inf":
            data = -200
        if data2 == "Inf":
            data2 = -200

        average = (data + data2)/2.0
        if not self.mute:
            if average < (self.thresholdVum):
                self.dispatcher.emit("audio-mute")
                self.mute = True
        if self.mute and average > (self.thresholdVum + 5.0):
            self.dispatcher.emit("audio-recovered")
            self.mute = False


        if data < -self.rangeVum:
            valor = 1
        else:
            valor = 1 - ((data + self.rangeVum)/float(self.rangeVum))

        if data2 < -self.rangeVum:
            valor2 = 1
        else:
            valor2 = 1 - ((data2 + self.rangeVum)/float(self.rangeVum))

        return valor, valor2


    def swap_videos(self, button=None):
        """GUI callback"""
        self.swap = not self.swap
        self.dispatcher.emit("action-reload-profile")
        self.mute = False

    def on_rec(self,button=None):
        """GUI callback for manual recording"""
        logger.info("Recording")
        self.recorder.record()


    def on_pause(self, button):
        """GUI callback for pause/resume the recording"""
        if self.recorder.status == PAUSED_STATUS:
            self.dispatcher.emit("action-audio-enable-msg")
            logger.debug("Resuming Recording")
            self.recorder.resume()

        elif self.recorder.status == RECORDING_STATUS:
            self.dispatcher.emit("action-audio-disable-msg")
            logger.debug("Pausing Recording")
            self.recorder.pause()

            self.pause_dialog = self.create_pause_dialog(self.get_toplevel())
            if self.pause_dialog.run() == 1:
                self.on_pause(None)
            self.pause_dialog.destroy()


    def create_pause_dialog(self, parent):
        gui = Gtk.Builder()
        gui.add_from_file(get_ui_path("paused.glade"))
        dialog = gui.get_object("dialog")
        dialog.set_transient_for(parent)
        dialog.set_type_hint(Gdk.WindowTypeHint.TOOLBAR)
        dialog.set_modal(True)
        dialog.set_keep_above(False)
        dialog.set_skip_taskbar_hint(True)
        size = context.get_mainwindow().get_size()
        k2 = size[1] / 1080.0
        size = int(k2*150)
        dialog.set_default_size(size,size)
        button = gui.get_object("image")
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(get_image_path('gc-pause.svg'))
        pixbuf = pixbuf.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
        button.set_from_pixbuf(pixbuf)
        return dialog


    def on_ask_stop(self,button):
        """GUI callback for stops preview or recording and closes the Mediapakage"""
        if self.conf.get_boolean("basic", "stopdialog"):
            text = {"title" : _("Recorder"),
                    "main" : _("Are you sure you want to\nstop the recording?")}
            buttons = (Gtk.STOCK_STOP, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT)
            self.dispatcher.emit("action-audio-disable-msg")
            #warning = message.PopUp(message.WARN_STOP, text,
            #  context.get_mainwindow(), buttons)
            message.PopUp(message.WARN_STOP, text,
                          context.get_mainwindow(), buttons, self.on_stop_dialog_response)
            self.dispatcher.emit("action-audio-enable-msg")
            #if warning.response not in message.POSITIVE or self.recorder.status not in [RECORDING_STATUS]:
            #    return False

    def on_stop_dialog_response(self, response_id, **kwargs):
        """ Manage the response of the WARN_STOP dialog """
        self.recorder.stop()


    def on_help(self,button):
        """GUI callback to triggers a pop-up when Help button is clicked"""
        logger.info("Help requested")

        text = {"title" : _("Help"),
                "main" : _(self.help_main_str),
                "text" : _(self.help_text_str)
                }
        buttons = None
        self.dispatcher.emit("action-audio-disable-msg")
        message.PopUp(message.INFO, text,
                      context.get_mainwindow(), buttons)
        self.dispatcher.emit("action-audio-enable-msg")


    def launch_error_message(self, error_msg=None):
        """Shows an active error message."""
        msg = error_msg or self.recorder.error_msg
        text = {
            "title" : _("Recorder"),
            "main" : _(" Please review your configuration \nor load another profile"),
            "text" : msg
                        }

        if self.error_dialog:
            self.destroy_error_dialog()
        self.error_dialog = message.PopUp(message.ERROR, text,
                                          context.get_mainwindow(), None, self.on_close_error_affirmative)

    def on_close_error_affirmative(self, origin=None, builder=None, popup=None):
        self.dispatcher.emit("action-reload-profile")


    def destroy_error_dialog(self):
        if self.error_dialog:
            self.error_dialog.dialog_destroy()
            self.error_dialog = None


    def recording_info_timeout(self, rec_title, rec_elapsed):
        """GObject.timeout callback with 500 ms intervals"""
        if self.recorder.status == RECORDING_STATUS:
            if rec_title.get_text() != self.recorder.current_mediapackage.getTitle():
                rec_title.set_text(self.recorder.current_mediapackage.getTitle())
            msec = datetime.timedelta(microseconds=(round(self.recorder.get_recorded_time()/1000.0,-6)))
            rec_elapsed.set_text(_("Elapsed Time: ") + readable.long_time(msec))
            return True
        return False


    def update_clock_timeout(self, clock):
        """GObject.timeout callback with 10000 ms intervals"""
        clocktime = datetime.datetime.now().time().strftime("%H:%M")
        clock.set_text(clocktime)
        return True


    def update_scheduler_deps(self):
        """dependences for GObject.timeout callback with 500 ms intervals"""
        event_type = self.gui.get_object("nextlabel")
        title = self.gui.get_object("titlelabel")
        status = self.gui.get_object("eventlabel")

        return status, event_type, title


    def update_scheduler_timeout(self, status, event_type, title):
        """GObject.timeout callback with 500 ms intervals"""
        global status_label_changed, status_label_blink, signalized

        if self.recorder.current_mediapackage and not self.recorder.current_mediapackage.manual:
            start = self.recorder.current_mediapackage.getLocalDate()
            duration = self.recorder.current_mediapackage.getDuration() / 1000
            end = start + datetime.timedelta(seconds=duration)
            dif = end - datetime.datetime.now()

            if dif < datetime.timedelta(0):
                return True

            if self.recorder.current_mediapackage.anticipated:
                if event_type.get_text() != CURRENT_TEXT or title.get_text() != self.recorder.current_mediapackage.title:
                    status.set_text("")
                    event_type.set_text(CURRENT_TEXT)
                    title.set_text(self.recorder.current_mediapackage.title)
                return True
            status.set_text(_("Stopping in {0}").format(readable.long_time(dif)))
            event_type.set_text(CURRENT_TEXT)
            title.set_text(self.recorder.current_mediapackage.title)

            if dif < datetime.timedelta(0, TIME_RED_STOP):
                if not status_label_changed:
                    status.set_name('red_coloured')
                    status_label_changed = True
            elif status_label_changed:
                status.set_name('black_coloured')
                status_label_changed = False
            if dif < datetime.timedelta(0,TIME_BLINK_STOP):
                if status_label_blink:
                    status.set_name('blinking_coloured_from')
                else:
                    status.set_name('blinking_coloured_to')
                status_label_blink = not status_label_blink

        else:
            next_mediapackage = self.repo.get_next_mediapackage()
            if next_mediapackage and next_mediapackage.isScheduled():
                start = next_mediapackage.getLocalDate()
                dif = start - datetime.datetime.now()
                if event_type.get_text != NEXT_TEXT:
                    event_type.set_text(NEXT_TEXT)
                if title.get_text() != next_mediapackage.title:
                    title.set_text(next_mediapackage.title)
                status.set_text(_("Starting in {0}").format(readable.long_time(dif)))

                if dif < datetime.timedelta(0,TIME_UPCOMING):
                    if not signalized:
                        self.dispatcher.emit("recorder-upcoming-event")
                    signalized = True
                elif signalized:
                    signalized = False


                if dif < datetime.timedelta(0,TIME_RED_START):
                    if not status_label_changed:
                        status.set_name('red_coloured')
                        status_label_changed = True
                elif status_label_changed:
                    status.set_name('black_coloured')
                    status_label_changed = False

                if dif < datetime.timedelta(0,TIME_BLINK_START):
                    if status_label_blink:
                        status.set_name('blinking_coloured_from')
                    else:
                        status.set_name('blinking_coloured_to')
                    status_label_blink = not status_label_blink

            else: # Not current or pending recordings
                if event_type.get_text():
                    event_type.set_text("")
                if status.get_text():
                    status.set_text("")
                if title.get_text() != _("No upcoming events"):
                    title.set_text(_("No upcoming events"))

        return True



    def on_edit_meta(self,button):
        """GUI callback Pops up the  Metadata editor of the active Mediapackage"""
        self.dispatcher.emit("action-audio-disable-msg")
        if self.recorder.current_mediapackage and self.recorder.current_mediapackage.manual:
            Metadata(self.recorder.current_mediapackage, parent=self)
            self.dispatcher.emit("action-audio-enable-msg")
        return True


    def show_next(self,button=None,tipe = None):
        """GUI callback Pops up the Event Manager"""
        self.dispatcher.emit("action-audio-disable-msg")
        text = {
                'title' : _('Next Recordings'),
                'next_recs' : self.get_next_recs(),
                }
        message.PopUp(message.NEXT_REC, text, context.get_mainwindow())
        self.dispatcher.emit("action-audio-enable-msg")
        return True

    def get_next_recs(self):
        mps = self.repo.get_next_mediapackages(5)
        mp_info = []
        for mp in mps:

            date = ''
            rec_time = mp.getLocalDate()
            if rec_time.date() == datetime.date.today():
                date = "Today"
            elif rec_time.date() == ( datetime.date.today()+datetime.timedelta(1) ):
                date = "Tomorrow"
            else:
                date = mp.getDate().strftime("%d %b %Y")

            hour = rec_time.time().strftime("%H:%M")

            # FIXME REFACTOR DURATION
            info = OrderedDict()
            info['title']    = mp.title
            info['date']     = date
            info['duration'] = hour
            info['button']   = mp.identifier

            mp_info.append(info)
        return mp_info

    def show_about(self,button=None,tipe = None):
        text = {"title" : _("About"),
                    "main" : ''}
        message.PopUp(message.ABOUT, text, context.get_mainwindow())

    def create_drawing_areas(self, sources):
        """Create as preview areas as video sources exits"""
        main = self.main_area

        for child in main.get_children():
            main.remove(child)
            child.destroy()

        if self.swap:
            sources.reverse()

        areas = dict()
        for source in sources:
            new_area = Gtk.DrawingArea()
            new_area.set_name(source)
            new_area.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("black"))
            areas[source] = new_area
            main.pack_start(new_area, True, True, int(self.proportion*3))

        for child in main.get_children():
            child.show()

        return areas

    def event_change_mode(self, orig, old_state, new_state):
        """Handles the focus or the Rercording Area, launching messages when focus is recoverde"""
        if new_state == 0:
            self.focus_is_active = True
            self.recorder.mute_preview(False)
            if self.recorder.status == ERROR_STATUS:
                self.launch_error_message()

        if old_state == 0:
            self.focus_is_active = False
            self.recorder.mute_preview(True)


    def change_mode(self, button):
        """GUI callback Launch the signal to change to another area"""
        self.dispatcher.emit("action-view-change", 3) # FIXME use constant


    def set_status_view(self):
        """Set the message and color of the status pilot on the top bar"""

        size = context.get_mainwindow().get_size()
        k1 = size[0] / 1920.0
#        k2 = size[1] / 1080.0

        l = Gtk.ListStore(str,str,str)

        main_window = context.get_mainwindow()
        main_window.realize()

        for i in STATUSES:
            l.append([_(i.description), i.bg_color, i.fg_color])

        v = Gtk.CellView()
        v.set_model(l)
        v.get_style_context().add_class('label_extrabig')

        r = Gtk.CellRendererText()
        self.renderer=r
        r.set_alignment(0.5,0.5)

        # k1 = size[0] / 1920.0
        v.pack_start(r,True)
        v.add_attribute(r, "text", 0)
        v.add_attribute(r, "background", 1)
        v.add_attribute(r, "foreground", 2)
#        v.set_displayed_row(0)
        v.set_displayed_row(Gtk.TreePath(0))
        relabel(v,k1*52,True)
        return v



    #TODO timeout
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
        agent = self.conf.get_hostname() # TODO just consult it once
        if s4.get_text() != agent:
            s4.set_text(agent)


    def check_net(self, origin, status=None):
        """Update the value of the network status"""

        network_css_ids = {
            'Disabled'  : 'gray_coloured',
            'Up'        : 'green_coloured',
            'Down'      : 'red_coloured',
            'Connecting': 'orange_coloured',
        }
        s3 = self.gui.get_object("status3")
        if not self.net_activity:
            s3.set_text(_("Disabled"))
            s3.set_name(network_css_ids['Disabled'])
        else:
            try:
                if status == True:
                    s3.set_text(_("Up"))
                    s3.set_name(network_css_ids['Up'])
                elif status == False:
                    s3.set_text(_("Down"))
                    s3.set_name(network_css_ids['Down'])
                else:
                    s3.set_text(_("Connecting..."))
                    s3.set_name(network_css_ids['Connecting'])
            except KeyError:
                s3.set_text(_("Connecting"))
                s3.set_name(network_css_ids['Connecting'])


    def resize(self):
        """Adapts GUI elements to the screen size"""
        size = context.get_mainwindow().get_size()

 #       altura = size[1]
        anchura = size[0]

        k1 = anchura / 1920.0
#        k2 = altura / 1080.0
        self.proportion = k1

        #Recorder
        clock = self.gui.get_object("local_clock")
        logo = self.gui.get_object("classlogo")
        nextl = self.gui.get_object("nextlabel")
        title = self.gui.get_object("titlelabel")
        # eventl = self.gui.get_object("eventlabel")
        pbox = self.gui.get_object("prebox")

        rec_title = self.gui.get_object("recording1")
        status_panel = self.gui.get_object('status_panel')

        l1 = self.gui.get_object("tab1")
        l2 = self.gui.get_object("tab2")
        l3 = self.gui.get_object("tab3")

        relabel(clock,k1*25,False)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(get_image_path('logo.svg'))
        pixbuf = pixbuf.scale_simple(
            int(pixbuf.get_width()*k1*0.5),
            int(pixbuf.get_height()*k1*0.5),
            GdkPixbuf.InterpType.BILINEAR)
        logo.set_from_pixbuf(pixbuf)

        modification = "bold "+str(k1*42)
        self.font = Pango.FontDescription(modification)
        relabel(nextl,k1*25,True)
        relabel(title,k1*33,True)

        # REC AND STATUS PANEL
        relabel(rec_title, k1*25, True)
        rec_title.set_line_wrap(True)

        for child in status_panel.get_children():
            if type(child) is Gtk.Label:
                relabel(child,k1*19,True)
        relabel(l1,k1*20,False)
        relabel(l2,k1*20,False)
        relabel(l3,k1*20,False)

        # change stop button
        for name in ["pause","stop"]:
            button = self.gui.get_object(name+"button")
            image = button.get_children()[0]
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(get_image_path('gc-'+name+'.svg'))
            pixbuf = pixbuf.scale_simple(
                int(60*k1),
                int(60*k1),
                GdkPixbuf.InterpType.BILINEAR)
            image.set_from_pixbuf(pixbuf)

        for name  in ["previousbutton", "morebutton"]:
            button = self.gui.get_object(name)
            button.set_property("width-request", int(k1*250) )
            button.set_property("height-request", int(k1*70) )

            image = button.get_children()
            if type(image[0]) == Gtk.Image:
                image[0].set_pixel_size(int(k1*56))

        vum = self.gui.get_object("vubox")
        vum.set_padding(int(k1*20),int(k1*10),0,0)
        pbox.set_property("width-request", int(k1*225) )
        hbox1 = self.gui.get_object('hbox1')
        hbox1.set_property('spacing', int(k1*325))

        for name  in ["recbutton","pausebutton","stopbutton","helpbutton","editbutton","swapbutton"]:
            button = self.gui.get_object(name)
            resize_button(button,size_image=k1*60,size_box=k1*46,size_label=k1*16)

        return True


    def handle_status(self, origin, status):
        """Activates or deactivates the buttons depending on the new status"""

        record = self.gui.get_object("recbutton")
        pause = self.gui.get_object("pausebutton")
        stop = self.gui.get_object("stopbutton")
        helpb = self.gui.get_object("helpbutton")
        editb = self.gui.get_object("editbutton")
        prevb = self.gui.get_object("previousbutton")
        swapb = self.gui.get_object("swapbutton")

        if status == INIT_STATUS:
            record.set_sensitive(False)
            pause.set_sensitive(False)
            stop.set_sensitive(False)
            helpb.set_sensitive(True)
            prevb.set_sensitive(True)
            editb.set_sensitive(False)
            swapb.set_sensitive(False)

        elif status == PREVIEW_STATUS:
            record.set_sensitive( (self.allow_start or self.allow_manual) )
            pause.set_sensitive(False)
            stop.set_sensitive(False)
            helpb.set_sensitive(True)
            prevb.set_sensitive(True)
            editb.set_sensitive(False)
            swapb.set_sensitive(True)

        elif status == RECORDING_STATUS:
            GObject.timeout_add(500, self.recording_info_timeout,
                                self.gui.get_object("recording1"),
                                self.gui.get_object("recording3"))

            record.set_sensitive(False)
            pause.set_sensitive(self.allow_pause and self.recorder.is_pausable())
            stop.set_sensitive( (self.allow_stop or self.allow_manual) )
            helpb.set_sensitive(True)
            prevb.set_sensitive(False)
            swapb.set_sensitive(False)
            editb.set_sensitive(self.recorder.current_mediapackage and self.recorder.current_mediapackage.manual)

        elif status == PAUSED_STATUS:
            record.set_sensitive(False)
            pause.set_sensitive(False)
            stop.set_sensitive(False)
            prevb.set_sensitive(False)
            helpb.set_sensitive(False)
            editb.set_sensitive(False)

        elif status == ERROR_STATUS:
            record.set_sensitive(False)
            pause.set_sensitive(False)
            stop.set_sensitive(False)
            helpb.set_sensitive(True)
            prevb.set_sensitive(True)
            editb.set_sensitive(False)
            if self.focus_is_active:
                self.launch_error_message()

        # Change status label
        if status in STATUSES:
            self.view.set_displayed_row(Gtk.TreePath(STATUSES.index(status)))
        else:
            logger.error("Unable to change status label, unknown status {}".format(status))
        # Close error dialog
        if status not in [ERROR_STATUS] and self.error_dialog:
            self.destroy_error_dialog()

    def block(self):
        prev = self.gui.get_object("prebox")
        prev.set_child_visible(False)
        self.focus_is_active = True
        self.recorder.mute_preview(False)

        # Show Help or Edit_meta
        helpbutton = self.gui.get_object("helpbutton")
        helpbutton.set_visible(True)

        editbutton = self.gui.get_object("editbutton")
        parent = editbutton.get_parent()
        parent.remove(editbutton)

    def reset_mute(self, element):
        self.mute = False

GObject.type_register(RecorderClassUI)
