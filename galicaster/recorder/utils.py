# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/utils
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


import logging

import gst
import time
import thread



log = logging.getLogger()

class Switcher(gst.Bin):

    def __init__(self, name, device, image=None, driver_type="v4lsrc"): 

        gst.Bin.__init__(self, name)
        self.eph_error = False
        self.let_pass = False
        self.removing = False

        self.devicepath = device
        self.driver_type = driver_type

        # Create elements
        self.image = gst.element_factory_make('videotestsrc', 'image')
        #for sending eos
        self.src1 = self.image


        self.device = gst.element_factory_make(self.driver_type, 'device')
        scale = gst.element_factory_make('videoscale')      
        self.selector = gst.element_factory_make('input-selector', 'selector')
        q0 = gst.element_factory_make('queue', 'q2image')
        q1 = gst.element_factory_make('queue', 'q2device')
        qs = gst.element_factory_make('queue', 'q2selector')
        qn = gst.element_factory_make('queue', 'q2identity')
        self.identity = gst.element_factory_make('identity', 'idprobe')
        color = gst.element_factory_make('ffmpegcolorspace', 'colordevice')

        caps = gst.element_factory_make('capsfilter', 'capsdevice')  
        caps2 = gst.element_factory_make('capsfilter', 'capsimage')
        caps3 = gst.element_factory_make('capsfilter', 'capsselector')
        text = gst.element_factory_make('textoverlay', 'textimage')

        # Set properties
        self.device.set_property('device', device)
        self.image.set_property('is-live', True)
        self.image.set_property('pattern', "blue")
        text.set_property('text', "No VGA Signal")
        text.set_property('valignment', 1)
        text.set_property('font-desc', "arial,50px")

        q0.set_property('max-size-buffers', 1)
        q1.set_property('max-size-buffers', 1)
        qn.set_property('max-size-buffers', 1)

        # CAPS
        filtre = gst.caps_from_string("video/x-raw-yuv,format=\(fourcc\)YUY2,width=800,height=600,framerate=(fraction)25/1") 
        filtre2 = gst.caps_from_string("video/x-raw-yuv,format=\(fourcc\)YUY2,width=1024,height=786,framerate=(fraction)25/1")

        caps.set_property('caps', filtre)
        caps2.set_property('caps', filtre)
        caps3.set_property('caps', filtre)

        # Add elements
        self.add(self.image, caps2, text, scale, q0, 
                 self.device, self.identity, qn, caps, color, q1,
                 self.selector, qs, caps3)

        # Link elements and set ghostpad
        gst.element_link_many(self.image, caps2, text, scale, q0)
        gst.element_link_many(self.device, self.identity, qn, caps, color, q1)

        q0.link(self.selector)
        q1.link(self.selector)
        gst.element_link_many(self.selector, caps3, qs)
        self.add_pad(gst.GhostPad('src', qs.get_pad('src')))

        # Set active pad
        if self.checking():
            self.selector.set_property('active-pad', 
                                       self.selector.get_pad('sink1'))
        else:
            self.selector.set_property('active-pad', 
                                       self.selector.get_pad('sink0'))
            self.eph_error = True
            self.thread_id=thread.start_new_thread(self.polling_thread, ())
            self.device.set_state(gst.STATE_NULL)
            self.remove(self.device)  #IDEA remove it when at NULL

      # Set probe
        pad = self.identity.get_static_pad("src")
        pad.add_event_probe(self.probe)
        
    def let_eos_pass(self):
        """
        Change the variable to let the final EOS event pass
        """
        self.let_pass = True

    def checking(self):
        pipe = gst.Pipeline('check')
        device = gst.element_factory_make(self.driver_type, 'check-device')
        device.set_property('device', self.devicepath)
        sink = gst.element_factory_make('fakesink', 'fake')
        pipe.add(device, sink)
        device.link(sink)
        # run pipeline
        pipe.set_state(gst.STATE_PAUSED)
        pipe.set_state(gst.STATE_PLAYING)
        state = pipe.get_state()
        if state[0] != gst.STATE_CHANGE_FAILURE:
            pipe.set_state(gst.STATE_NULL)
            return True
        return False

    def polling_thread(self):
        log.debug("Initializing polling")
        thread_id = self.thread_id
        pipe = gst.Pipeline('poll')
        device = gst.element_factory_make(self.driver_type, 'polling-device')
        device.set_property('device', self.devicepath)
        sink = gst.element_factory_make('fakesink', 'fake')
        pipe.add(device, sink)
        device.link(sink)
        bucle = 0
        while thread_id == self.thread_id:
            if self.removing == True:
                self.removing = False
                self.device.set_state(gst.STATE_NULL)
                self.remove(self.device)
            pipe.set_state(gst.STATE_PAUSED) # FIXME assert if a gtk.gdk is neccesary
            pipe.set_state(gst.STATE_PLAYING)
            state = pipe.get_state()
            if state[0] != gst.STATE_CHANGE_FAILURE:
                log.debug("VGA active again")
                pipe.set_state(gst.STATE_NULL)
                self.thread_id = None
                self.reset_vga()
            else:
                pipe.set_state(gst.STATE_NULL)
                time.sleep(0.8)
            bucle += 1


    def probe(self, pad, event):       
        if not self.let_pass:
            if event.type == gst.EVENT_EOS and not self.eph_error:
                log.debug("EOS Received")
                self.switch("sink0")
                self.eph_error = True
                # self.device.set_state(gst.STATE_NULL)
                self.thread_id = thread.start_new_thread(self.polling_thread,())
                log.debug("Epiphan BROKEN: Switching Epiphan to Background")
                return False
            if event.type == gst.EVENT_NEWSEGMENT and self.eph_error:
                log.debug("NEW SEGMENT Received")
                
                self.switch("sink1")
                self.eph_error = False
                log.debug('Epiphan RECOVERED: Switching back to Epiphan')
                return False # Sure about this?
        else:
            return True # the eos keeps going till the sink

    def switch(self, padname):
        log.debug("Switching to: "+padname)
        stop_time = self.selector.emit('block')
        newpad = self.selector.get_static_pad(padname)
        # start_time = newpad.get_property('running-time')
        self.selector.emit('switch', newpad, -1, -1)
        self.removing = True

    def switch2(self): # TODO review this function and delete if unnecessary
        padname = self.selector.get_property('active-pad').get_name()
        if padname == "sink0":
            newpad = self.selector.get_static_pad("sink1")
        else:
            newpad = self.selector.get_static_pad("sink0")

        self.selector.emit('block')            
        self.selector.emit('switch', newpad, -1, -1)

    def reset_vga(self):
        log.debug("Resetting Epiphan")
        
        if self.get_by_name('device') != None :
            self.device.set_state(gst.STATE_NULL) 
            self.remove(self.device)
        del self.device
        self.device = gst.element_factory_make(self.driver_type, 'device')
        self.device.set_property('device', self.devicepath)
        self.add(self.device)
        self.device.link(self.identity)
        self.device.set_state(gst.STATE_PLAYING)
        self.identity.get_state() 

    def reset2(self):
        self.device = gst.element_factory_make(self.driver_type, 'device')
        self.device.set_property('device', self.devicepath)
        self.add(self.device)
        self.device.link(self.identity)
        self.device.set_state(gst.STATE_PLAYING)
        self.identity.get_state()

    def send_event_to_src(self, event): # IDEA made a common for all our bins
        self.let_eos_pass()
        self.device.send_event(event)    
        self.src1.send_event(event)

        
