# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.
"""
Basic Dialog Messag UI
"""

import gtk
import pango
from os import path
import gobject

TEXT = {'title': None, 'main': None, 'text': None}
INFO = gtk.STOCK_DIALOG_INFO
QUESTION = gtk.STOCK_DIALOG_QUESTION
WARNING = gtk.STOCK_DIALOG_WARNING
ERROR = gtk.STOCK_DIALOG_ERROR
ACTION = gtk.STOCK_DIALOG_QUESTION
POSITIVE = [gtk.RESPONSE_ACCEPT, gtk.RESPONSE_OK, gtk.RESPONSE_YES, gtk.RESPONSE_APPLY]
NEGATIVE = [gtk.RESPONSE_REJECT, gtk.RESPONSE_DELETE_EVENT, gtk.RESPONSE_CANCEL, gtk.RESPONSE_CLOSE, gtk.RESPONSE_NO]

class PopUp(gtk.Widget):
    """Handle a pop up for warnings and questions"""
    __gtype_name__ = 'PopUp'

    def __init__(self, message = None, text = dict(), parent=None,
                 buttons = None, two_lines = None): 
        """
        message: type of message (INFO,QUESTION,WARNING, ERROR, ACTION)
        text: dictionary with three fields (title, main question, explanation text)
        parent: program main window 
        buttons: buttons to be shown and values
        two_lines: second line of buttons
        """
        # Parse Size proportions
        size = parent.get_size()
        self.size = size
        self.wprop = size[0]/1920.0
        self.hprop = size[1]/1080.0
            
        # Default buttons
        if buttons == None:
            if message == WARNING:
                pass
            elif message == INFO:
                buttons = ( gtk.STOCK_OK, gtk.RESPONSE_OK ) 
            elif message == QUESTION:
                buttons = ( gtk.STOCK_ACCEPT, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,)
            elif message == ERROR:
                buttons = ( gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE )


        # Create an display dialog
        if message == "INGEST":
            joined = two_lines+buttons
            dialog = self.create_framed_lines(joined, text, QUESTION, parent)
        elif two_lines:
            dialog = self.create_ui_two_lines(buttons, two_lines, text, message, parent)
        else:
            dialog = self.create_ui(buttons,text, message, parent, message == ERROR)  
        self.response = dialog.run()
        dialog.destroy()
        return None

    def create_ui_two_lines(self, buttons, secondary, text, message, parent):
        """Creates and additional button box"""

        secondary_area = gtk.HButtonBox()
        secondary_area.set_homogeneous(True)
        for element in secondary:
            if type(element) is str:
                response = secondary[secondary.index(element)+1]
                button = gtk.Button(element)
                button.show()
                secondary_area.pack_start(button,True,True)                
                button.connect("clicked",self.force_response,response)

        self.resize_buttons(secondary_area, 35)            

        dialog = self.create_ui(buttons,text, message, parent, message == ERROR, True)  

        self.resize_buttons(dialog.action_area, 20)

        dialog.vbox.pack_end(secondary_area,True,True,0)
        secondary_area.set_layout(gtk.BUTTONBOX_SPREAD)        
        secondary_area.show() 

        return dialog       


    def create_ui(self, buttons, text, icon, parent, modifier = None, another = False):
        """Creates the dialog window and sets its configuration"""
  
        #dialog        
        dialog = gtk.Dialog(text.get("title","Galicaster"),parent,0,buttons)

        self.dialog = dialog
        dialog.set_property('width-request',int(self.size[0]/2.5)) 
        # relative to screen size       
        if self.size[0]<1300:
            dialog.set_property('width-request',int(self.size[0]/2.2))
        if another:
             dialog.set_property('width-request',int(self.size[0]/1.5)) 
         

        wprop = self.wprop

        dialog.vbox.set_property('spacing',int(self.hprop*20)) # vertical
            
        dialog.set_property('border-width',30) # full
        if parent != None:
            dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
            
        else:
            dialog.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        dialog.set_resizable(False)

        #Content
        box = gtk.HBox(spacing=int(self.wprop*30)) # between image and text

        label = gtk.Label(text["main"])
        font=self.set_font(str(int(self.hprop*30))+"px")
        label.set_attributes(font)
        label.set_alignment(0,0.5)


        image = gtk.Image()
        image.set_from_icon_name(icon, gtk.ICON_SIZE_DIALOG)
        image.set_pixel_size(int(self.wprop*80))
        box.pack_start(image,True,True,0)
        box.pack_start(label,True,True,0)  
        dialog.vbox.pack_start(box, True , True ,0)
   
        if text.has_key("text"):
            if text["text"] != None:
                stext= gtk.Label(text["text"])
                font=self.set_font(str(int(self.hprop*20))+"px")
                stext.set_attributes(font)
                if not modifier:
                    stext.set_alignment(0.5,0.5)                
                    stext.set_ellipsize(pango.ELLIPSIZE_END)
                else:
                    stext.set_alignment(0,0.5)                
                    stext.set_line_wrap(True)
                dialog.vbox.pack_start(stext)
                stext.show()

        # Action Area
        dialog.action_area.set_layout(gtk.BUTTONBOX_SPREAD)

        self.resize_buttons(dialog.action_area, 35)

        # Show
                        
        image.show()
        label.show()        
        box.show()
        #frame.show()
        #align.show()

        return dialog

    def create_framed_lines(self, buttons, text, icon, parent):
        """Creates frames arround groups of buttons"""
        dialog = gtk.Dialog(text.get("title","Galicaster"),parent,0)
        self.dialog = dialog
        dialog.set_property('width-request',int(self.size[0]/1.8)) # relative to screen size       
        wprop = self.wprop

        dialog.vbox.set_property('spacing',int(self.hprop*20)) # vertical
            
        dialog.set_property('border-width',30) # full
        if parent != None:
            dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
            #dialog.set_transient_for(parent)
            #dialog.set_destroy_with_parent(True)
            
        else:
            dialog.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        dialog.set_resizable(False)

        #Content
        box = gtk.HBox(spacing=int(self.wprop*30)) # between image and text

        label = gtk.Label(text["main"])
        font=self.set_font(str(int(self.hprop*30))+"px")
        label.set_attributes(font)
        label.set_alignment(0,0.5)


        image = gtk.Image()
        image.set_from_icon_name(icon, gtk.ICON_SIZE_DIALOG)
        image.set_pixel_size(int(self.wprop*80))
        box.pack_start(image,True,True,0)
        box.pack_start(label,True,True,0)  
        dialog.vbox.pack_start(box, True , True ,0)
   
        if text.has_key("text"):
            if text["text"] != None:
                stext= gtk.Label(text["text"])
                font=self.set_font(str(int(self.hprop*20))+"px")
                stext.set_attributes(font)
                stext.set_alignment(0.5,0.5)                
                stext.set_line_wrap(True)
                dialog.vbox.pack_start(stext)
                stext.show()

 
        # Show
                        
        image.show()
        label.show()        
        box.show()

        options = gtk.HBox()

        has_ingest = False
        for element in buttons:
            if type(element) is str:
                if element.count("Ingest"):
                    has_ingest = True

        if has_ingest:
            ingest = gtk.Frame("Ingest")
            ingest.set_label_align(0.5,0.5)
            ing_align = gtk.Alignment(0.5,0.5,0.6,0.6)
            ing_buttons =  gtk.VButtonBox()
            ing_buttons.set_layout(gtk.BUTTONBOX_SPREAD)
            ingest.add(ing_align)
            ing_align.add(ing_buttons)

        export = gtk.Frame("Export")
        exp_align = gtk.Alignment(0.5,0.5,0.7,0.7)
        export.set_label_align(0.5,0.5)
        export_box = gtk.Table(2,2,homogeneous=True)       
        exp_align.add(export_box)
        export.add(exp_align)

        cancel_frame = gtk.Frame(" ")
        cancel_align = gtk.Alignment(0.5,0.5,0.7,0.7)
        cancel_buttons = gtk.VButtonBox()
        cancel_frame.add(cancel_align)
        cancel_align.add(cancel_buttons)
        cancel_frame.set_shadow_type(gtk.SHADOW_NONE)

        index_down=0
        index_up=0
        for element in buttons:
            if type(element) is str:
                response = buttons[buttons.index(element)+1]
                button = gtk.Button(element)
                #PATCH
                if element == "Cancel Export to Zip Nightly":
                    button.set_label("Cancel Zip Nightly")
                if element == "Cancel Side by Side Nightly":
                    button.set_label("Cancel SbS Nightly")

                button.connect("clicked",self.force_response,response)
                if element.count("Ingest"):
                    ing_buttons.pack_start(button, True, True, int(self.hprop*20))
                elif element ==("Cancel"):
                    cancel_buttons.pack_start(button, True, True,int(self.hprop*20))
                else:
                    if element.count("Nightly"):
                        export_box.attach(button,index_down,index_down+1,1,2,gtk.FILL|gtk.EXPAND,0,
                                          int(self.wprop*5),int(self.hprop*5))
                        index_down+=1
                    else:
                        export_box.attach(button,index_up,index_up+1,0,1,gtk.EXPAND|gtk.FILL,0,
                                          int(self.wprop*5),int(self.hprop*5))
                        index_up+=1
                button.show()

        if has_ingest:
            options.pack_start(ingest)
            ing_buttons.show()
            ing_align.show()
            ingest.show()

        options.pack_start(export)
        options.pack_start(cancel_frame)

        cancel_buttons.show()
        exp_align.show()
        export_box.show()
        cancel_align.show()
        cancel_buttons.show()
        export.show()
        cancel_frame.show()
        options.show()
        dialog.vbox.pack_start(options, True, True)

        self.resize_buttons(options, 22, True)
        return dialog

    def resize_buttons(self, area, fontsize, equal = False):    
        """Adapts buttons to the dialog size"""
        wprop = self.wprop
        fsize=int(wprop*fontsize)
        font2 = self.set_font(str(fsize)+"px")
        chars = int(wprop*26)
        for button in area.get_children():
            for element in button.get_children():
                if type(element) == gtk.Label:
                    element.set_attributes(font2)
                    if equal:
                        element.set_padding(-1,int(wprop*fsize/2.6))
                        element.set_width_chars(chars)
                else:# is a box
                    for box in element.get_children():
                        for label in box.get_children():
                            if type(label) == gtk.Label:
                                label.set_attributes(font2)
                                label.set_padding(int(wprop*fsize),
                                                  int(wprop*fsize/3))
                                if equal:
                                    label.set_padding(int(wprop*fsize/3),
                                                      int(wprop*fsize/2.6))
                                    label.set_width_chars(chars)
                            elif type(label) == gtk.Button:
                                for other in label.get_children():
                                    if type(other) == gtk.Label:
                                        other.set_attributes(font2)
                                        if equal:
                                            other.set_padding(-1,int(wprop*fsize/2.6))
                                            other.set_width_chars(chars)
                                    

    def force_response(self, origin, response):
        self.dialog.response(response)
    
    def set_font(self,description):
        """Asign a font description to a text"""
        alist = pango.AttrList()
        font=pango.FontDescription(description)
        attr=pango.AttrFontDesc(font,0,-1)
        alist.insert(attr)
        return alist

    def dialog_destroy(self):
        self.dialog.destroy()
        self.dialog = None 
    
gobject.type_register(PopUp)

def main(args):
    """Launcher for debugging purposes"""
    print "Running Main Message PopUp"
    v = PopUp()
    gtk.main()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv)) 



