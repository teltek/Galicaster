#!/usr/bin/env python
# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import pygtk
pygtk.require('2.0')

import sys
import os
import time
import types
import shutil

import gobject
gobject.threads_init()

import pygst
pygst.require('0.10')
import gst
import gst.interfaces
import gtk
gtk.gdk.threads_init() 

from mediapackage import *
from calendarwindow import CalendarWindow
from pipeline import Pipeline
import ConfigParser
from conf import Conf

from termcolor import colored
# gst.extend import discoverer

# Ordenar as funcions ou repartir por diferentes arquivos - player, recorder, auxiliar, pipelining, ingest...
# Pasar constantes a outro arquivo

insert_message = "<Insert value>"
metadata ={"title": "Title:", "creator": "Presenter:", "ispartof": "Course/Series:", "description": "Description:", 
           "subject": "Subject:", "language": "Language:", "identifier": "Identifier:", "contributor": "Contributor:", 
           "created":"Start Time:", "Title:":"title", "Presenter:":"creator", "Course/Series:":"ispartof", 
           "Description:":"description", "Subject:":"subject", "Language:":"language", "Identifier:":"identifier", 
           "Contributor:":"contributor", "Start Time:":"created"}
properties ={"Temporal Folder":"temp", "MP default name":"zip", "Pipeline":"pipe", "Host":"host", "Username":"username",
             "Password":"password", "Workflow":"workflow", "Player":"player", "Recorder":"recorder"}

basic = [ "temp", "zip", "pipe"]
ingest = [ "host", "username", "password", "workflow" ] # FIXME take names from INI keys
screen = [ "player"]

EXP_STRINGS = [ (0, 'B'), (10, 'KB'),(20, 'MB'),(30, 'GB'),(40, 'TB'), (50, 'PB'),]
ONE_MB = 1024*1024


class Galicaster :
    __def_win_size__ = (750, 450)
    GC_INIT = -1
    GC_QUIT = 0
    GC_REC_INIT = 1
    GC_PLAY_INIT = 2 
    GC_ERROR = 3

    GC_REC_PLAY = 11
    GC_REC_REC = 12
    GC_REC_PAUSE = 13
    GC_REC_STOP = 14

    GC_PLAY_PLAY = 21
    GC_PLAY_REC = 22
    GC_PLAY_PAUSE = 23
    GC_PLAY_STOP = 24

    GC_RECORDER = 0 
    GC_PLAYER = 1

    def __init__(self):

        #estados: -1:INIT 0:STOPPED 1:PLAYING 2:PAUSED
        self.status = self.GC_INIT      
        self.function = self.GC_RECORDER
        self.case = 0

        #mediapackage
        self.mp = Mediapackage()
        self.mp2 = Mediapackage()
        
        #signals and location
        self.bus = gst.Bus
        self.number_of_videos = 2;        
        self.pipeline = gst.Pipeline
        self.valvula1 = gst.Element
        self.valvula2 = gst.Element
        self.valvula3 = gst.Element
        #self.preview1 = gst.Element
        #self.preview2 = gst.Element
        self.duration = 0
        self.jump=0 # valor para realizar o seek
        self.jump_id=0 # id do sinal que regula o seek
        self.correct=False # Para correxir o evento SCROLL_JUMP residual, despois de procesar o RELEASE

        self.conf = Conf()
        timestamp=datetime.datetime.now().replace(microsecond=0).isoformat()
        self.files = [ self.conf.get("basic","temp")+"/"+"gc"+timestamp+"/"+self.conf.get("track1","file"),
                       self.conf.get("basic","temp")+"/"+"gc"+timestamp+"/"+self.conf.get("track2","file") ]
                       
        # self.files = [ "/tmp/CAMERA.mpeg" , "/tmp/SCREEN.mpeg" , "/tmp/AUDIO.mp3" ]
        # self.files = [ '/tmp/video' + str(index) + '_temp.' for index in range(1,self.number_of_videos+1) ]

        #GUI
        self.guifile = "xestor.glade"
        self.gui = gtk.Builder()
        self.gui.add_from_file(self.guifile)
        self.gui.connect_signals(self)

        self.function_area = self.gui.get_object("notebook")
        # status bar
        self.status_f=self.gui.get_object("status_function")
        self.status_s=self.gui.get_object("status_state")
        self.status_t=self.gui.get_object("status_time")
        self.status_disk=self.gui.get_object("status_space")
        self.status_v=self.gui.get_object("status_vumeter")
        
        self.status_f.set_text("Recorder")
        self.status_s.set_text("Iddle")
        self.status_t.set_text("00:00")
        self.status_disk.set_text(self.get_free_space(self.conf.get("basic","temp")))        
        self.chrono = -1 #CHECK IF DELETE
        self.quit_dialog = self.gui.get_object("quitdialog")

        self.quit_dialog = self.gui.get_object("quitdialog")
        self.save_dialog = self.gui.get_object("savedialog")
        self.zip_dialog = self.gui.get_object("zipdialog")
        self.conf_dialog = self.gui.get_object("confdialog")
        
        self.start_button = self.gui.get_object('startbutton')
        self.stop_button = self.gui.get_object('stopbutton')
        self.record_button = self.gui.get_object('recordbutton')

        self.start_button2 = self.gui.get_object('startbutton2')
        self.stop_button2 = self.gui.get_object('stopbutton2')
        self.pause_button2 = self.gui.get_object('pausebutton2')

        #self.chooser1 = self.gui.get_object('file1')
        #self.chooser2 = self.gui.get_object('file2')
        self.chooser1 = None
        self.chooser2 = None

        self.tab1 = self.gui.get_object('recorder')
        self.tab2 = self.gui.get_object('player')

        self.expanderp = self.gui.get_object('expander_player')
        self.infobox = self.gui.get_object('infobox')
        self.infobox2 = self.gui.get_object('infobox2')

        # conectar eventbox do calendario no recorder
        self.eboxrec = self.gui.get_object('ebox_rec')        
        self.eboxrec.add_events(gtk.gdk.BUTTON_PRESS_MASK)#filtrar so o doble click 
        self.eboxrec.connect("button-press-event",self.edit_date)# CONSIDER connect Intro to eventbox notto entry        
        self.eboxrec.get_children()[0].set_text(datetime.datetime.now().replace(microsecond=0).isoformat())

        # conectar events da seekbar
        self.seek_bar=self.gui.get_object("seekbar")
        self.seek_bar.add_events(gtk.gdk.SCROLL_MASK)
        self.seek_bar.connect("change-value",self.seek_player) # FIXME connect only on playing/pause

        # event box for shifting screen preferencers
        self.shifter1 = self.gui.get_object('playershift') 
        self.shifter2 = self.gui.get_object('recordshift') 
        self.shifter1.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.shifter1.connect("button-press-event",self.on_toggle) # CHANGE method name
        self.shifter2.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.shifter2.connect("button-press-event",self.on_toggle) # CHANGE method name
        if self.conf.get("screen","player") == "presentation":
            self.on_toggle(self.shifter1, None)
        if self.conf.get("screen","recorder") == "presentation":
            self.on_toggle(self.shifter2, None)

        # Window
        self.window = self.gui.get_object('mainwindow')  
        self.window.set_size_request(*self.__def_win_size__)
        self.window.set_title("GaliCASTER 0.65");
        
        self.window.connect('delete_event', lambda *x: on_delete_event())
        self.window.update_id = -1
        self.window.changed_id = -1
        self.window.seek_timeout_id = -1

        self.window.p_position = gst.CLOCK_TIME_NONE
        self.window.p_duration = gst.CLOCK_TIME_NONE
        self.window.show_all()

        self.status = self.GC_REC_INIT

        # Initialize videoarea
        self.video1 = VideoWidget()
        self.video2 = VideoWidget()
        self.audio1 = VideoWidget()
        self.videobox = self.gui.get_object('videobox')
        self.videobox.pack_start(self.video1,False)
        self.videobox.pack_end(self.video2,False)

        def on_delete_event():
            self.quit("nada")


############################### GSTREAMER ####################################

    def gstreamer_communication(self,bus) :  #CALL IT w self_bus
        bus = self.pipeline.get_bus()
        bus.enable_sync_message_emission()
        bus.add_signal_watch()
        bus.connect('sync-message::element', self.on_sync_message)
        bus.connect('message', self.on_message)

       
    def on_sync_message(self, bus, message):     
        #print colored("SYNC"+message.structure.get_name(),'blue')
        if message.structure.get_name() == 'prepare-xwindow-id':
            # Sync with the X server before giving the X-id to the sink
            gtk.gdk.threads_enter()
            gtk.gdk.display_get_default().sync()
            
            sinkname = message.src.get_property('name')
            print "on sync message " + sinkname               

            if sinkname == "pre1":
                self.preview1.set_state(gst.STATE_PLAYING)                
                message.src.set_xwindow_id(self.gui.get_object('videoarea1').window.xid)
     
            elif sinkname == "pre2":
                self.preview2.set_state(gst.STATE_PLAYING)
                message.src.set_xwindow_id(self.gui.get_object('videoarea2').window.xid)               
               
            if sinkname == "play1": # Associated to track-1
                if self.conf.get("screen","player")+"/source"==self.mp.tracks[0].etype:
                    message.src.set_xwindow_id(self.gui.get_object('player_left').window.xid)
                else:
                    message.src.set_xwindow_id(self.gui.get_object('player_right').window.xid)

            elif sinkname == "play2": # Associated to track-2
                if self.conf.get("screen","player")+"/source"==self.mp.tracks[1].etype:
                    message.src.set_xwindow_id(self.gui.get_object('player_left').window.xid)
                else:
                    message.src.set_xwindow_id(self.gui.get_object('player_right').window.xid)

            elif sinkname == "playonly": # Only one track avaliable
                message.src.set_xwindow_id(self.gui.get_object('player_left').window.xid) 
                # FIXME coller toda a area de video (despois repor a area doble)

            message.src.set_property('force-aspect-ratio', True)
            gtk.gdk.threads_leave()
            
    def on_message(self, bus, message):
        t = message.type
        # print t        
        if t == gst.MESSAGE_STREAM_STATUS:
            struct = message.structure
            print "STREAM STATUS: "+struct.to_string()
        if t == gst.MESSAGE_ASYNC_DONE:
            print "Async message receive"
            #self.pipeline.set_state(gst.STATE_PLAYING)        
            #self.pipeline.set_state(gst.STATE_PAUSED)     
        if message.src.get_property('name').count("vumeter"):
            print "VUMETER: "+message

        if t == gst.MESSAGE_STATE_CHANGED:
            old, new, pending = message.parse_state_changed()
            if message.src.get_property('name').count("pre"):
                print colored( message.src.get_property('name') + " " + str(old) + " pasa a " + str(new),'red')
            else:
                print message.src.get_property('name') + " " + str(old) + " pasa a " + str(new)
            if message.src.get_property('name').count("pipeline") and ((old, new) == (gst.STATE_READY, gst.STATE_PAUSED)):
                if self.function == self.GC_RECORDER:
                    self.valvula1.set_property('drop', True) 
                    if self.conf.get("basic","pipe") != "only2":
                        self.valvula2.set_property('drop', True) 
                        if self.conf.get("basic","pipe") != "only" and self.conf.get("basic","pipe") != "audio" :
                            if self.conf.get("basic","pipe") != "improved" :
                                self.valvula3.set_property('drop', True) 
                    print "Valvulas  activadas"
                self.pipeline.set_state(gst.STATE_PLAYING)
                

            if message.src.get_property('name')== "pre3" and ((old, new) == (gst.STATE_READY, gst.STATE_PAUSED)):
                print "Audio activado"                
                self.preview3.set_state(gst.STATE_PLAYING)   

        if t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            if self.status == self.GC_REC_PLAY:                            
                self.tab2.set_sensitive(True)   
                self.start_button.set_sensitive(True)
                self.record_button.set_sensitive(False)
                self.stop_button.set_sensitive(False)    
                self.status = self.GC_INIT
            elif self.status == self.GC_PLAY_PLAY:
                self.tab1.set_sensitive(True)
                self.pause_button2.set_sensitive(False)
                self.stop_button2.set_sensitive(False)        
                self.start_button2.set_sensitive(True)
                self.status = self.GC_PLAY_INIT
                self.seek_bar.set_value(0)
                self.pipeline.set_state(gst.STATE_NULL)
            elif self.status == self.GC_REC_REC: 
                pass # CHANGE source for a fakesink                
            else:
                self.status = self.GC_ERROR

        # ACTUALIZACION VUMETRO
        if t == gst.MESSAGE_ELEMENT:
            struct = message.structure
            if struct.get_name() == 'level':
                # print struct['peak'][0], struct['decay'][0], struct['rms'][0]       
                if struct['rms'] < -60 :
                    valor = 0.0
                elif struct['rms'] == float("-inf"):
                    valor = 0.0
                else:                
                    valor=(struct['rms'][0]+60)/60
                    if valor < 0:
                        valor = 0.0                
                self.status_v.set_fraction(valor)              

            # ACTUALIZAR SEEKBAR interval=0.1 s
            if self.function == self.GC_PLAYER:
            # if self.function == 10:
                if self.duration == 0:
                    duration = self.pipeline.query_duration(gst.FORMAT_TIME)[0]
                    self.duration=duration/1000000000 # in seconds
                    self.status_t.set_text(time.strftime('%H:%M:%S',time.gmtime(self.duration)))
                    print colored( "DURATION: "+self.status_t.get_text(),'yellow')
                    print colored( "DURATION (in seconds): "+str(self.duration),'yellow')
                temp=(self.seek_bar.get_value()*self.duration/100)+0.1 # FIX: use interval, value is in seconds
                # print colored(str(value/self.duration),'green')
                self.seek_bar.set_value(100*temp/self.duration)                
                old_time=self.status_t.get_text()
                new_time=str(time.strftime('%H:%M:%S',time.gmtime(temp // 1 )))+" / "+str(time.strftime('%H:%M:%S',time.gmtime(self.duration)))
                if new_time != old_time:
                    self.status_t.set_text(new_time)                       

        # if self.on_eos:
        #    self.on_eos()

        elif t == gst.MESSAGE_EOS:
            print "EOS MESSAGE received"
            self.pipeline.set_state(gst.STATE_NULL)
            if self.function == self.GC_PLAYER:
                self.tab1.set_sensitive(True)
                self.pause_button2.set_sensitive(False)
                self.stop_button2.set_sensitive(False)        
                self.start_button2.set_sensitive(True)
                self.status = self.GC_PLAY_INIT
                self.seek_bar.set_value(0)
                new_time=(str(time.strftime('%H:%M:%S',time.gmtime(self.duration)))+ " / " + 
                          str(time.strftime('%H:%M:%S',time.gmtime(self.duration))))
                self.status_t.set_text(new_time)
                self.duration=0
                print "Stopped"
                self.status_s.set_text("Iddle")
        

########################### SEEK OPERATIONS ##################################

    def seek_player(self,button,scroll_type,new_value):
        """Move to the new position"""
        print colored("SEEKING tempo: "+str(new_value)+" | porcentaxe:"+str(new_value*self.duration/100),'blue')
        print scroll_type
        ns=1000000000/100
        if new_value>100:
            new_value=100;
        temp=new_value*self.duration*ns
        if scroll_type == gtk.SCROLL_JUMP and not self.correct:
            print "Handling JUMP"
            if self.pipeline.get_state()[1]==gst.STATE_PLAYING:
                self.pipeline.set_state(gst.STATE_PAUSED)
            new_time=(str(time.strftime('%H:%M:%S',time.gmtime(new_value*self.duration // 100 )))+ " / " + 
                       str(time.strftime('%H:%M:%S',time.gmtime(self.duration))))
            self.status_t.set_text(new_time)
            self.jump=temp
            if not self.jump_id:
                self.jump_id=self.seek_bar.connect("button-release-event",self.seek_player,0)# FIXME ensure real release, not click                        
        if self.correct:
            self.correct=False
            

        if scroll_type != gtk.SCROLL_JUMP:
            p1 = self.pipeline.get_by_name('play1') # FIXME, if there is only one video?
            p2 = self.pipeline.get_by_name('play2')        
            if scroll_type ==  gtk.SCROLL_PAGE_FORWARD or scroll_type ==  gtk.SCROLL_PAGE_BACKWARD:
                print "Handling Seek"
                p1.seek(1.0, gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH,         
                        gst.SEEK_TYPE_SET,temp, gst.SEEK_TYPE_NONE,-1) 
                p2.seek(1.0, gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH,         
                        gst.SEEK_TYPE_SET,temp, gst.SEEK_TYPE_NONE,-1) 
            else:
                print "Handling SEEK after JUMP"
                p1.seek(1.0, gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH,         
                        gst.SEEK_TYPE_SET,self.jump, gst.SEEK_TYPE_NONE,-1) 
                p2.seek(1.0, gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH,         
                        gst.SEEK_TYPE_SET,self.jump, gst.SEEK_TYPE_NONE,-1) 
                if self.pipeline.get_state()[1]==gst.STATE_PAUSED:
                    print "Recovering PLAYING state"
                    self.pipeline.set_state(gst.STATE_PLAYING)
                self.seek_bar.disconnect(self.jump_id)
                self.jump_id=0
                self.correct=True




########################### BUTTON OPERATIONS ##################################

    def rec_preview(self,button):
        """ Initializing the pipe and starting the preview"""
        if self.status == self.GC_REC_INIT or self.status == self.GC_REC_STOP :

            timestamp = datetime.datetime.now().replace(microsecond=0).isoformat()
            os.makedirs(self.conf.get("basic","temp")+"/"+"gc"+timestamp)
            self.files = [ self.conf.get("basic","temp")+"/"+"gc"+timestamp+"/"+self.conf.get("track1","file"),
                           self.conf.get("basic","temp")+"/"+"gc"+timestamp+"/"+self.conf.get("track2","file")  ]
            pipestr2 = Pipeline.get(self.conf.get("basic","pipe"),self.files[0],self.files[1])
            self.pipeline = gst.parse_launch(pipestr2)
            self.valvula1 = self.pipeline.get_by_name('valvula1')
            if self.conf.get("basic","pipe") != "only2":
                self.valvula2 = self.pipeline.get_by_name('valvula2')
                if self.conf.get("basic","pipe") != "only" and self.conf.get("basic","pipe") != "audio":
                    self.valvula3 = self.pipeline.get_by_name('valvula3')
            self.vumetro = self.pipeline.get_by_name('vumeter')
            self.preview1 = self.pipeline.get_by_name('pre1')
            self.preview2 = self.pipeline.get_by_name('pre2')
            try:
                self.preview3 = self.pipeline.get_by_name('pre3')
            except:
                pass

        # CONFIGURE LEVEL FOR VUMETER
        
        #ESTABLISH GST CONNECTION
            self.gstreamer_communication(self.bus)

        #MODIFY BUTTONS
        self.tab2.set_sensitive(False)# FIXME make Player unavaliable
        self.start_button.set_sensitive(False)
        self.record_button.set_sensitive(True)
        self.stop_button.set_sensitive(True)

        #PREVIEW VIDEOS
        gst.info("Start Preview")
        print "Start Preview"
        self.status_s.set_text("Preview")
        self.status = self.GC_REC_PLAY
        # FIXME: poner a PAUSED (antes PLAYING)
        self.conf.open("conf.ini") # Refresh conf data
        self.pipeline.set_state(gst.STATE_PAUSED)

    def start_play(self,button):
        """Play the chosen MP"""
        #idea, cambiar a funcion de goberno do boton segundo o estado
        
        if self.status == self.GC_PLAY_INIT : 
        #CHECK FILES: 1 or 2 ok
            print "Checking files"
            video1 = self.chooser1 #COULD BE THAT video1 is FULL PATH ALREADY
            video2 = self.chooser2
            
            if (video1,video2) == (None,None) : #pasar a comprobacion matematica
                print "Ningun ficheiro seleccionado"
                choose_dialog = self.gui.get_object('atleastone')
                if choose_dialog.run() == gtk.RESPONSE_OK :
                    choose_dialog.hide()
                    return 0
            else:   # TAKE OUT CASE LOGIC
                print "Creando pipeline"
                if video1 == None :
                    print "Reproducir video2"
                    self.case = 2
                    pipestr = ( ' filesrc location='+  video2 +' ! decodebin2 ! xvimagesink name=playonly ')
                elif video2 == None :
                    print "Reproducir video1"
                    self.case = 1
                    time=100*1000*1000 # 100 ms
                    interval = str(time)    
                    pipestr = ( ' filesrc location='+ video1 +' ! tee name=audio ! queue ! ' 
                                ' decodebin2 ! xvimagesink name=play1 audio. ! queue ! decodebin2 ' 
                                ' ! level name=VUMETER message=true interval='+ interval +' ! autoaudiosink name=play3 ')   

                else:               
                    print "Reproducir multistream"
                    self.case = 3                    
                    time=100*1000*1000 # 100 ms
                    interval = str(time)        
                    pipestr = ( ' filesrc location='+ video1 +' ! ' 
                                ' decodebin2 name=audio ! queue ! xvimagesink name=play1 '
                                ' filesrc location='+ video2 +' ! decodebin2 ! queue ! xvimagesink name=play2 ' 
                                ' audio. ! queue ! '
                                ' level name=VUMETER message=true interval='+ interval +' ! autoaudiosink name=play3 ')
                                

                self.pipeline = gst.parse_launch(pipestr)
                # ESTABLISH GST CONNECTION
                self.gstreamer_communication(self.bus)             
                gst.info("Start Preview")
                print "Start Preview"
                
        else:
            gst.info("Resuming Preview")
            print "Resuming preview"
        self.status_s.set_text("Playing...")
        self.status = self.GC_PLAY_PLAY

        #MODIFY BUTTONS
        self.tab1.set_sensitive(False)
        self.start_button2.set_sensitive(False)
        self.pause_button2.set_sensitive(True)
        self.stop_button2.set_sensitive(True)
        #PLAY VIDEOS
        self.conf.open("conf.ini") # Refresh conf data
        self.pipeline.set_state(gst.STATE_PLAYING)   
              
    def record_rec(self,button):
        #inicia ou reinicia a gravacion
        self.status = self.GC_REC_REC
        self.tab2.set_sensitive(False)   
        self.record_button.set_sensitive(False) 
        gst.info("Start Record")
        print ("Start Record")
        self.status_s.set_text("Recording...")
        self.valvula1.set_property('drop', False)
        if self.conf.get("basic","pipe") != "only2":
            self.valvula2.set_property('drop', False)
            if self.conf.get("basic","pipe") != "only2" and self.conf.get("basic","pipe") != "audio":
                if self.conf.get("basic","pipe") != "improved":
                    self.valvula3.set_property('drop', False)
        # CONNECT CHRONO
        #self.chronometer()
        
    def pause_rec(self,button): # DELETE
        #pausa a gravacion, e posible reiniciala posteriormente sen sobreescribir
        self.status = self.GC_REC_PAUSE
        #self.tab2.set_sensitive(False)   
        self.record_button.set_sensitive(True)
        gst.info("Stop record")
        print "Record Paused"
        self.valvula1.set_property('drop', True)
        if self.conf.get("basic","pipe") != "only2":
            self.valvula2.set_property('drop', True)
            if self.conf.get("basic","pipe") != "only" and self.conf.get("basic","pipe") != "audio":
                self.valvula3.set_property('drop', True)
        #comando1 = "cp " + self.files[0] + " videos/video1.mpeg"
        #comando2 = "cp " + self.files[1] + " videos/video2.mpeg"
        #comando2 = "ffmpeg -i " + self.files[1] + " -vcodec copy -acodec copy -y " + " videos/video2.mpeg"
        #os.system(comando1)
        #os.system(comando2)

    def stop_rec(self,button):
        # para a gravacion e a pipeline
        # self.valvula1.set_property('drop', True)
        # self.valvula2.set_property('drop', True)
        # if self.conf.get("basic","pipe") != "only2":
        #    self.valvula3.set_property('drop', True)
        self.GC_REC_PLAY
  
        self.tab2.set_sensitive(True)
        self.start_button.set_sensitive(True)
        self.record_button.set_sensitive(False)
        self.stop_button.set_sensitive(False)      
        gst.info("Stop record")
        self.status_s.set_text("Iddle")
        print "Record Stopped"       
        
        if self.status == self.GC_REC_REC:
            self.status = self.GC_REC_STOP
            # SEND EOS
            self.pipeline.send_event(gst.event_new_eos())      

            # XML
            print os.path.dirname(self.files[0])
            novo = Mediapackage(tmp=os.path.dirname(self.files[0]))
            for meta in dcterms:
                entry = self.gui.get_object(meta)
                if entry != None:
                    text = entry.get_text()
                    if text != None and text != "" and text != insert_message: # get proper sintax
                        novo.metadata_episode[meta]=text
                    if meta == "title" and text == insert_message:
                        novo.metadata_episode[meta]="Saved on: "+datetime.datetime.now().replace(microsecond=0).isoformat()
            novo.metadata_episode["identifier"]=str(uuid.uuid4())
            novo.add_track(self.files[0],"presenter")
            if self.conf.get("basic","pipe") != "only2": 
                novo.add_track(self.files[1],"presentation")
            novo.episode="episode.xml"
            novo.add_catalog("episode.xml","dublincore/episode")
            novo.create_xml()
            self.status_disk.set_text(self.get_free_space(self.conf.get("basic","temp")))

        else:
            #borrar directorio temporal
            shutil.rmtree(os.path.dirname(self.files[0]))
            self.status = self.GC_REC_STOP
            self.pipeline.set_state(gst.STATE_NULL)        
       
    def pause_play(self,button):
        #pausa a reproducion
        self.tab1.set_sensitive(False)
        self.pause_button2.set_sensitive(False)
        self.start_button2.set_sensitive(True)              
        self.status = self.GC_PLAY_PAUSE
        self.pipeline.set_state(gst.STATE_PAUSED)        
        gst.info("Pause")
        print "Paused"
        self.status_s.set_text("Paused")

    
    def stop_play(self,button):
        #para a reproducion completamente
        self.tab1.set_sensitive(True)
        self.pause_button2.set_sensitive(False)
        self.stop_button2.set_sensitive(False)        
        self.start_button2.set_sensitive(True)
        self.status = self.GC_PLAY_INIT
        self.pipeline.set_state(gst.STATE_NULL)        
        self.seek_bar.set_value(0)
        self.duration=0
        gst.info("Stop playing")
        print "Stopped"
        self.status_s.set_text("Iddle")

########################### MediaPackage Handle ###########################3

    def rec_save(self,button):
        """Save a new Mediapackage from the recording"""
        #CONSIDER close all text entries
        asigned = False
        novo = Mediapackage()
        self.save_dialog.set_current_name(self.conf.get("basic","zip"))
        if self.save_dialog.run() == 1 :            
            name = self.save_dialog.get_filename()            
            print "Gravado en " + str(name)
            if str(name) != "None" : asigned = True
        else :
            print "Cancel pressed in rec_save" 
        self.save_dialog.hide()

        if asigned :
            for meta in dcterms:
                entry = self.gui.get_object(meta)
                if entry != None:
                    text = entry.get_text()
                    if text != None and text != "" and text != insert_message: # get proper sintax
                        novo.metadata_episode[meta]=text
                    if meta == "title" and text == insert_message:
                        novo.metadata_episode[meta] = "Saved on: "+datetime.datetime.now().replace(microsecond=0).isoformat()
                        
            novo.metadata_episode["identifier"]=str(uuid.uuid4())
            novo.add_track(self.files[0],"presenter")
            if self.conf.get("basic","pipe") != "only2":
                novo.add_track(self.files[1],"presentation")
            novo.episode="episode.xml"
            #CONSIDER clear old episode
            novo.add_catalog("episode.xml","dublincore/episode")
            novo.create_mediapackage(name)
        else: print "Non se indicou arquivo"

    def rec_ingest(self,button):
        #FIXME comprobar se esta gravado, a partir
        asigned = False
        novo = Mediapackage()
        self.save_dialog.set_current_name(self.conf.get("basic","zip"))     
        if self.save_dialog.run() == 1 :            
            name = self.save_dialog.get_filename()            
            print "Gravado en " + str(name)
            if str(name) != "None" : asigned = True
        else :
            print "Cancel pressed in rec_save" 
        self.save_dialog.hide()

        if asigned :
            for meta in dcterms:
                entry = self.gui.get_object(meta)
                if entry != None:
                    text = entry.get_text()
                    if text != None and text != "" and text != insert_message: # get proper sintax
                        novo.metadata_episode[meta]=text
                        
            novo.metadata_episode["identifier"]=str(uuid.uuid4())
            novo.add_track(self.files[0],"presenter")
            novo.add_track(self.files[1],"presentation")
            novo.episode="episode.xml"
            #CONSIDER clear old episode
            novo.add_catalog("episode.xml","dublincore/episode")
            novo.create_mediapackage(name)
            c=self.conf.get_section("ingest")
            novo.send_zip(name,c["host"],c["username"],c["password"],c["workflow"])
        else: print "Non se indicou arquivo"

    def rec_ingest2(self,button):
        asigned = False
        self.save_dialog.set_current_name(self.conf.get("basic","zip"))     
        if self.save_dialog.run() == 1 :            
            name = self.save_dialog.get_filename()            
            print "Gravado en " + str(name)
            if str(name) != "None" : asigned = True
        else :
            print "Cancel pressed in rec_save" 
        self.save_dialog.hide()

        if asigned :
            c=self.conf.get_section("ingest")
            self.mp.send_zip(name,c["host"],c["username"],c["password"],c["workflow"])
        else: print "Non se indicou arquivo"


    def play_open(self,button):
        "Play both videofiles from a MH Mediapackage and show some metadata"
        print "Playing MP"
        if self.zip_dialog.run() == 1 :
            print "Choosing file"
            self.mp = Mediapackage()
            self.mp.get_mediapackage(self.zip_dialog.get_filename())            
            self.zip_dialog.hide()                        
            self.chooser1 = self.mp.tmp+"/"+os.path.basename(self.mp.tracks[0].url) #cambiar barra de sistema
            if len(self.mp.tracks) >= 2:
                self.chooser2 = self.mp.tmp+"/"+os.path.basename(self.mp.tracks[1].url)# OJO con el Basename
            else:
                self.chooser2 = None
            # crear todos os metadatos en tempo real
            table = self.infobox
            for child in self.infobox.get_children():
                table.remove(child)            
            table.resize(1,2)
            row=1
            #FIX get into a new function to use on rec_play too
            combo = gtk.combo_box_new_text()
            #lista = gtk.ListStore(str)

            for meta in dcterms:
                if self.mp.metadata_episode[meta] != None:
                    t=gtk.Label(metadata[meta])
                    t.set_justify(gtk.JUSTIFY_LEFT)
                    t.set_alignment(0,0)
                    t.set_width_chars(15)
                    e=gtk.EventBox()
                    d=gtk.Label(self.mp.metadata_episode[meta])
                    d.set_justify(gtk.JUSTIFY_LEFT)
                    d.set_alignment(0,0)
                    d.set_line_wrap(True)
                    #FIX, establecer un ancho de widget porcentual para que realice ben o salto de linha
                    e.add(d)
                    e.add_events(gtk.gdk.BUTTON_PRESS_MASK)#filtrar so o doble click
                    if meta != "created":
                        e.connect("button-press-event",self.edit_meta)# CONSIDER connect Intro to eventbox notto entry
                    else:
                        e.connect("button-press-event",self.edit_date)# CONSIDER connect Intro to eventbox notto entry
                    table.attach(t,0,1,row-1,row,False,False,0,0)
                    table.attach(e,1,2,row-1,row,gtk.EXPAND|gtk.FILL,False,0,0)
                    t.show()
                    e.show()
                    d.show()
                    #print "Metadata "+meta.capitalize()+" attached: "+str(self.mp.metadata_episode[meta])
                    row=row+1
                else:
                    combo.append_text(meta)
                    #lista.append([meta])
                    #FIX configurar o combobox apropiadamente para que non faga cousas raras
            # CONSIDER function for comobox addmeta

            addbutton = gtk.Button("Add new metadata")
            addbutton.connect("clicked", self.add_meta, combo)
            table.attach(combo,0,1,row-1,row,False,False,0,0)
            table.attach(addbutton,1,2,row-1,row,False,False,0,0)
            combo.show()
            addbutton.show()
            # FIX!!! modificar para que elimine restos ao abrir varios arquivos seguidos
        
            self.expanderp.set_sensitive(True)
            self.expanderp.set_expanded(True)            
        else: 
            print "No file selected"
            self.zip_dialog.hide()

    def play_save(self,button):
        """Save a modified Mediapackage in a new zip"""
        #CONSIDER close all text entries
        asigned = False
        novo = Mediapackage()
        self.save_dialog.set_current_name(self.conf.get("basic","zip"))     
        if self.save_dialog.run() == 1 :            
            name = self.save_dialog.get_filename()            
            print "Gravado en " + str(name)
            if str(name) != "None" : asigned = True
        else :
            print "Cancel pressed in play_save" 
        self.save_dialog.hide()

        if asigned :
            col=1
            for child in reversed(self.infobox.get_children()):
                if col == 1 and type(child) is gtk.Label:
                    meta=metadata[child.get_text()]
                    col == 2
                elif type(child) is gtk.EventBox:
                    text = child.get_children()[0].get_text()
                    if text != insert_message and text != "":
                        novo.metadata_episode[meta]=child.get_children()[0].get_text() #label in an event box
                        #print meta+"  "+child.get_children()[0].get_text()
                    col == 1

            novo.add_track(self.chooser1,"presenter")# FIXME add /source and take it out from MP
            if self.chooser2 != None:
                novo.add_track(self.chooser2,"presentation")
            novo.episode="episode.xml"
            novo.add_catalog("episode.xml","dublincore/episode")#BF metadata/dublincore            
            novo.create_mediapackage(name)
        else: print "Non se indicou arquivo"


################################# METADATA #######################################3

    def edit_meta(self, ebox, signal):
        if signal.type == gtk.gdk._2BUTTON_PRESS:
            print "OPENing: changing to gtkEntry"
            content=ebox.get_children()[0]
            text= content.get_text()            
            ebox.remove(content)
            f= gtk.Entry()    
            f.set_text(text)
            f.connect("activate",self.no_edit_meta,ebox)
            ebox.add(f)
            f.show()

    def edit_date(self, ebox, signal):
        # REVISAR!!!!!!
        if signal.type == gtk.gdk._2BUTTON_PRESS:
            print "OPENing: showing calendar"
            content=ebox.get_children()[0]
            text= content.get_text() #have data
            if text != insert_message and text != "":
                date=datetime.datetime.strptime(text,"%Y-%m-%dT%H:%M:%S") # change model
            v = CalendarWindow()
            v.run()
            print v.date
            if v.date != None:
                content.set_text(v.date.isoformat())


    def no_edit_meta(self, content, ebox):
        print "CLOSING and changing to gtkLabel"
        text= content.get_text()            
        ebox.remove(content)
        d=gtk.Label()
        d.set_text(text)
        d.set_justify(gtk.JUSTIFY_LEFT)
        d.set_alignment(0,0)
        d.set_line_wrap(True)
        ebox.add(d)
        d.show()
    
    def add_meta(self, button, combo):
        #FIX 1: Retirar da combobox os novos metadata
        #FIX 2: Recolocar novos metadata e combobox
        #FIX 3: Engadir varios metadata

        name = combo.get_active_text()
        table = self.infobox
        row=table.get_property('n-rows')
        table.resize(row+1,2)
        table.remove(combo)
        combo.destroy()
        used = []
        for child in reversed(self.infobox.get_children()):
            if type(child) is gtk.Button:
                table.remove(child)
                child.destroy()
                #table.attach(child,1,2,row,row+1,False,False,0,0)
            elif type(child) is gtk.Label:
                    used.append(metadata[child.get_text()]) #engade LOW

        if name in dcterms: #CHANGE por meta == None??
                t=gtk.Label(metadata[name])
                t.set_justify(gtk.JUSTIFY_LEFT)
                t.set_alignment(0,0)
                t.set_width_chars(15)
                e=gtk.EventBox()
                d=gtk.Label(insert_message)
                d.set_justify(gtk.JUSTIFY_LEFT)
                d.set_alignment(0,0)
                d.set_line_wrap(True)
            #FIX, establecer un ancho de widget porcentual para que realice ben o salto de linha
                e.add(d)
                e.add_events(gtk.gdk.BUTTON_PRESS_MASK)#filtrar so o doble click
                if name != "created":
                    e.connect("button-press-event",self.edit_meta)# CONSIDER connect Intro to eventbox notto entry
                else:
                    e.connect("button-press-event",self.edit_date)# CONSIDER connect Intro to eventbox notto entry
                table.attach(t,0,1,row-1,row,False,False,0,0)
                table.attach(e,1,2,row-1,row,gtk.EXPAND|gtk.FILL,False,0,0)

        combo2 = gtk.combo_box_new_text()
        for meta in dcterms:
            if not meta in used and meta != name:                
                combo2.append_text(meta)    
        addbutton = gtk.Button("Add new metadata")
        addbutton.connect("clicked", self.add_meta, combo2)
        table.attach(addbutton,1,2,row,row+1,False,False,0,0)
        table.attach(combo2,0,1,row,row+1,False,False,0,0)    
        #addbutton.show()
        #combo2.show()
        #t.show()
        #e.show()
        #d.show()
        self.window.show_all()
        row=row+1


    def get_state(self, timeout=1):
        return self.pipeline.get_state(timeout=timeout)

################################# CONTROL ###############################

    def preferences(self,button):
        # while self.conf_dialog.run() =! gtk.RESPONSE_OK:
        self.populate_conf()
        response = self.conf_dialog.run()        
        if response > 1:
            print "Galicaster Configuration"
            self.update_conf()
            self.conf_dialog.hide()
            # aply changes and hide
        elif response == 1:
            # just apply changes
            print "Must apply changes and keep it open"
            self.update_conf()
            self.conf_dialog.hide()
        else:       
            print "Cancel Configuration"
            self.conf_dialog.hide()

    def populate_conf(self):
        for a in basic:
            entry = self.gui.get_object(a)
            if type(entry) is gtk.FileChooserButton:
                print "Getting temp folder"                
                entry.set_current_folder(self.conf.get("basic",a))
            # elif type(entry) is gtk.ComboBox:
            elif type(entry) is gtk.ListStore: 
                print "Getting avaliable pipelines"
                print Pipeline.getPipes()   
                for i,b in enumerate(Pipeline.getPipes()):                    
                    #entry.append((b,))
                    if b == self.conf.get("basic",a):
                        print "Activando pipe "+b                                
            else:
                entry.set_text(self.conf.get("basic",a))
        for a in ingest:
            entry = self.gui.get_object(a)
            entry.set_text(self.conf.get("ingest",a))

    def update_conf(self):
        for a in basic:
            entry = self.gui.get_object(a)
            if type(entry) is gtk.FileChooserButton:
                print "Setting temp folder"
                self.conf.set("basic",a,entry.get_current_folder())
            elif type(entry) is gtk.ComboBox:
                print "Setting avaliable pipelines"
                self.conf.set("basic",a,entry.get_active_text())
            else:
                self.conf.set("basic",a,entry.get_text())
        for a in ingest:
            entry = self.gui.get_object(a)
            self.conf.set("ingest",a,entry.get_text())

        entry = self.gui.get_object("playershift")
        button = entry.get_children()[0].get_children()[0].get_label()
        self.conf.set("screen","player",button.lower())
        entry = self.gui.get_object("recordshift")
        button = entry.get_children()[0].get_children()[0].get_label()
        self.conf.set("screen","recorder",button.lower())

        self.conf.update()

    def quit(self,button):
        #sae do programa e cerra todas as xanelas
        if self.quit_dialog.run() == gtk.RESPONSE_OK :
            print "Quit Galicaster"
            if self.status > 3 : 
                print "Quit type 1 "
                self.status = self.GC_QUIT   
                self.pipeline.set_state(gst.STATE_NULL)
                self.quit_dialog.destroy()
                gtk.main_quit()
            else : 
                print " Quit type 2 "
                self.status = self.GC_QUIT   
                gtk.main_quit()
            gst.info("free player")            
        else : 
            print "Cancel Quit"
            self.quit_dialog.hide()

    def change_function(self,a,b,c):
        #FIXME bloquear cambios de funcion invalidos (funcion desactivada)
        print "Function changing"

        if self.function == self.GC_RECORDER :
            print "Changing to player"
            self.status =  self.GC_PLAY_INIT # just for the first time
            self.function = self.GC_PLAYER           
        elif self.function == self.GC_PLAYER :
            print "Changing to recorder"
            self.status =  self.GC_REC_INIT # just for the first time
            self.function = self.GC_RECORDER

    def change_function2(self,menu):
        #FIXME bloquear cambios de funcion invalidos (funcion desactivada)
        label = menu.get_label()
        if label == "Player":
            print "Changing to player"
            self.status =  self.GC_PLAY_INIT # just for the first time
            self.function = self.GC_PLAYER
        else:
            print "Changing to recorder"
            self.status =  self.GC_REC_INIT # just for the first time
            self.function = self.GC_RECORDER

        self.status_f.set_text(label)
        self.status_s.set_text("Iddle")
        self.function_area.set_current_page(self.function)


    def on_toggle(self, button, signal):
        box = button.get_children()[0]
        box.reorder_child(box.get_children()[1],1)
        box.reorder_child(box.get_children()[0],2)

    def shift_videos(self,signal):
        if self.function == self.GC_RECORDER :
           self.on_toggle(self.shifter2, None)  
           self.update_conf()
        elif self.function == self.GC_PLAYER :
           self.on_toggle(self.shifter1, None)
           self.update_conf()

    def get_free_space(self, directorio):
        stats = os.statvfs(directorio)
        freespace=(stats.f_bsize * stats.f_bavail)
        return "Free Space: "+self.make_human_readable(freespace)

    def make_human_readable(self,num):
        """Generates human readable string for a number.
        Returns: A string form of the number using size abbreviations (KB, MB, etc.) """
        i = 0
        while i+1 < len(EXP_STRINGS) and num >= (2 ** EXP_STRINGS[i+1][0]):
            i += 1
            rounded_val = round(float(num) / 2 ** EXP_STRINGS[i][0], 2)
        return '%s %s' % (rounded_val, EXP_STRINGS[i][1])

    def chronometer(self):
        self.chrono +=1
        self.status_t.set_text=time.strftime('%H:%M:%S', time.gmtime(self.chrono))
        time.sleep(1)
        return self.chronometer()
######################## VIDEOWIDGET RELATED ###########################


class VideoWidget(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.imagesink = None
        #self.unset_flags(gtk.DOUBLE_BUFFERED)

    def do_expose_event(self, event):
        print "do_expose_event"
        if self.imagesink:
            self.imagesink.expose()
            return False
        else:
            return True

    def set_sink(self, sink):
        print "set_sink"
        assert self.window.xid #EMITE UN ERROR AQUI, cause window id is not set yet
        self.imagesink = sink
        self.imagesink.set_xwindow_id(self.window.xid)
        print self.window.xid

#-------------------------------------------------------------------------------------------------
        
def main(args):
    def usage():
        sys.stderr.write("usage: %s\n" % args[0])
        return 1

    # Need to register our derived widget types -as gtk types -
    # for implicit event handlers to get called. 
    gobject.type_register(VideoWidget)

    if len(args) != 1:
        return usage()

    v = Galicaster()
    gtk.main()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv)) 
