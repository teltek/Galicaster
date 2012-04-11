# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


import gtk
import pango
from os import path
import gobject

TEXT = {'title': None, 'main': None, 'text': None}
INFO = gtk.STOCK_DIALOG_INFO
QUESTION = gtk.STOCK_DIALOG_QUESTION
WARNING = gtk.STOCK_DIALOG_WARNING
ERROR = gtk.STOCK_DIALOG_ERROR
POSITIVE = [gtk.RESPONSE_ACCEPT, gtk.RESPONSE_OK, gtk.RESPONSE_YES, gtk.RESPONSE_APPLY]
NEGATIVE = [gtk.RESPONSE_REJECT, gtk.RESPONSE_DELETE_EVENT, gtk.RESPONSE_CANCEL, gtk.RESPONSE_CLOSE, gtk.RESPONSE_NO]

class PopUp(gtk.Widget):
    """
    Handle a pop up for warnings and tipos
    """
    __gtype_name__ = 'PopUp'

    def __init__(self, message = None, text = dict(), size = None, parent=None , buttons = None): 

        # Parse Size proportions
        self.wprop = 1
        self.hprop = 1
        if size != None:
            self.wprop = size[0]/1920.0
            self.hprop = size[1]/1080.0
        else:
            size = [1280,960]
            self.wprop = 0.6667
            self.hprop = 0.8889
        self.size=size
            
        # Default buttons
        if buttons == None:
            if message == WARNING:
                pass
            elif message == INFO:
                buttons = ( gtk.STOCK_OK, gtk.RESPONSE_OK ) 
            elif message == QUESTION:
                buttons = ( gtk.STOCK_ACCEPT, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,)
            elif message == ERROR:
                buttons = ( gst.STOCK_CLOSE, gtk.RESPONSE_CLOSE )


        # Define types: WARNING (OK), YES_NO, ACCEPT_CANCEL, THREE_BUTTONS

        # Create an display dialog
        dialog=self.create_ui(buttons,text, message, parent)
        self.response = dialog.run()
        self.dialog.destroy()
        return None

    def create_ui(self, buttons, text, icon, parent):
       
        #dialog
        dialog = gtk.Dialog(text.get("title","Galicaster"),parent,0,buttons)
        self.dialog = dialog
        dialog.set_property('width-request',int(self.size[0]/2.5)) # relative to screen size       
        if self.size[0]<1300:
            dialog.set_property('width-request',int(self.size[0]/2.2)) # relative to screen size   
 
        if buttons != None:
            if len(buttons) > 5:
                dialog.set_property('width-request',int(self.size[0]/2)) # relative to screen size       


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
        #label.set_justify(gtk.JUSTIFY_LEFT)
        #label.set_line_wrap(True)
        #label.set_line_wrap_mode(pango.WRAP_WORD)


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
                stext.set_ellipsize(pango.ELLIPSIZE_END)
                dialog.vbox.pack_start(stext)
                stext.show()

        # Action Area
        
        dialog.action_area.set_layout(gtk.BUTTONBOX_SPREAD)
       

        for e1 in dialog.action_area.get_children(): #buttons
            for e2 in e1.get_children(): #aligns
                if type(e2) == gtk.Label:
                    font2 = self.set_font(str(int(self.wprop*35))+"px")
                    e2.set_attributes(font2)
                else:
                    for e3 in e2.get_children(): #boxes
                        for e4 in e3.get_children():# images and labels
                            if type(e4) == gtk.Label:
                                font2 = self.set_font(str(int(self.wprop*35))+"px")
                                e4.set_attributes(font2)
        # Show
                        
        image.show()
        label.show()        
        box.show()
        #frame.show()
        #align.show()

        return dialog
    
    def set_font(self,description):
        alist = pango.AttrList()
        font=pango.FontDescription(description)
        attr=pango.AttrFontDesc(font,0,-1)
        alist.insert(attr)
        return alist

    def destroy(self):
        self.dialog_destroy()
    
    
        #buttons

gobject.type_register(PopUp)

def main(args):
    v = PopUplisting()
    gtk.main()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv)) 



