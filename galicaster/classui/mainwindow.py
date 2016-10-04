# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/ui/mainwindow
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.
"""
UI for the welcoming page
"""
import re
from gi.repository import Gtk, Gdk, GdkPixbuf

from galicaster import __version__
from galicaster.classui import message
from galicaster.classui import get_image_path
from galicaster.classui import get_ui_path
from galicaster.utils.shutdown import shutdown as UtilsShutdown


from galicaster.utils.i18n import _


class GCWindow(Gtk.Window):
    """
    GUI for the Welcoming - Distribution Screen
    """
    __gtype_name__ = 'GCWindow'

    def __init__(self, dispatcher=None, size=None, logger=None):
        Gtk.Window.__init__(self, Gtk.WindowType.TOPLEVEL)
        self.logger = logger

        self.full_size = self.discover_size()  # Fullscreen size
        self.custom_size = self.full_size
        expr = '[0-9]+[\,x\:][0-9]+'  # Parse custom size
        if re.match(expr, size):
            self.custom_size = [int(a) for a in size.split(re.search('[,x:]', size).group())]
        elif size == "auto":
            self.logger.info("Default resolution and fullscreen: " + str(self.full_size))
        else:
            self.logger.warning("Invalid resolution, set default. Should be 'width,height'. " + size)

        if self.custom_size[0] > self.full_size[0]:
            self.custom_size[0] = self.full_size[0]
            self.logger.warning("Resolution Width is bigger than the monitor, set to monitor maximum")

        if self.custom_size[1] > self.full_size[1]:
            self.custom_size[1] = self.full_size[1]
            self.logger.warning("Resolution height is bigger than the monitor, set to monitor maximum")

        self.__def_win_size__ = (self.custom_size[0], self.custom_size[1])
        self.set_size_request(self.custom_size[0], self.custom_size[1])
        #        self.resize(self.custom_size[0],self.custom_size[1])

        self.set_title(_("GaliCASTER {0}").format(__version__))
        self.set_decorated(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.is_fullscreen = (self.custom_size == self.full_size)

        self.set_style()
        self.set_width_interval_class(self.get_size()[0])

        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(get_image_path('galicaster.svg'),48,48)
        pixbuf = pixbuf.scale_simple(128, 128, GdkPixbuf.InterpType.BILINEAR)
        self.set_icon(pixbuf)
        self.connect('delete_event', lambda *x: self.__on_delete_event())
        self.dispatcher = dispatcher
        self.connect('visibility-notify-event', self.on_visibility_event)
        if self.dispatcher:
            self.dispatcher.connect('action-quit', self.close)
            self.dispatcher.connect('action-shutdown', self.shutdown)

        self.nbox = Gtk.Notebook()
        self.nbox.set_show_tabs(False)
        self.add(self.nbox)

        self.connect('key-press-event', self.on_key_press)
        self.connect('key-release-event', self.on_key_release)

    def on_visibility_event(self, *args):
        self.dispatcher.emit('gc-shown')

    def start(self):
        """Shifts to fullscreen mode and triggers content resizing and drawing"""
        if self.is_fullscreen:
            self.fullscreen()
            self.maximize()
        self.resize_childs()
        self.show_all()

    def set_style(self):
        """ Apply the main style of the application from the CSS """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_path(get_ui_path('style.css'))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def set_width_interval_class(self, size):
        """ Set the window width class: small, medium or large.
        By default is medium.
        Arguments:
            size (int): the width of the main window in pixels
        """
        max_small = 992
        min_large = 1200
        style_context = self.get_style_context()
        if size < max_small:
            style_context.add_class('small')
        elif size > min_large:
            style_context.add_class('large')
        else:
            style_context.add_class('medium')

    def toggle_fullscreen(self, other=None):
        """Allows shifting between full and regular screen mode.
        For development purposes."""
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.unfullscreen()
        else:
            self.is_fullscreen = True
            self.fullscreen()
        self.resize_childs()

    def resize_childs(self):
        """Resize the children upon the main window screen size."""
        nbook = self.get_child()
        current = nbook.get_nth_page(self.get_current_page())
        current.resize()

        for child in nbook.get_children():
            if child is current:
                continue
            child.resize()

    def get_size(self):
        """Returns the current size of the main window. """
        if self.is_fullscreen:
            return self.full_size
        else:
            return self.custom_size

    def get_k1_k2(self):
        k1 = self.get_size()[0] / 1920.0
        k2 = self.get_size()[0] / 1080.0
        return k1, k2
        
    def discover_size(self):
        """Retrieves the current size of the window where the application will be shown"""
        size = (1920, 1080)
        try:
            root = Gdk.get_default_root_window()
#            root.set_cursor(gtk.gdk.Cursor(gtk.gdk.ARROW))
            screen = root.get_screen()
            rect = screen.get_monitor_geometry(0)
            size = [rect.width, rect.height]
        except:
            if self.logger:
                self.logger.error("Unable to get root screen size")

        return size

    def insert_page(self, page, label, cod):
        """Insert an area on the main window notebook widget"""
        self.nbox.insert_page(page, Gtk.Label(label=label), cod)


    def insert_element(self, element, ui, box_id, method="add",  **kwargs):
        """Insert an element in the container named box_id
           in the notebook page with number ui"""
        try:
            box = self.get_element(box_id, ui)
            if box:
                try:
                    m = getattr(box,method)
                except AttributeError:
                    self.logger.error("Error trying to add the element {} to the box {}, tried the method: {}".format(element, box, method))
                    return None
                else:
                    m(element,**kwargs)
                    box.show_all()
                    self.logger.debug("Element inserted in id: {}".format(box_id))
                    return element
        except Exception as error:
            self.logger.error("Error trying to add the element: {}".format(error))
            return None


    def insert_element_with_position(self, element, ui, box_id, method="add", position=0, **kwargs):
        """Insert an element in the container named box_id
           in the notebook page with number ui"""
        element = self.insert_element(element, ui, box_id, method, **kwargs)
        if element:
            try:
                builder = self.nbox.get_nth_page(ui).gui
                box = builder.get_object(box_id)
                box.reorder_child(element,position)
                return element
            except Exception as exc:
                self.logger.error("Error trying to reorcer element {}: {}".format(element, exc))



    def get_element(self, element_name, ui):
        try:
            builder = self.nbox.get_nth_page(ui).gui
            box = builder.get_object(element_name)
            return box
        except Exception as exc:
            self.logger.error("Error trying to get element with name {} from {}: {}".format(element_name, ui, exc))


    def set_current_page(self, cod):
        """Changes active area"""
        self.nbox.set_current_page(cod)

    def get_current_page(self):
        """Gets the current page id number"""
        return self.nbox.get_current_page()

    def __on_delete_event(self):
        """Emits the quit signal to its childs"""
        if self.logger:
            self.logger.debug("Delete Event Received")
        if self.dispatcher:
            self.dispatcher.emit('action-quit')
        return True

    def close(self, signal):
        """Pops up a dialog asking to quit"""
        text = {"title": _("Quit"),
                "main": _("Are you sure you want to QUIT? "),
                }

        buttons = (Gtk.STOCK_QUIT, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT)
        self.dispatcher.emit("action-audio-disable-msg")
        message.PopUp(message.WARN_QUIT, text,
                      self, buttons, self.on_close_dialog_response)
        self.dispatcher.emit("action-audio-enable-msg")

    def on_close_dialog_response(self, response_id, **kwargs):
        if response_id in message.POSITIVE:
            self.do_quit()
        else:
            if self.logger:
                self.logger.info("Cancel Quit")


    def do_quit(self,element=None):
        if self.logger:
            self.logger.info("Quit Galicaster")
        if self.dispatcher:
            self.dispatcher.emit('quit')
        Gtk.main_quit()

    def shutdown(self, signal):
        """Pops up a dialog asking to shutdown the computer"""
        text = {"title": _("Shutdwon"),
                "main": _("Are you sure you want to SHUTDOWN? "),
                }

        buttons = (Gtk.STOCK_QUIT, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT)
        warning = message.PopUp(message.WARN_QUIT, text,
                                self, buttons)

        if warning.response in message.POSITIVE:
            if self.logger:
                self.logger.info("Shutdown Galicaster")
            if self.dispatcher:
                self.dispatcher.emit('quit')
            UtilsShutdown()
        else:
            if self.logger:
                self.logger.info("Cancel Shutdown")

    def on_key_press(self, source, event):
        self.dispatcher.emit("action-key-press", source, event)

    def on_key_release(self, source, event):
        self.dispatcher.emit("action-key-release", source, event)
