#!/usr/bin/env python
# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import pygtk
pygtk.require('2.0')

import sys
import os
import time

import gobject
gobject.threads_init()

import pygst
pygst.require('0.10')
import gst
import gst.interfaces
import gtk
gtk.gdk.threads_init()

class SwitchTest:
    def __init__(self, videowidget, avideowidget, audiowidget):
        self.playing = False
        self.prepared = False
        self.index = 1
        self.temp = "temp.avi"
        self.inputs = 
        
        pipestr = (' v4l2src device=/dev/video0 ! tee name=tee1 ! queue ! s.sink1'
                   ' v4l2src device=/dev/video0 ! tee name=tee2 ! queue ! s.sink2'
                   ' v4l2src device=/dev/video0 ! tee name=tee3 ! queue ! s.sink3'
                   ' v4l2src device=/dev/video0 ! tee name=tee4 ! queue ! s.sink4'
                   ' input-selector name=s ! videorate name= estadisticas ! videoscale ! video/x-raw-yuv, width=720, height=576, framerate=25/1 !'
                   ' tee name=tee6 ! queue ! autovideosink name=live'
                   ' tee6.         ! queue ! ffmpegcolorspace ! ffenc_dvvideo bitrate=30000     ! queue ! mux.'
                   ' alsasrc ! audioconvert ! audio/x-raw-int, rate=48000, channels=1, width=16 !'
                   ' audioamplify amplification=12 ! tee name=tee5 ! queue ! mux.'
                   ' avimux name=mux  bigfile=true ! queue ! valve name=valvula drop=false !'
                   ' filesink name=sinkrecord location=' + self.temp +' sync=false'
                   ' tee1.  !  queue ! autovideosink name=pre1'
                   ' tee2.  !  queue ! autovideosink name=pre2'
                   ' tee3.  !  queue ! autovideosink name=pre3'
                   ' tee4.  !  queue ! autovideosink name=pre4'
                   ' tee5.  !  queue ! audioconvert ! monoscope ! ximagesink name=audio'
                   )
        self.pipeline = gst.parse_launch(pipestr)
        self.videowidget = videowidget
        self.avideowidget = avideowidget
        self.audiowidget = audiowidget
        
        bus = self.pipeline.get_bus()
        bus.enable_sync_message_emission()
        bus.add_signal_watch()
        bus.connect('sync-message::element', self.on_sync_message)
        bus.connect('message', self.on_message)

    def on_sync_message(self, bus, message):
        
        if message.structure is None:
            return
        if message.structure.get_name() == 'prepare-xwindow-id':
            # Sync with the X server before giving the X-id to the sink
            gtk.gdk.threads_enter()
            gtk.gdk.display_get_default().sync()

            sinkname = message.src.get_property('name')
            print sinkname
            if sinkname == "live-actual-sink-xvimage":
                self.videowidget.set_sink(message.src)
            elif sinkname == "audio":
                self.audiowidget.set_sink(message.src)
            else:
                for ovideowidget in self.avideowidget:
                    if ovideowidget.imagesink == None:
                        ovideowidget.set_sink(message.src)
                        break
        
            message.src.set_property('force-aspect-ratio', True)
            gtk.gdk.threads_leave()
            
    def on_message(self, bus, message):
        t = message.type
        if (("valvula" == message.src.get_property('name')) and (not (self.prepared))):
            time.sleep(2)
            message.src.set_property('drop',True)
            self.prepared = True
            
        if t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            #if self.on_eos:
            #    self.on_eos()
            self.playing = False
        elif t == gst.MESSAGE_EOS:
            #if self.on_eos:
            #    self.on_eos()
            self.playing = False

    def start(self):
        self.playing = True
        gst.info("Start Preview")
        self.pipeline.set_state(gst.STATE_PLAYING)
        
    def record(self):
        gst.info("Start Record")
        valvula = self.pipeline.get_by_name('valvula')
        valvula.set_property('drop', False)
        
    def stop(self):
        gst.info("Stop record")
        valvula = self.pipeline.get_by_name('valvula')
        valvula.set_property('drop', True)
        sinkrec = self.pipeline.get_by_name('sinkrecord')
        sinkrec.set_state(gst.STATE_NULL)
        comando = "ffmpeg -i " + self.temp + " -vcodec copy -acodec copy " + self.location + "_" + str(self.index) + ".avi"
        os.system(comando)
        sinkrec.set_state(gst.STATE_PLAYING)
        
    def quit(self):
        self.pipeline.set_state(gst.STATE_NULL)
        gst.info("free player")
        self.playing = False

    def get_state(self, timeout=1):
        return self.pipeline.get_state(timeout=timeout)

    def is_playing(self):
        return self.playing

    def set_location(self,archivo):
        self.location = archivo
        
    def switch(self, padname):
        switch = self.pipeline.get_by_name('s')
        stop_time = switch.emit('block')
        newpad = switch.get_static_pad(padname)
        start_time = newpad.get_property('running-time')
        
        gst.warning('stop time = %d' % (stop_time,))
        print 'stop time = %d' % (stop_time,)
        gst.warning('stop time = %s' % (gst.TIME_ARGS(stop_time),))
        print 'stop time = %s' % (gst.TIME_ARGS(stop_time),)

        gst.warning('start time = %d' % (start_time,))
        print 'start time = %d' % (start_time,)
        gst.warning('start time = %s' % (gst.TIME_ARGS(start_time),))
        print 'start time = %s' % (gst.TIME_ARGS(start_time),)

        gst.warning('switching from %r to %r'
                    % (switch.get_property('active-pad'), padname))
        print 'switching from %r to %r' % (switch.get_property('active-pad'), padname)
        switch.emit('switch', newpad, stop_time, start_time)
        

class VideoWidget(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.imagesink = None
        self.unset_flags(gtk.DOUBLE_BUFFERED)

    def do_expose_event(self, event):
        if self.imagesink:
            self.imagesink.expose()
            return False
        else:
            return True

    def set_sink(self, sink):
        assert self.window.xid
        self.imagesink = sink
        self.imagesink.set_xwindow_id(self.window.xid)

class SwitchWindow(gtk.Window):
    UPDATE_INTERVAL = 500
    
    __def_win_size__ = (750, 450)
    
    def __init__(self):
        gtk.Window.__init__(self)

        self.set_size_request(*self.__def_win_size__)
        self.set_title("GaliCASTER");
                
        self.create_ui()
        self.player = SwitchTest(self.videowidget,self.arrayVideoWidgets,self.audiowidget)
        
        self.populate_combobox()

        self.update_id = -1
        self.changed_id = -1
        self.seek_timeout_id = -1

        self.p_position = gst.CLOCK_TIME_NONE
        self.p_duration = gst.CLOCK_TIME_NONE

        #asociamos evento de salida
        def on_delete_event():
          self.quit("nada")    
        self.connect('delete-event', lambda *x: on_delete_event())

    def file_sel(self,w):
        self.player.set_location(w)

        
    def load_file(self, location):
        dialog = gtk.FileChooserDialog("Open..",
                                       None,
                                       gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        
        dialog.set_default_response(gtk.RESPONSE_OK)
        
        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)
        filter = gtk.FileFilter()
        filter.set_name("Images")
        filter.add_mime_type("video/x-msvideo")
        filter.add_pattern("*.avi")
        dialog.add_filter(filter)
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.file_sel(dialog.get_filename())
        elif response == gtk.RESPONSE_CANCEL:
            print 'Closed, no files selected'
        dialog.destroy()
                                                                                        
                                  
    def start(self,unused_button):
        self.player.start()

    def record(self,unused_button):
        self.player.record()
        
    def stop(self,unused_button):
        self.player.stop()

    def quit(self, unusedbottom):
        self.player.quit()
        gtk.main_quit()
        
    def populate_combobox(self):
        switch = self.player.pipeline.get_by_name('s')
        for i, pad in enumerate([p for p in switch.pads()
                                 if p.get_direction() == gst.PAD_SINK]):
            self.combobox.append_text(pad.get_name())
            if switch.get_property('active-pad') == pad.get_name():
                self.combobox.set_active(i)
        if self.combobox.get_active() == -1:
            self.combobox.set_active(0)

    def combobox_changed(self):
        model = self.combobox.get_model()
        row = model[self.combobox.get_active()]
        padname, = row
        self.player.switch(padname)

    def create_ui(self):
        vbox = gtk.VBox(False)
        hbox1 = gtk.HBox(False)
        self.add(vbox)
        vbox.pack_start(hbox1)

        #creamos area para ventana de directo
        self.videowidget = VideoWidget()
        self.videowidget.modify_bg(gtk.STATE_NORMAL, self.videowidget.style.black)
        hbox1.pack_start(self.videowidget)


        #creamos area para vumetro
        self.audiowidget = VideoWidget()
        self.audiowidget.modify_bg(gtk.STATE_NORMAL, self.audiowidget.style.black)
        hbox1.pack_end(self.audiowidget)

        
        hboxwidget = gtk.HBox(False)
        vbox.pack_start(hboxwidget)
        
        self.arrayVideoWidgets = [VideoWidget() for each in range(4)]

        for oneWidget in self.arrayVideoWidgets:
            oneWidget.modify_bg(gtk.STATE_NORMAL, oneWidget.style.black)
            hboxwidget.pack_start(oneWidget)
        
        
        hbox = gtk.HBox(False)
        vbox.pack_start(hbox, fill=False, expand=False)
        
        
        self.combobox = combobox = gtk.combo_box_new_text()
        combobox.show()

        hbox.pack_start(combobox)

        self.combobox.connect('changed',
                              lambda *x: self.combobox_changed())

        self.controls = [
                        (gtk.ToolButton(gtk.STOCK_MEDIA_PLAY),self.start),
                        (gtk.ToolButton(gtk.STOCK_FILE), self.load_file),
                        (gtk.ToolButton(gtk.STOCK_MEDIA_RECORD), self.record),
                        (gtk.ToolButton(gtk.STOCK_MEDIA_STOP), self.stop),
                        (gtk.ToolButton(gtk.STOCK_QUIT), gtk.main_quit)
                    ]

        # as well as the container in which to put them
        box = gtk.HButtonBox()

        # asociamos cada boton al metodo correspondiente
        for widget, handler in self.controls:
          widget.connect("clicked", handler)
          box.pack_start(widget, True)

        hbox.pack_end(box, False, False)

        
def main(args):
    def usage():
        sys.stderr.write("usage: %s\n" % args[0])
        return 1

    # Need to register our derived widget types for implicit event
    # handlers to get called.
    gobject.type_register(SwitchWindow)
    gobject.type_register(VideoWidget)

    if len(args) != 1:
        return usage()

    w = SwitchWindow()
    w.show_all()
    gtk.main()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
