## -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/classui/profile
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.
"""
UI for the profile selector
"""


from gi.repository import Gtk, Gdk
from gi.repository import GObject
from gi.repository import Pango

from galicaster.core import context
from galicaster.classui.elements.message_header import Header

#from galicaster.recorder.bins import v4l2
#from galicaster.recorder.bins import vga2usb
#from galicaster.recorder.bins import hauppauge
#from galicaster.recorder.bins import pulse
#from galicaster.recorder.bins import blackmagic
#from galicaster.recorder.bins import videotest
#from galicaster.recorder.bins import audiotest
#from galicaster.recorder.bins import oldblackmagic
#from galicaster.recorder.bins import rtpvideo

from galicaster.utils.i18n import _

class ProfileUI(Gtk.Window):
    """
    Main window of the Profile Selector.
    It holds two tabs, one for profiles and another for tracks.
    """

    __gtype_name__ = 'ProfileUI'

    def __init__(self, parent=None, width = None, height=None):
        if not parent:
            parent = context.get_mainwindow()
        size = context.get_mainwindow().get_size()
        width = int(size[0]/2.2)
        height = int(size[1]/2.0)
        Gtk.Window.__init__(self, type=Gtk.WindowType.POPUP)
        self.set_transient_for(parent)
        self.set_destroy_with_parent(True)
        self.set_type_hint(Gdk.WindowTypeHint.TOOLBAR)
        self.set_title(_("Profile Selector"))
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_default_size(width,height)
        self.set_skip_taskbar_hint(True)
        self.set_modal(True)
        self.set_keep_above(False)
        self.parent = parent

        strip = Header(size=size,title=_("Profile Selector"))

        self.notebook = Gtk.Notebook()
        self.notebook.set_show_tabs(False)

        box = Gtk.VBox()
        box.pack_start(strip, False, False, int(0))
        strip.show()
        box.pack_start(self.notebook, True, True, 0)
        self.add(box)
        self.list=ListProfileBox(self, size)
        self.profile=None
        self.track=None

        tab1 = Gtk.Label(label=_("Profile Selector"))
        self.append_tab(self.list,tab1)
        parent.get_style_context().add_class('shaded')
        self.show_all()
        self.present()


    def append_tab(self, widget, label):
        """Add a tab with a new edition area"""
        self.notebook.append_page(widget,label)
        self.set_title(label.get_text())
        self.notebook.next_page()

    def remove_tab(self):
        """Once edition is finished, remove a edition tab"""
        current_num=self.notebook.get_current_page()
        self.notebook.prev_page()
        new_num = self.notebook.get_current_page()
        current=self.notebook.get_nth_page(current_num)
        if current == self.profile:
            self.profile = None
        elif current == self.track:
            self.track = None
        new=self.notebook.get_nth_page(new_num)
        self.notebook.remove_page(current_num)
        text=self.notebook.get_tab_label(new).get_text()
        new.refresh()
        self.set_title(text)


    def close(self):
        """Handles UI closure, destroying tabs and updating changes"""
        if self.profile:
            self.profile.destroy()
        if self.track:
            self.track.destroy()
        self.parent.get_style_context().remove_class('shaded')
        self.destroy()

class ProfileDialog(Gtk.HBox):
    """
    Profiles Information of Galicaster
    """

    def __init__(self, parent=None, size=(1920,1080)):
        self.superior = parent
        wprop = size[0]/1920.0
        hprop = size[1]/1080.0
        self.wprop = wprop
        self.hprop = hprop
        #GObject.__init__(self, False, int(wprop*5))
        GObject.GObject.__init__(self)

        self.set_border_width(int(wprop*20))
        self.vbox = Gtk.VBox(False,0)

        self.buttons = Gtk.VButtonBox()
        self.buttons.set_layout(Gtk.ButtonBoxStyle.START)
        self.buttons.set_spacing(int(wprop*5))

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_shadow_type(Gtk.ShadowType.ETCHED_IN)

        self.list,self.view = self.prepare_view()
        self.view.get_selection().connect("changed",self.append_info)
        scrolled.add(self.view)

        sidebox = Gtk.VBox(False,0)
        frame = Gtk.Frame()

        label= Gtk.Label(label=_("Profile Tracks"))
        alist = Pango.AttrList()
        #font = Pango.FontDescription("bold "+str(int(self.hprop*15)))
        #attr=Pango.AttrFontDesc(font,0,-1)
        #alist.insert(attr)
        label.set_attributes(alist)

        frame.set_label_widget(label)
        frame.set_label_align(0.5,0.5)
        frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        align=Gtk.Alignment.new(1,0.5,0.95,0.9)
        self.sidetable = Gtk.Table(homogeneous=True)
        self.sidetable.set_size_request(int(wprop*300),-1)
        align.add(self.sidetable)
        frame.add(align)

        self.vbox.pack_end(scrolled, True, True, 0)
        self.pack_start(self.vbox, True, True, 0)
        sidebox.pack_start(self.buttons, False, False, int(hprop*10))
        sidebox.pack_start(frame, False, False, int(hprop*15))
        self.pack_start(sidebox,False,False,int(wprop*15))


    def add_button(self, text, connection, end=False):
        """Adds an action button to the right side of the Box"""
        k1 = self.wprop
        button = Gtk.Button(text)
        button.set_property("width-request", int(k1*150))
        button.set_property("height-request", int(k1*50))
        # label = button.get_children()[0]
        # modification = str(int(self.hprop*20))
        #label.modify_font(Pango.FontDescription(modification))
        if not end:
            self.buttons.pack_start(button, True, True, 0)
        else:
            self.buttons.pack_end(button, True, True, 0)
        button.connect("clicked",connection)
        return button

    def append_profiles(self):
        """Lists the available profiles"""
        profile_list = context.get_conf().get_profiles()
        for name,profile in list(profile_list.items()):
            if not profile.to_delete:
                self.list.append([profile, profile.name])

    def append_info(self, selection = None):
        """Completes the profile auxiliar data on the right side of the box"""
        model,iterator = selection.get_selected()
        if not iterator:
            return None
        table = self.sidetable
        for child in table.get_children():
            table.remove(child)

        profile = model.get_value(iterator,0)
        row=0
        for track in profile.tracks:
            label = Gtk.Label(label=track.flavor+":  ")
            label.set_alignment(1,0)
            label.set_width_chars(int(self.hprop*15))
            widget= Gtk.Label(label=track.name)
            widget.set_alignment(0,0)
            widget.set_ellipsize(Pango.EllipsizeMode.END)
            alist = Pango.AttrList()
            #font = Pango.FontDescription(str(int(self.hprop*13)))
            #attr=Pango.AttrFontDesc(font,0,-1)
            #alist.insert(attr)
            label.set_attributes(alist)
            widget.set_attributes(alist)
            label.show()
            widget.show()
            table.attach(label,0,1,row,row+1,Gtk.AttachOptions.EXPAND|Gtk.AttachOptions.FILL,False,0,0)
            table.attach(widget,1,2,row,row+1,Gtk.AttachOptions.EXPAND|Gtk.AttachOptions.FILL,False,0,0)
            row+=1

    def close(self,button=None):
        """Leaves and close the profile tab"""
        self.superior.remove_tab()
        self.destroy()

class ListProfileBox(ProfileDialog):
    def __init__(self, parent, size, tester = False):
        ProfileDialog.__init__(self, parent, size)

        self.add_button(_("Select"),self.change_selected_profile)
        self.add_button(_("Close"),self.close, True)

        self.append_profiles()
        self.select_current_profile()
        self.append_info(self.view.get_selection())
        self.show_all()

    def select_current_profile(self):
        iterator =self.list.get_iter_first()
        while iterator != None:
            if self.list[iterator][1] == context.get_conf().get_current_profile().name:
                self.view.get_selection().select_iter(iterator)
                #text=self.list[iterator][1]
                break
            iterator = self.list.iter_next(iterator)

        return self.list,iterator

    def prepare_view(self):
        lista = Gtk.ListStore(object, str)
        view = Gtk.TreeView()
        view.set_model(lista)
        view.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
        view.set_headers_visible(False)
        view.columns_autosize()

        render = Gtk.CellRendererText()
        render.set_property('width-chars', 300)
        render.set_property('xalign', 0)
        #render.set_property('height', 40)
        font = Pango.FontDescription("bold "+str(int(self.hprop*20)))
        render.set_property('font-desc', font)
        render.set_fixed_height_from_font(1)

        image = Gtk.CellRendererPixbuf()

        column0 = Gtk.TreeViewColumn("Profile", render, text = 1)
        column1 = Gtk.TreeViewColumn("Current", image)
        column1.set_property('fixed-width', 40)
        column1.set_cell_data_func(image, self.show_current_image)
        view.append_column(column1)
        view.append_column(column0)

        column0.set_sort_column_id(1)
        lista.set_sort_func(1,self.sorting,None)
        lista.set_sort_column_id(1,Gtk.SortType.ASCENDING)
        return lista,view

    def sorting(self, treemodel, iter1, iter2, args=None):
        first = treemodel[iter1][1]
        second = treemodel[iter2][1]

        if first == "Default" or first.lower() < second.lower():
            return -1
        elif second == "Default" or second.lower() < first.lower():
            return 1

    def show_current_image(self, column, cell, model, iterator, data=None):
        profile = model[iterator][0]
        if profile == context.get_conf().get_current_profile():
            cell.set_property("stock-id", Gtk.STOCK_YES)
            cell.set_property("stock-size", Gtk.IconSize.LARGE_TOOLBAR)
        else:
            cell.set_property("stock-id", "0")
        return None

    def change_selected_profile(self, button):
        model,iterator=self.view.get_selection().get_selected()
        if type(iterator) is Gtk.TreeIter:
            profile=model.get_value(iterator,0)
            context.get_conf().change_current_profile(profile.name)

        context.get_dispatcher().emit("action-reload-profile")
        self.close()

    def refresh(self):
        self.list.clear()
        self.append_profiles()
        self.select_current_profile()

    def close(self, button=None):
        self.superior.close()
