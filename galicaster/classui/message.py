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
from gi.repository import GObject
from galicaster.classui import get_image_path, get_ui_path
from galicaster.classui.elements.message_header import Header

from galicaster.utils.i18n import _
from galicaster.core import context

TEXT = {'title': None, 'main': None, 'text': None}

INFO = 'help.glade'
ERROR = 'error.glade'
WARN_STOP = 'stop.glade'
WARN_QUIT = 'quit.glade'
WARN_DELETE = 'delete.glade'
WARN_OK = 'okwarning.glade'
OPERATIONS = 'operations.glade'
ABOUT = 'about.glade'
LOCKSCREEN = 'lockscreen.glade'

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

instance = None

class PopUp(Gtk.Widget):
    """Handle a pop up for warnings and questions"""
    __gtype_name__ = 'PopUp'

    def __init__(self, message=None, text=TEXT, parent=None,
                 buttons=None, response_action=None, close_on_response=True):
        """ Initializes the Gtk.Dialog from its GLADE
        Args:
            message (str): type of message (See above constants)
            text (Dict{str:str}): dictionary with three fields (title, main question, explanation text)
            parent (Gtk.Window): program main window
            buttons (Dict{str:str}): button labels to be shown and its responses
        """
        # FIXME: Workaround in order to avoid the gurbage collector (GC)
        global instance
        instance = self

        #TODO: Remove unused params.
        # Parse Size proportions
        #FIXME: Use always as parent context.get_mainwindow()??
        size = parent.get_size()
        self.response_action = response_action
        self.close_on_response = close_on_response
        self.message = message
        self.size = size
        self.wprop = size[0]/1920.0
        self.hprop = size[1]/1080.0

        # Create dialog
        self.gui = Gtk.Builder()
        self.gui.add_from_file(get_ui_path(message))
        self.gui.connect_signals(self)
        self.dialog = self.configure_ui(text, message, self.gui, parent)

        if message == OPERATIONS:

            frames = {'Cancel': {'Cancel' : -2}}

            for operation,response in buttons.iteritems():
                if operation.count('Ingest'):
                    if not frames.has_key('Ingest'):
                        frames['Ingest'] = {}
                    frames['Ingest'][operation] = response
                elif operation.count('Side') or operation.count('Export'):
                    if not frames.has_key('Export'):
                        frames['Export'] = {}
                    frames['Export'][operation] = response

            self.set_buttons(self.gui, frames)

        elif message == ABOUT:
            self.set_logos(self.gui)

        # Display dialog
        parent.get_style_context().add_class('shaded')
        if message == ERROR or message == WARN_QUIT or message == WARN_STOP or message == ABOUT or message == INFO or message == WARN_DELETE or message == LOCKSCREEN:
            self.dialog.show_all()
            self.dialog.connect('response', self.on_dialog_response)
        #elif message == ABOUT:
        #    #TODO: use on_dialog_response instead of on_about_dialog_response
        #    self.dialog.show_all()
        #    self.dialog.connect('response', self.on_about_dialog_response)

        else:
            self.response = self.dialog.run()
            self.dialog.destroy()
            parent.get_style_context().remove_class('shaded')


    def configure_ui(self, text, message_type, gui, parent, another=None):
        """Imports the dialog from the corresponding GLADE and adds some configuration
        Args:
            text (Dict{Str:str}): a dictionary wit the text to be filled
            message_type (str): one of the above constants that leads to the appropriate GLADE
            gui (Gtk.Builder): the builder with the GLADE info
            parent (Gtk.Window): the Main Window of the application
            another (Bool): True if dialog_width is small. Otherwise false.
        Returns:
            Gtk.Dialog: the dialog with the main body configured
        """

        image = gui.get_object("image")
        if image:
            image.set_pixel_size(int(self.wprop*80))

        if message_type != INFO:
            main = gui.get_object("main")
            if main:
                main.set_label(text.get('main',''))
        elif message_type == INFO:
            # TODO: Overwrite info text if given
            help_message = "{}\n{}".format(text.get('main',''),text.get('text',''))
            textbuffer = gui.get_object('textbuffer')
            textbuffer.set_text(help_message)

        dialog = gui.get_object("dialog")

        text_label = gui.get_object('text')
        if text_label:
            text_label.set_label(text.get('text',''))
            text_label.show()


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
            dialog.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        else:
            dialog.set_position(Gtk.WindowPosition.CENTER_ALWAYS)

        strip.show()

        return dialog

    def set_buttons(self, gui, frames):
        """ Show the buttons on the different frames and configure its response.
        Args:
            frames (Dict{}): dictionary structure that represents the frames with
                                the buttons to be shown and its response code.
            gui (Gtk.Builder): the structure imported from glade
        """
        for frame,operations in frames.iteritems():
            frame = gui.get_object('{} frame'.format(frame))
            frame.show()
            for operation,response in operations.iteritems():
                button = gui.get_object("{} button".format(operation))
                button.set_label(OPERATION_NAMES[operation])
                button.connect("clicked",self.force_response,response)
                button.show()

    def set_logos(self,gui):
        """ Set the logos of the product and the company
        """

        pixbuf = GdkPixbuf.Pixbuf.new_from_file(get_image_path('logo.svg'))    
        pixbuf = pixbuf.scale_simple(
            int(pixbuf.get_width()*self.wprop),
            int(pixbuf.get_height()*self.wprop),
            GdkPixbuf.InterpType.BILINEAR)
        self.dialog.set_logo(pixbuf)

        teltek_logo = gui.get_object("teltek")
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(get_image_path('teltek.svg'))    
        pixbuf = pixbuf.scale_simple(
            int(pixbuf.get_width()*self.wprop),
            int(pixbuf.get_height()*self.wprop),
            GdkPixbuf.InterpType.BILINEAR)
        teltek_logo.set_from_pixbuf(pixbuf)


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


    def force_response(self, origin=None, response=None):
        self.dialog.response(response)

    def on_about_dialog_response(self, origin, response_id):
        if response_id in NEGATIVE:
            context.get_mainwindow().get_style_context().remove_class('shaded')
            self.dialog_destroy()

    def on_dialog_response(self, origin, response_id):        
        if response_id not in NEGATIVE and self.response_action:            
            self.response_action(response_id, builder=self.gui, popup=self)
            
        if self.close_on_response:
            self.dialog_destroy()

    def dialog_destroy(self, origin=None):
        global instance
        if self.dialog:
            context.get_mainwindow().get_style_context().remove_class('shaded')
            self.dialog.destroy()
            self.dialog = None
        instance = None

    def error_reload_profile(self, origin=None):        
        self.dialog_destroy()

        dispatcher = context.get_dispatcher()
        dispatcher.emit('action-reload-profile')


GObject.type_register(PopUp)

def main(args):
    """Launcher for debugging purposes"""
    print "Running Main Message PopUp"
    PopUp()
    Gtk.main()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))

