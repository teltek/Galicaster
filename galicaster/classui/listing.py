# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/ui/listing
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import Pango

from galicaster import __version__
from galicaster.classui.managerui import ManagerUI
from galicaster.core import context
from galicaster.mediapackage import mediapackage
from galicaster.classui import get_ui_path
from galicaster.classui import message
from galicaster.utils import readable

from galicaster.utils.i18n import _

logger = context.get_logger()

rcstring = """
style "big-scroll" {
    GtkRange::stepper-size = 20
    GtkRange::slider-width = 25
}

class "GtkRange" style "big-scroll"

"""

Gtk.rc_parse_string(rcstring)
#Gtk.rc_reset_styles(self.main_window.get_settings())


class ListingClassUI(ManagerUI):
    """
    Create Recording Listing in a VBOX with TreeView from an MP list
    """
    __gtype_name__ = 'Listing'


    def __init__(self):
        ManagerUI.__init__(self, 3)

        self.menu = Gtk.Menu()
        self.fill_menu()
        builder = Gtk.Builder()
        builder.add_from_file(get_ui_path('listing.glade'))
        release = builder.get_object("release_label")
        release.set_label("Galicaster "+__version__)

        self.gui = builder

        self.box = builder.get_object("listingbox")
        self.vista = builder.get_object("vista")
        self.scroll = builder.get_object("scrolledw")
        self.vista.get_selection().set_mode(Gtk.SelectionMode.SINGLE) # could SELECTION_MULTIPLE

        old_style = context.get_conf().get_color_style()
        self.color = context.get_conf().get_palette(old_style)

        builder.connect_signals(self)
        self.dispatcher.connect_ui("action-mm-refresh-row", self.refresh_row_from_mp)
        self.dispatcher.connect_ui("operation-started", self.refresh_operation)
        self.dispatcher.connect_ui("operation-stopped", self.refresh_operation)
        self.dispatcher.connect_ui("view-changed", self.event_change_mode)

        self.populate_treeview(self.repository.list().values())
        self.box.pack_start(self.strip,False,False,0)
        self.box.reorder_child(self.strip,0)
        self.box.show()
        self.pack_start(self.box,True,True,0)



    def event_change_mode(self, orig, old_state, new_state):
        if new_state == 1:
            self.refresh()

    def insert_data_in_list(self, lista, mps):
        """Appends the mediapackage data into the list"""
        lista.clear()
        for mp in mps:
            duration = mp.getDuration()
            if duration in ["", None]:
                duration = 0

            if mp.status != mediapackage.SCHEDULED:
                lista.append([mp.getIdentifier(),
                    mp.getTitle(),
                    mp.getCreator(),
                    mp.series_title ,
                    long(mp.getSize()),
                    int(duration),
                    mp.getStartDateAsString(),
                    mp.status,
                    self.color[mp.getOpStatus("ingest")],
                    mp.getOpStatus("ingest"),
                    mp.getOpStatus("exporttozip"),
                    mp.getOpStatus("sidebyside"),])


    def populate_treeview(self, mp):
        """Establishes which values to be shown, its properties"""
        self.lista = Gtk.ListStore(str, str, str, str, float, int, str, int, str, int, int, int)
        # GObject.TYPE_PYOBJECT
        self.insert_data_in_list(self.lista, mp)

        # Edit Cells per column
        render1 = Gtk.CellRendererText() #name
        render6 = Gtk.CellRendererText() #presenter
        render7 = Gtk.CellRendererText() #series
        render2 = Gtk.CellRendererText() #size
        render3 = Gtk.CellRendererText() #duration
        render4 = Gtk.CellRendererText() #date
        render5 = Gtk.CellRendererText() #id
        render8 = Gtk.CellRendererText() #status
        render9 = Gtk.CellRendererText() #operation
        #render9 = Gtk.CellRendererText() #bg
        self.renders= [render1, render2, render3, render4, render5, render6, render7, render8, render9]
        self.renders[1].set_property('xalign',1.0)
        self.renders[2].set_property('xalign',0.5)
        self.renders[3].set_property('xalign',0.5)
        self.renders[8].set_property('xalign',0.5)


        # vbar = self.scroll.get_vscrollbar()
        # vbar.set_update_policy(Gtk.UPDATE_DELAYED)

        # Create each column
        #columna5 = Gtk.TreeViewColumn("Id",render5,text = 0, background= 8)
        # column5 wont be append to the treeview
        columna1 = Gtk.TreeViewColumn(_("Name"),render1,text = 1, background= 8)
        columna6 = Gtk.TreeViewColumn(_("Presenter"), render6, text = 2, background= 8)
        columna7 = Gtk.TreeViewColumn(_("Series"), render7, text = 3, background= 8)
        columna2 = Gtk.TreeViewColumn(_("Size"), render2, text = 4, background= 8)
        columna3 = Gtk.TreeViewColumn(_("Duration"), render3, text = 5, background= 8)
        columna4 = Gtk.TreeViewColumn(_("Date"), render4, text = 6, background= 8)

        #columna8 = Gtk.TreeViewColumn("Status", render8, text = 7, background= 8)
        columna9 = Gtk.TreeViewColumn(_("Ingest"), render9)
        columna10 = Gtk.TreeViewColumn(_("Zip"), render9)
        columna11 = Gtk.TreeViewColumn(_("SbS"), render9)

        #columna8 = Gtk.TreeViewColumn("Status", render8, text = 7, background= 8)
        #columna9 = Gtk.TreeViewColumn("Operations", render9, text = 9, background= 8)
        #columna9 = Gtk.TreeViewColumn("Background",render9, text = 8)

        # Edit columns
        columna1.set_expand(True)

        # Edit content
        columna2.set_cell_data_func(render2, self.size_readable, 4)
        columna3.set_cell_data_func(render3, self.time_readable, 5)
        columna4.set_cell_data_func(render4, self.date_readable, 6)
        #columna8.set_cell_data_func(render8,self.status_readable,None)
        columna9.set_cell_data_func(render9,self.operation_readable,"ingest")
        columna10.set_cell_data_func(render9,self.operation_readable,"exporttozip")
        columna11.set_cell_data_func(render9,self.operation_readable,"sidebyside")
        # Columns 6 and 7 are not edited

        # Set Treeview Model
        self.vista.set_model(self.lista)

        # Append Columns
        self.vista.append_column(columna4) # date
        self.vista.append_column(columna1) # name
        self.vista.append_column(columna6) # presenter
        self.vista.append_column(columna7) # series
        self.vista.append_column(columna2) # size
        self.vista.append_column(columna3) # duration
        #self.vista.append_column(columna8) # operation former status
        self.vista.append_column(columna9) # operation former status
        self.vista.append_column(columna10) # operation
        self.vista.append_column(columna11) # operation


        #self.resize()
        self.equivalent= {6: 0, 1: 1, 2 : 2, 3 : 3, 4: 4, 5 : 5, 7: 3, 9:6, 10:7, 11:8}  # 9
        # data position versus column position

        # Show TreeView
        self.vista.show()

        # Make Headers clickable
        self.vista.set_headers_clickable(True)

        # Make colums sortable
        columna1.set_sort_column_id(1) # name <<
        columna2.set_sort_column_id(4) # size
        columna3.set_sort_column_id(5) # duration
        columna4.set_sort_column_id(6) # date
        columna6.set_sort_column_id(2) # presenter <<
        columna7.set_sort_column_id(3) # series <<
        #columna8.set_sort_column_id(7) # operation form status <<
        columna9.set_sort_column_id(9) # operation <<
        columna10.set_sort_column_id(10) # operation <<
        columna11.set_sort_column_id(11) # operation <<

        self.lista.set_sort_func(5,self.sorting,5)
        self.lista.set_sort_func(1,self.sorting_text,1)
        self.lista.set_sort_func(2,self.sorting_empty,2)
        self.lista.set_sort_func(3,self.sorting_empty,3)
        #self.lista.set_sort_func(7,self.sorting,7)
        #self.lista.set_sort_func(10,self.sorting,10)
        #self.lista.set_sort_func(11,self.sorting,11)
        #self.lista.set_sort_func(12,self.sorting,12)

        self.vista.connect('row-activated',self.on_double_click)
        self.vista.connect('button-release-event',self.on_list_click)

        self.lista.set_sort_column_id(6,Gtk.SortType.DESCENDING)

    def refresh_treeview(self):
        """Refresh all the values on the list"""
        logger.info("Refreshing TreeView")
        model, selected = self.vista.get_selection().get_selected_rows()
        self.insert_data_in_list(self.lista, self.repository.list().values())

        s = 0 if len(selected) == 0 else selected[0][0]
        self.vista.get_selection().select_path(s)

    def refresh_row_from_mp(self, origin, identifier):
        """Refresh the values of a single row"""
        # Search Iter to the liststor
        i = None
        for row in self.lista:
            if row[0] == identifier:
                i = row.iter

            mp = self.repository.get(identifier)
            if i:
                self._refresh(mp,i)

    def refresh_operation(self, origin, operation, package, success = None, extra=None):
        """Refresh the status of an operation in a given row"""
        identifier = package.identifier
        self.refresh_row_from_mp(origin,identifier)

    def refresh_row(self,reference,i):# FIXME keep the sort id
        mpid = self.lista[i][0] # FIXME set the id as the first metadata
        mp = self.repository.get(mpid)
        self._refresh(mp,i)

    def _refresh(self,mp,i):
        """Fills the new values of a refreshed row"""
        self.lista.set(i,0,mp.getIdentifier())
        self.lista.set(i,1,mp.getTitle())
        self.lista.set(i,2,mp.getCreator())
        self.lista.set(i,3,mp.series_title)
        self.lista.set(i,4,long(mp.getSize()))
        self.lista.set(i,5,int(mp.getDuration()))
        self.lista.set(i,6,mp.getStartDateAsString())
        self.lista.set(i,7,mp.status)
        self.lista.set(i,8,self.color[mp.getOpStatus("ingest")])
        self.lista.set(i,9,mp.getOpStatus("ingest"))
        self.lista.set(i,10,mp.getOpStatus("exporttozip"))
        self.lista.set(i,11,mp.getOpStatus("sidebyside"))

    def refresh(self,element=None,package=None):
        # self refresh_row()
        self.refresh_treeview()
        return True

#---------------------------- MOUSE AND SELECTION MANAGMENT --------------------


    def on_action(self, widget):
        """When an action its selected calls the function associated"""
        action=widget.get_name()
        #if not isinstance(op,str):
            #    op=action.get_label()

        logger.info("ON_action >> {0}".format(action))


        if action == "delete_action":
            #self.vista.get_selection().selected_foreach(self.delete)
            model, selected = self.vista.get_selection().get_selected_rows()
            iters = []
            for row in selected:
                iterator=self.lista.get_iter(row)
            iters.append(iterator)
            for i in iters:
                #self.on_delete(self.lista,i)
                key = self.lista[i][0]
                self.delete(key,self.create_delete_dialog_response(self.lista, i))
            #TODO connect "row-deleted" to delete package
        elif action == "operations_action":
            self.vista.get_selection().selected_foreach(self.on_ingest_question)
        elif action == "play_action":
            self.vista.get_selection().selected_foreach(self.on_play)# FIX single operation
        elif action == "edit_action":
            self.vista.get_selection().selected_foreach(self.on_edit)# FIX single operation
        elif action == "info_action":
            self.vista.get_selection().selected_foreach(self.on_info)
        else:
            logger.debug('Invalid action')


    def fill_menu(self):
        """Fill the menu to be shown on right-button-click over a MP"""
        operations = [ (_("Play"), "play_action"),
                (_("Edit"), "edit_action"),
                (_("Info"), "info_action"),
                (_("Operations"), "operations_action"),
                (_("Delete"), "delete_action")]

        for op in operations:
            item = Gtk.MenuItem.new_with_label(op[0])
            item.set_name(op[1])
            self.menu.append(item)
            item.connect("activate", self.on_action)
            item.show()


    def on_list_click(self,widget,event):
        """ If rigth-button is clicked: ensure proper selection, get row,  create menu and pop it
        """
        if event.button == 3:
            reference,column,xcell,ycell = widget.get_path_at_pos(int(event.x),int(event.y))
            c = self.lista.get_iter(reference)
            self.vista.get_selection().unselect_all()
            self.vista.get_selection().select_iter(c)
            self.menu.popup(None,None,None,None,event.button,event.time)
            self.menu.show()
            return True
        return False


    def on_double_click(self,treeview,reference,column):
        """Set the player for previewing if double click"""
        self.on_play(treeview.get_model(),reference,treeview.get_model().get_iter(reference))

    def on_ingest_question(self,store,reference,iterator):
        """Launchs ingest dialog and refresh row afterwards."""
        package = self.repository.get(store[iterator][0])
        self.ingest_question(package)
        self.refresh_row(reference,iterator)
        return True

    #def on_delete(self,store,iterator):
    #    """Remove a mediapackage from the view list"""
    #    key = store[iterator][0]
    #    response = self.delete(key,self.create_delete_dialog_response(store, iterator))

    def create_delete_dialog_response(self, store, iterator):

        def on_delete_dialog_response(response_id, **kwargs):
            if response_id in message.POSITIVE:
                self.repository.delete(self.repository.get(store[iterator][0]))
                self.lista.remove(iterator)
                self.vista.get_selection().select_path(0)

        return on_delete_dialog_response

    def on_play(self,store,reference,iterator):
        """ Retrieve mediapackage and send videos to player"""
        key = store[iterator][0]
        logger.info("Play: " + str(key))
        package = self.repository.get(key)

        if package.status == mediapackage.RECORDED:
            self.dispatcher.emit("play-list", package)
        else:
            text = {"title" : _("Media Manager"),
                "main" : _("This recording can't be played"),
               }
            buttons = ( Gtk.STOCK_OK, Gtk.ResponseType.OK )
            message.PopUp(message.WARN_OK, text,
                              context.get_mainwindow(),
                              buttons)
        return True

#-------------------------------- DATA PRESENTATION --------------------------------


    def size_readable(self, column, cell, model, iterator, index):
        """Generates human readable string for a number.
        Returns: A string form of the number using size abbreviations (KB, MB, etc.) """
        value = readable.size(model.get_value(iterator, index))
        cell.set_property('text', value)

    def date_readable(self, column, cell, model, iterator, index):
        """ Generates date readable string from an isoformat datetime. """
        value = readable.date(model.get_value(iterator, index))
        cell.set_property('text', value)

    def time_readable(self, column, cell, model, iterator, index):
        """Generates date hour:minute:seconds from seconds."""
        value = readable.time(model.get_value(iterator, index)/1000)
        cell.set_property('text', value)

    def list_readable(self,listed):
        """Generates a string of items from a list, separated by commas."""
        novo = readable.list(listed)
        return novo

    def status_readable(self, column, cell, model, iterator, index):
        """Set text equivalent for numeric status of mediapackages."""
        value = mediapackage.mp_status.get(model.get_value(iterator, index))
        cell.set_property('text', value)

    def operation_readable(self, column, cell, model, iterator, operation):
        """Sets text equivalent for numeric operation status of mediapackages."""
        mp=self.repository.get((model[iterator])[0])
        status=mp.getOpStatus(operation)
        out = _(mediapackage.op_status[status])
        cell.set_property('text', out)
        old_style = context.get_conf().get_color_style()
        if old_style:
            color = model[iterator][8]
        else:
            palette = context.get_conf().get_palette()
            color = palette[status]
        cell.set_property('background', color)

#--------------------------------------- Edit METADATA -----------------------------

    def on_edit(self,store,reference,iterator):
        """Pop ups the Metadata Editor"""
        key = store[iterator][0]
        self.edit(key)
        self.refresh_row(reference,iterator)

    def on_info(self,store,reference,iterator):
        """Pops up de MP info dialog"""
        key = store[iterator][0]
        self.info(key)

    def resize(self):
        """Adapts GUI elements to the screen size"""
        buttonlist = ["playbutton","editbutton","ingestbutton","deletebutton"]
        size = context.get_mainwindow().get_size()
        wprop = size[0]/1920.0
        hprop = size[1]/1080.0

        vbar = self.scroll.get_vscrollbar()
        vbar.set_size_request(int(wprop*6),-1)

        self.renders[0].set_property('height', int(hprop*40))
        self.renders[0].set_property('width-chars',int(wprop*56))#name
        self.renders[1].set_property('width-chars',int(wprop*14))#size
        self.renders[2].set_property('width-chars',int(wprop*10))#duration
        self.renders[3].set_property('width-chars',int(wprop*23))#date
        self.renders[5].set_property('width-chars',int(wprop*27))#presenter
        self.renders[6].set_property('width-chars',int(wprop*33.5))#series
        #self.renders[7].set_property('width-chars',int(wprop*12.5))#statusess
        self.renders[8].set_property('width-chars',int(wprop*14))#operations less

        fsize = 12*hprop
        for cell in self.renders:
            font = Pango.FontDescription(str(fsize))
            cell.set_property('font-desc', font)

        for column in self.vista.get_columns():
            first = column.get_widget()
            if not first:
                label = Gtk.Label(label=" "+column.get_title())
            else:
                label = column.get_widget()
                attr = Pango.AttrList()
    #            attr.insert(Pango.AttrFontDesc(font,0,-1))
                label.set_attributes(attr)
                if not first:
                    label.show()
                    column.set_widget(label)
                column.queue_resize()

        self.do_resize(buttonlist)
        return True


GObject.type_register(ListingClassUI)

