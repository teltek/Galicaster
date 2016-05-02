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

import sys
from gi.repository import Gtk, Gdk, GdkPixbuf
from os import path
from gi.repository import GObject
from galicaster.classui import get_image_path, get_ui_path
from galicaster.classui.elements.message_header import Header

from galicaster.utils.i18n import _

TEXT = {'title': None, 'main': None, 'text': None}


INFO = 'help2.glade'
ERROR = 'error.glade'
WARN_STOP = 'stop.glade'
WARN_QUIT = 'quit.glade'
WARN_DELETE = 'delete.glade'
WARN_OK = 'okwarning.glade'

# FIXME
QUESTION = Gtk.STOCK_DIALOG_QUESTION

#ACTION = Gtk.STOCK_DIALOG_QUESTION
POSITIVE = [Gtk.ResponseType.ACCEPT, Gtk.ResponseType.OK, Gtk.ResponseType.YES, Gtk.ResponseType.APPLY]
NEGATIVE = [Gtk.ResponseType.REJECT, Gtk.ResponseType.DELETE_EVENT, Gtk.ResponseType.CANCEL, Gtk.ResponseType.CLOSE, Gtk.ResponseType.NO]

OPERATION_NAMES = { 'Export to Zip': _('Export to Zip'),
            'Export to Zip Nightly': _('Export to Zip Nightly'),
            'Cancel Export to Zip Nightly': _('Cancel Zip Nightly'),
            'Ingest': _('Ingest'),
            'Ingest Nightly': _('Ingest Nightly'),
            'Cancel Ingest Nightly': _('Cancel Ingest Nightly:'),
            'Side by Side': _('Side by Side'),
            'Side by Side Nightly': _('Side by Side Nightly'),
            'Cancel Side by Side Nightly': _('Cancel SbS Nightly'),            
            'Cancel': _('Cancel'),
             }

class PopUp(Gtk.Widget):
    """Handle a pop up for warnings and questions"""
    __gtype_name__ = 'PopUp'

    def __init__(self, message = None, text = TEXT, parent=None,
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
            
        # Create dialog
        if message == "INGEST":
            joined = two_lines+buttons
            #TODO: Glade for ingest dialog message
            dialog = self.create_framed_lines(joined, text, QUESTION, parent)
        else:
            dialog = self.create_ui(buttons,text, message, parent, message == ERROR)  

        # Display dialog
        self.dialog = dialog
        if message == ERROR:
            a = self.dialog.get_action_area().get_children()[0]
            a.connect('clicked',self.dialog_destroy)            
            self.dialog.show_all()
        else:
            self.response = dialog.run()
            dialog.destroy()


    def create_ui(self, buttons, text, icon, parent, modifier = None, another = False):
        """Imports the dialog from the corresponding GLADE and adds some configuration"""

        #dialog

        # TODO: Overwrite info text if given
        gui = Gtk.Builder()
        gui.add_from_file(get_ui_path(icon))

        image = gui.get_object("image")
        image.set_pixel_size(int(self.wprop*80))

        if icon != INFO:
            main = gui.get_object("main")
            main.set_label(text.get('main',''))
        else:
            help_message = "{}\n{}".format(text.get('main',''),text.get('text',''))
            textbuffer = gui.get_object('textbuffer')
            textbuffer.set_text(help_message)


        dialog = gui.get_object("dialog")

        text_label = gui.get_object('text')
        if text_label:
            text_label.set_label(text.get('text',''))


        dialog.set_type_hint(Gdk.WindowTypeHint.TOOLBAR)
        dialog.set_skip_taskbar_hint(True)

        dialog.set_keep_above(False)

        #HEADER
        strip = Header(size=self.size, title=text.get("title","Galicaster"))
        dialog.vbox.pack_start(strip, True, True, 0)
        dialog.vbox.reorder_child(strip,0)

        dialog.set_property('width-request',int(self.size[0]/2.5)) 
        # relative to screen size       
        if self.size[0]<1300:
            dialog.set_property('width-request',int(self.size[0]/2.2))
        if another:
             dialog.set_property('width-request',int(self.size[0]/1.5)) 

        if parent != None:
            dialog_style_context = dialog.get_style_context()
            window_classes = parent.get_style_context().list_classes()
            for style_class in window_classes:
                dialog_style_context.add_class(style_class)
            dialog.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)    
            dialog.set_transient_for(parent)
            dialog.set_destroy_with_parent(True)
        else:
            dialog.set_position(Gtk.WindowPosition.CENTER_ALWAYS)

        dialog.show_all()

        return dialog

    def create_framed_lines(self, buttons, text, icon, parent): # TODO get commom code with create_ui
        """Creates frames arround groups of buttons"""
        dialog = Gtk.Dialog(text.get("title","Galicaster"),parent,0)
        dialog.set_type_hint(Gdk.WindowTypeHint.TOOLBAR)
        dialog.set_skip_taskbar_hint(True)
        dialog.set_modal(True)

        #Taskbar
        strip = Header(size=self.size, title=text.get("title","Galicaster"))
        dialog.vbox.pack_start(strip, True, True, 0)
        strip.show()

        dialog.set_property('width-request',int(self.size[0]/1.8)) # relative to screen size       
                    
        if parent != None:
            dialog_style_context = dialog.get_style_context()
            window_classes = parent.get_style_context().list_classes()
            for style_class in window_classes:
                dialog_style_context.add_class(style_class)
            dialog.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
            dialog.set_transient_for(parent)
            dialog.set_destroy_with_parent(True)
        else:
            dialog.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        dialog.set_resizable(False)

        # SPACING
        # dialog.vbox.set_property('spacing',int(self.hprop*10)) # vertical

        #Content and spacing
        bigbox = Gtk.VBox(0)
        box = Gtk.HBox(spacing=int(self.wprop*10)) # between image and text
        bigbox.pack_start(box, True, True, 
                          int(self.hprop*10))
                          #0)
        bigbox.set_border_width(int(self.wprop*10))
        dialog.vbox.set_child_packing(dialog.action_area, True, True, int(self.hprop*15), Gtk.PackType.END)

        label = Gtk.Label(label=text["main"])
        label.set_alignment(0,0.5)


        image = Gtk.Image()
        image.set_from_icon_name(icon, Gtk.IconSize.DIALOG)
        image.set_pixel_size(int(self.wprop*80))
        box.pack_start(image,True,True,0)
        box.pack_start(label,True,True,0)  
   
        if text.has_key("text"):
            if text["text"] != None:
                stext= Gtk.Label(label=text["text"])
                stext.set_alignment(0.5,0.5)                
                stext.set_line_wrap(True)
                bigbox.pack_start(stext, True, True, 0)

 
        # Show
        dialog.vbox.pack_start(bigbox, True , True ,int(self.hprop*10))
        bigbox.show_all()

        options = Gtk.HBox()

        has_ingest = False
        for element in buttons:
            if type(element) is str:
                if "Ingest" in element:
                    has_ingest = True
                    break

        has_export = False
        for element in buttons:
            if type(element) is str:
                if "Export" in element or "Side" in element:
                    has_export = True
                    break

        if has_ingest:
            ingest = Gtk.Frame.new(_("Ingest"))
            ingest.set_label_align(0.5,0.5)
            ing_align = Gtk.Alignment.new(0.5,0.5,0.6,0.6)
            ing_align.set_padding(0,0,int(self.wprop*10),int(self.wprop*10))
            ing_buttons =  Gtk.VButtonBox()
            ing_buttons.set_layout(Gtk.ButtonBoxStyle.SPREAD)
            ing_align.add(ing_buttons)
            ingest.add(ing_align)


        if has_export:
            export = Gtk.Frame.new(_("Export"))
            exp_align = Gtk.Alignment.new(0.5,0.5,0.7,0.7)
            exp_align.set_padding(0,0,int(self.wprop*10),int(self.wprop*10))
            export.set_label_align(0.5,0.5)
            export_box = Gtk.Table(2,2,homogeneous=True)       
            exp_align.add(export_box)
            export.add(exp_align)

        cancel_frame = Gtk.Frame.new(" ")
        cancel_align = Gtk.Alignment.new(0.5,0.5,0.7,0.7)
        cancel_buttons = Gtk.VButtonBox()
        cancel_align.add(cancel_buttons)
        cancel_frame.add(cancel_align)
        cancel_frame.set_shadow_type(Gtk.ShadowType.NONE)

        index_down=0
        index_up=0
        for element in buttons:
            if type(element) is str:
                response = buttons[buttons.index(element)+1]
                button = Gtk.Button(OPERATION_NAMES[element])

                #PATCH
                if element == "Cancel Export to Zip Nightly":
                    button.set_label(OPERATION_NAMES[element])
                if element == "Cancel Side by Side Nightly":
                    button.set_label(OPERATION_NAMES[element])

                button.connect("clicked",self.force_response,response)
                if "Ingest" in element:
                    ing_buttons.pack_start(button, True, True, int(self.hprop*20))
                elif element ==("Cancel"):
                    cancel_buttons.pack_start(button, True, True,int(self.hprop*20))
                elif "Export" in element or "Side" in element:
                    if "Nightly" in element:
                        export_box.attach(button,index_down,index_down+1,1,2,Gtk.AttachOptions.FILL|Gtk.AttachOptions.EXPAND,0,
                                          int(self.wprop*5),int(self.hprop*5))
                        index_down+=1
                    else:
                        export_box.attach(button,index_up,index_up+1,0,1,Gtk.AttachOptions.EXPAND|Gtk.AttachOptions.FILL,0,
                                          int(self.wprop*5),int(self.hprop*5))
                        index_up+=1

        if has_ingest:
            options.pack_start(ingest, True, False, 0)
        if has_export:
            options.pack_start(export, True, False, 0)
        options.pack_start(cancel_frame, True, False,  0)

        dialog.vbox.pack_start(options, False, False , 0)
        options.show_all()

        self.resize_buttons(options, 22, True)
        return dialog

    def resize_buttons(self, area, fontsize, equal = False):    
        """Adapts buttons to the dialog size"""
        wprop = self.wprop
        fsize=int(wprop*fontsize)
        chars = int(wprop*26)
        for button in area.get_children():
            for element in button.get_children():
                if type(element) == Gtk.Label:
                    #element.set_attributes(font2)
                    if equal:
                        element.set_padding(-1,int(wprop*fsize/2.6))
                        element.set_width_chars(chars)
                else:# is a box
                    for box in element.get_children():
                        for label in box.get_children():
                            if type(label) == Gtk.Label:
                                #label.set_attributes(font2)
                                label.set_padding(int(wprop*fsize),
                                                  int(wprop*fsize/3))
                                if equal:
                                    label.set_padding(int(wprop*fsize/3),
                                                      int(wprop*fsize/2.6))
                                    label.set_width_chars(chars)
                            elif type(label) == Gtk.Button:
                                for other in label.get_children():
                                    if type(other) == Gtk.Label:
                                        #other.set_attributes(font2)
                                        if equal:
                                            other.set_padding(-1,int(wprop*fsize/2.6))
                                            other.set_width_chars(chars)
                                    

    def force_response(self, origin, response):
        self.dialog.response(response)
    
    def dialog_destroy(self, origin=None):
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None 
    
GObject.type_register(PopUp)

def main(args):
    """Launcher for debugging purposes"""
    print "Running Main Message PopUp"
    PopUp()
    Gtk.main()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv)) 

