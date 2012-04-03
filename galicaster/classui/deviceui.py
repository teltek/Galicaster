# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/classui/deviceui
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


import gobject
import os
import re
from os import path
import gtk
import pango
import galicaster.recorder.pipeline as bins

from galicaster import context


flavors = [ "presenter", "presentation", "other"]
devices = [ "vga2usb", "hauppauge", "v4l2", "pulse"]
track = [ "name", "type", "flavor", "location", "file", "active" ]

class DeviceUI(gtk.Widget):
    """
    Handle a pop up configuration editor for devices
    """
    __gtype_name__ = 'DeviceUI'
    
    def __init__(self,package = None, parent = None):
        guifile = path.join(path.dirname(path.abspath(__file__)),'device.glade')
	#guifile = "galicaster/ui/conf.glade" #FIXME relative route
        self.gui = gtk.Builder()
        self.gui.add_from_file(guifile)
        self.gui.connect_signals(self)

        self.conf=context.get_conf()
        
        dialog = self.gui.get_object("confdialog")
        if parent != None:
            dialog.set_transient_for(parent.get_toplevel())
 
        self.populate_conf()
        dialog.show_all()
        response = dialog.run()        
        if response > 1: # FIXME, set Apply Button
            self.update_actives()
        elif response == 1:
            self.update_actives()
        else:       
            print "Cancel Configuration"
        dialog.destroy()

    def populate_conf(self): # FIXME, look for another way to do it, scalable

        """
        Fill the table with devices
        """        

        
        table  = self.gui.get_object("device_table")
        tabs  = self.gui.get_object("notebook1")
        for child in table.get_children():
            table.remove(child) #FIXME maybe change the glade to avoid removing any widget

        def device_label(name):
            label=gtk.Label(name)
            label.set_justify(gtk.JUSTIFY_LEFT)
            label.set_alignment(0,0.5)
            label.set_width_chars(20)
            label.set_ellipsize(pango.ELLIPSIZE_END)
            return label


        b = gtk.HBox(False,0)
        b.set_name("Titulo")
        d = device_label("Devices")
        d.set_width_chars(22)
        c =  gtk.Label("Active")
        c.set_alignment(0.5,0.5)
        c.set_width_chars(6)
        b.pack_start(d, False, False)
        b.pack_start(c, False, False)
        table.pack_start(b)

        b2 = gtk.HBox(False,5)
        n = gtk.Button("New Device...")
        n.connect("clicked",self.show_new_device)
        n2 = gtk.Button("Delete Device")
        n2.connect("clicked",self.delete_device)
        b2.pack_start(n)
        b2.pack_start(n2)
        n.show()
        n2.show()
        b2.show()
        table.pack_end(b2)

        for section in self.conf.conf.sections(): # FIXME conf.conf, crear algun tipo de interface
            if section.count("track"):
                b = gtk.HBox(False,0)
                b.set_name(section)
                b.set_spacing(30)

                d = device_label(self.conf.get(section,"name"))
                c =  gtk.CheckButton(None,False)
                c.set_mode(True)
                c.set_alignment(0.5,0.5)
                c.set_use_stock(True)
                
                active = self.conf.get(section,"active")
                if active == "True":
                    c.set_active(True)
                elif active == "False":
                    c.set_active(False)
                else:
                    pass # TODO raisa a exception or log debug

                a = gtk.Button("Advanced...") # TODO connect with name-advanced                 
                a.connect("clicked",self.show_advanced,section,self.conf.get(section,"name"))
                b.pack_start(d)
                b.pack_start(c)
                b.pack_start(a)
                if c.get_active():
                    table.pack_start(b)
                else:
                    table.pack_end(b)
                d.show()
                c.show()
                a.show()
                b.show()
                

        self.update_screen()

        tabs.connect("switch-page",self.update_screen)
        for screen in ["left","right"]:
            entry = self.gui.get_object(screen)
            entry.connect("changed",self.parse_screen)
        table.show()


    def update_screen(self,element=None, page = None, number = None):

        if number in [None, 1]:
            for screen in ["left","right"]:
                entry = self.gui.get_object(screen)
                devices = self.get_actives2(self.gui.get_object("device_table"),True)
                self.set_model_from_list(entry,devices)
                try:
                    entry.set_active(devices.index(self.conf.get("screen",screen)))
                except:
                    entry.set_active(0)
        elif number == 0 :
            r = self.gui.get_object("right").get_active_text()        
            l = self.gui.get_object("left").get_active_text()
            self.conf.set("screen","left",l)
            self.conf.set("screen","right",r)


    def set_model_from_list (self, cb, items):
        """Setup a ComboBox based on a list of strings."""           
        cb.clear()
        model = gtk.ListStore(str)
        for i in items:
            model.append([i])
        cb.set_model(model)
        cell = gtk.CellRendererText()
        cb.pack_start(cell, True)
        cb.add_attribute(cell, 'text', 0)
        

    def update_actives(self):
        table  = self.gui.get_object("device_table")
        actives = []

        for device in table.get_children():
            if device.name != "Titulo":
                for child in device.get_children():
                    if type(child) == gtk.CheckButton:
                        if child.get_active():
                            self.conf.set(device.name,"active","True")
                            actives.append(self.conf.get(device.name,"name"))
                        else:
                            self.conf.set(device.name,"active","False")

        r = self.gui.get_object("right").get_active_text()        
        l = self.gui.get_object("left").get_active_text()

        # check if an unactive device its selected for an screen

        if r in actives:      
            self.conf.set("screen","right",r)
        else: 
            self.conf.set("screen","right","None")

        if l in actives:      
            self.conf.set("screen","left",l)
        else: 
            self.conf.set("screen","left","None")

        self.conf.update()

    def parse_screen(self,element,event=None):

        r = self.gui.get_object("right")
        l = self.gui.get_object("left")
        
        if type(element) == gtk.Button: #shift screens
            sl=l.get_active()
            sr=r.get_active()
            l.set_active(sr)
            r.set_active(sl)
            return True
            
        elif type(element) == gtk.ComboBox:

            if r == element and l.get_active_text() == r.get_active_text():
                l.set_active(0)
            elif l == element and l.get_active_text() == r.get_active_text():
                r.set_active(0)
            return True
  


    def get_actives(self,table,withnone):
        """
        Devolve unha lista dos activos - do UI -  encabezados por None
        """

        listado = []
        if withnone :
            listado = ["None"]    

        for device in table.get_children():
            for child in device.get_children():
                if type(child) == gtk.CheckButton:
                    if child.get_active():
                        listado.append(device.name)                            
        return listado     

    
    def get_actives2(self,table,withnone):
        """
        Como actives 1 pero comproba se son pulse
        """
        actives = []
        listado = []
        if withnone :
            listado = ["None"]
    

        for device in table.get_children():
            if device.name != "Titulo":
                for child in device.get_children():
                    if type(child) == gtk.CheckButton:
                        if child.get_active():
                            actives.append(device.name)
                            
        for device in actives:    
            if self.conf.get(device,"device") != "pulse":
                listado.append(self.conf.get(device,"name"))
        return listado       

    def show_advanced(self,button,section,name): # FIXME section and name arent both necessary
        
        parent = button.get_parent()        
        # if SAVE clicked, update all the options but active

        guifile = path.join(path.dirname(path.abspath(__file__)),'advanced_device.glade')
        builder = gtk.Builder()
        builder.add_from_file(guifile)
 
        dialog = builder.get_object("advanced_dialog")
        table  = builder.get_object("deviceoptions")
        devicename = builder.get_object("devicename")

        if parent != None:
            dialog.set_transient_for(parent.get_toplevel())

        options = ["name","device","flavor","location","file","caps","vumeter","videocrop-left","videocrop-right"]
        show = ["Name: ", "Type: ", "Flavor: ", "Location: ", "File name: ", "Capabilities: ", "Main microphone: ", "Left crop: ", "Right crop: " ]
        toshow=dict(zip(options,show))        

        devicename.set_label(name) # Get the name from other place

        for child in table.get_children():
            table.remove(child) #FIXME maybe change the glade to avoid removing any widget
        
        table.resize(1,2) 
        row = 1


        for key in toshow.keys():
            
            if self.conf.conf.has_option(section,key):
                t=gtk.Label(toshow[key])
                t.set_justify(gtk.JUSTIFY_LEFT)
                t.set_alignment(0,0)
                t.set_width_chars(20)

                if key in ["device","flavor","location"]: #combobox
                    d = gtk.ComboBox()
                    d.set_name(key)
                    if key == "device":
                        self.set_model_from_list(d,devices)
                        try:
                            d.set_active(devices.index(self.conf.get(section,key)))
                        except:
                            pass
                    elif key == "flavor":
                        self.set_model_from_list(d,flavors)
                        try:
                            d.set_active(flavors.index(self.conf.get(section,key)))
                        except:
                            pass
                    elif key == "location":
                        videos = [path.join('/dev',f) for f in os.listdir('/dev') if re.match('video*', f)]
                        for custom in ["haucamera","screen", "webcam"]:
                            if custom in os.listdir('/dev'):
                                videos.append(path.join('/dev',custom))
                        audios = os.popen('pactl list | grep "Source" -A 3 | grep "Name"').read().replace("Name:","").split()
                        locations = audios
                        for v in videos:
                            locations.append(v)                      

                        self.set_model_from_list(d,locations)
                        try:
                            d.set_active(locations.index(self.conf.get(section,key)))
                        except:
                            pass
                        
                elif key in ["name","file","caps","videocrop-left","videocrop-right"]:#entry
                    d=gtk.Entry()
                    d.set_text(self.conf.get(section,key))
                    d.set_name(key)
                elif key == "vumeter": #checkbutton
                    d=gtk.CheckButton(None, False)
                    d.set_name(key)
                    #c.set_alignment(0.5,0.5)
                    #c.set_use_stock(True)
                    
                table.attach(t,0,1,row-1,row,False,False,0,0)
                table.attach(d,1,2,row-1,row,gtk.FILL,False,0,0)
                t.show()
                d.show()
                row=row+1 
                
            
 
        response = dialog.run()        
        if response >= 1: # FIXME, set Apply Button
            print "TODO Save Advance Configuration"
            changes = {}
            for child in table.get_children(): # TODO copy this to other handlings of Devices
                if child.name in options:
                    if type(child) == gtk.ComboBox:
                        changes[child.name] = child.get_active_text()
                    elif type(child) == gtk.Entry:
                        changes[child.name] = child.get_text()
                    elif type(child) == gtk.CheckButton:
                        if child.get_active():
                            changes[child.name] = "True"
                        else:
                             changes[child.name] = "False"
            self.conf.modify_track(section,changes)
            self.populate_conf()
        else:       
            print "Cancel Advanced Configuration"
        dialog.destroy()


    def show_new_device(self,button):
        
        parent = button.get_parent()
     
        guifile = path.join(path.dirname(path.abspath(__file__)),'advanced_device.glade')
        builder = gtk.Builder()
        builder.add_from_file(guifile)
 
        dialog = builder.get_object("advanced_dialog")
        table  = builder.get_object("deviceoptions")
        devicename = builder.get_object("devicename")

        if parent != None:
            dialog.set_transient_for(parent.get_toplevel())

        options = ["name","device","flavor","location","file"]
        show = ["Name: ", "Type: ", "Flavor: ", "Location: ", "File name: "]
        toshow=dict(zip(options,show))        

        devicename.set_label("New Device")

        for child in table.get_children():
            table.remove(child) #FIXME maybe change the glade to avoid removing any widget
        
        table.resize(1,2) 
        row = 1

        for key in options:
            t=gtk.Label(toshow[key])            
            t.set_justify(gtk.JUSTIFY_LEFT)
            t.set_alignment(0,0)
            t.set_width_chars(20)

            if key in ["device","flavor","location"]: #combobox
                d = gtk.ComboBox()
                print type(d)
                d.set_name(key)
                if key == "device":
                    self.set_model_from_list(d,devices)                    
                elif key == "flavor":
                    self.set_model_from_list(d,flavors)
                elif key == "location":
                    videos = [path.join('/dev',f) for f in os.listdir('/dev') if re.match('video*', f)]
                    audios = os.popen('pactl list | grep "Source" -A 3 | grep "Name"').read().replace("Name:","").split()
                    locations = audios
                    for v in videos:
                        locations.append(v)                      

                    self.set_model_from_list(d,locations)

                d.set_active(-1)
                        
            elif key in ["name","file"]:
                d=gtk.Entry()
                d.set_text("")
                d.set_name(key)
                    
            table.attach(t,0,1,row-1,row,False,False,0,0)
            table.attach(d,1,2,row-1,row,gtk.FILL,False,0,0)
            t.show()
            d.show()
            row=row+1                 
 
        response = dialog.run()        
        if response >= 1: # FIXME, set Apply Button
            print "TODO Create New Track"
            for child in table.get_children():
                if child.name == "name":
                    name = child.get_text()
                elif child.name == "device":
                    device = child.get_active_text()
                elif child.name == "flavor":
                    flavor = child.get_active_text()
                elif child.name == "location":
                    location  = child.get_active_text()
                elif child.name == "file":
                    archive = child.get_text()
                      
            self.conf.new_track(name,device,flavor,location,archive)
            self.populate_conf()
        else:       
            print "Cancel New Device"
        dialog.destroy()

    def show_more_options(self,button):
        kind = button.get_active_text()
        print kind
        if kind == "mjpeg":
            parameters = bins.mjpeg.GCMjpeg.gc_parameters
            print parameters
            
        else:
            print "TODO"
           
    def delete_device(self,button):
        print "TODO"
        #show a list of all devices with check boxes
        #the ones chosen delete
        parent = button.get_parent()
     
        guifile = path.join(path.dirname(path.abspath(__file__)),'delete_device.glade')
        builder = gtk.Builder()
        builder.add_from_file(guifile)
 
        dialog = builder.get_object("dialog")
        table  = builder.get_object("table")

        if parent != None:
            dialog.set_transient_for(parent.get_toplevel())

        def device_label(name):
            label=gtk.Label(name)
            label.set_justify(gtk.JUSTIFY_LEFT)
            label.set_alignment(0,0.5)
            label.set_width_chars(20)
            label.set_ellipsize(pango.ELLIPSIZE_END)
            return label


        b = gtk.HBox(False,0)
        b.set_name("Titulo")
        d = device_label("Devices")

        c =  gtk.Label("Delete")
        c.set_alignment(0.5,0.5)
        c.set_width_chars(6)

        b.pack_start(d)
        b.pack_start(c)
        table.pack_start(b)

        for section in self.conf.conf.sections(): # FIXME conf.conf, crear algun tipo de interface
            if section.count("track"):
                b = gtk.HBox(False,0)
                b.set_name(section)

                d = device_label(self.conf.get(section,"name"))
                c =  gtk.CheckButton(None,False)
                c.set_mode(True)
                #c.set_alignment(0.5,0.5)
                #c.set_use_stock(True)            
                c.set_active(False)
                                
                b.pack_start(d)
                b.pack_start(c,False,False,0)
                table.pack_start(b)  
        dialog.show_all()

        response = dialog.run()        
        if response >= 1: # FIXME, set Apply Button
            actives = self.get_actives(table,False)
            for device in actives:
                 self.conf.delete_track(device)
            self.populate_conf()
        else:       
            print "Cancel Delete DevicesAdvanced"
        dialog.destroy()  
       

gobject.type_register(DeviceUI)
