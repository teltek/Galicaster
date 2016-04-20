# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/ui/metadata
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.
"""
UI for a Metadata Editor Pop UP
"""

from gi.repository import Gtk, Gdk
import datetime
from os import path
from gi.repository import GObject
from gi.repository import Pango
import os

from galicaster.classui.calendarwindow import CalendarWindow
from galicaster.mediapackage import mediapackage
from galicaster.core import context
from galicaster.utils import series as listseries
from galicaster.classui import get_ui_path
from galicaster.classui.elements.message_header import Header

from galicaster.utils.i18n import _

NO_SERIES  = "** NO SERIES SELECTED **"
DEFAULT_SERIES = "DEFAULT SERIES"

DCTERMS = ["title", "creator", "description", "language", "isPartOf"]
EQUIV = { "presenter":"creator", "ispartof": "isPartOf", "series":"isPartOf" }

metadata = { "title": _("Title:"), _("Title:"):"title",
             "creator": _("Presenter:"), _("Presenter:"):"creator",
             "isPartOf": _("Course/Series:"), _("Course/Series:"):"isPartOf",
             "description": _("Description:"), _("Description:"):"description",
             "subject": _("Subject:"), _("Subject:"):"subject",
             "language": _("Language:"), _("Language:"):"language",
             "identifier": _("Identifier:"), _("Identifier:"):"identifier",
             "contributor": _("Contributor:"),_("Contributor:"):"contributor",
             "created":_("Start Time:"), _("Start Time:"):"created"}

class MetadataClass(Gtk.Widget):
    """
    Handle a pop up metadata editor, updating it if necessary
    """
    __gtype_name__ = 'MetadataClass'

    def __init__(self, package = None, series_list = [], parent = None,
                 title=_("Edit Metadata"), subtitle=_("Edit Metadata"), ok_label = _("Save"), ko_label = _("Cancel"),
                 empty_series_label = NO_SERIES):
        """
        """

        parent = context.get_mainwindow()
        size = parent.get_size()

        self.par = parent
        altura = size[1]
        anchura = size[0]
        k1 = anchura / 1920.0
        k2 = altura / 1080.0
        self.wprop = k1
        self.hprop = k2

        self.series_list = series_list
        self.empty_series_label = empty_series_label

        gui = Gtk.Builder()
        gui.add_from_file(get_ui_path('metadata.glade'))

        dialog = gui.get_object("metadatadialog")

        # Set up the dialog's label
        gui.get_object("title").set_text(subtitle)

        # Set up the button text
        gui.get_object("slabel").set_label(ok_label)
        gui.get_object("clabel").set_label(ko_label)

        dialog.set_property("width-request",int(anchura/2.2))
        dialog.set_type_hint(Gdk.WindowTypeHint.TOOLBAR)
        dialog.set_modal(True)
        dialog.set_keep_above(False)

        #NEW HEADER
        strip = Header(size=size, title=title)
        dialog.vbox.pack_start(strip, True, True, 0)
        dialog.vbox.reorder_child(strip,0)

        if parent != None:
            dialog.set_transient_for(parent.get_toplevel())

        table = gui.get_object('infobox')
        dialog.vbox.set_child_packing(table, True, True, int(self.hprop*25), Gtk.PackType.END)
        title = gui.get_object('title')
        sl = gui.get_object('slabel')
        cl = gui.get_object('clabel')
        talign = gui.get_object('table_align')

        modification = "bold "+str(int(k2*25))+"px"
        title.modify_font(Pango.FontDescription(modification))
        title.hide()
        talign.set_padding(int(k2*40),int(k2*40),0,0)
        mod2 = str(int(k1*35))+"px"
        sl.modify_font(Pango.FontDescription(mod2))
        cl.modify_font(Pango.FontDescription(mod2))

        # Get "blocked" and "mandatory" parameters
        blocked = set()
        mandatory = set()
        try:
            for term in context.get_conf().get('metadata', 'blocked').split():
                try:
                    blocked.add(EQUIV[term])
                except KeyError:
                    blocked.add(term)
        except (KeyError, AttributeError):
            # 'blocked' was not defined in configuration
            pass

        try:
            for term in context.get_conf().get('metadata', 'mandatory').split():
                try:
                    mandatory.add(EQUIV[term])
                except KeyError:
                    mandatory.add(term)
        except (KeyError, AttributeError):
            # 'mandatory' was not defined in configuration
            pass

        self.mandatory = {}
        ok_button = gui.get_object("savebutton")
        self.fill_metadata(table, package, ok_button, blocked, mandatory)

        self.check_mandatory(None, ok_button, check_all = True)

        talign.set_padding(int(self.hprop*25), int(self.hprop*10), int(self.hprop*25), int(self.hprop*25))
        dialog.vbox.set_child_packing(dialog.action_area, True, True, int(self.hprop*25), Gtk.PackType.END)
        dialog.show_all()

        self.return_value = dialog.run()
        if self.return_value == -8:
            self.update_metadata(table,package)
        dialog.destroy()


    def fill_metadata(self,table,mp,button,blocked=set(),mandatory=set()):
        """
        Fill the table with available data, empty otherwise
        """
        for child in table.get_children():
            table.remove(child) #FIXME maybe change the glade to avoid removing any widget
        table.resize(1,2)
        row = 1

        for meta in DCTERMS:
            t=Gtk.Label(label=metadata[meta])
            t.set_justify(Gtk.Justification.LEFT)
            t.set_alignment(0,0)
            modification = str(int(self.hprop*16))+"px"
            t.modify_font(Pango.FontDescription(modification))
            t.set_width_chars(15)

            # Switch the INSENSITIVE state colour to red, so that we can mark the mandatory parameters
            t.modify_fg(Gtk.StateType.INSENSITIVE, Gdk.color_parse('red'))

            if meta in ["ispartof", "isPartOf"]:
                try:
                    default_series = listseries.getSeriesbyId(mp.metadata_series['identifier'])['id']
                except TypeError:
                    default_series = None

                liststore = Gtk.ListStore(str,str)
                # Include empty_label in the list, if it is not None
                if self.empty_series_label is not None:
                    liststore.append([self.empty_series_label, None])

                for element in self.series_list:
                    liststore.append([element[1]['title'], element[0]]) # NAME ID

                # Set the appropriate value
                try:
                    # If 'default' is an existing series id,
                    # set "default_text" to the corresponding series title
                    default_text = dict(self.series_list)[default_series]['title']
                except KeyError:
                    # "default" is not in the listing, so we ignore it
                    default_text = None

                d = Gtk.ComboBox.new_with_model(liststore)
                renderer_text = Gtk.CellRendererText()
                d.pack_start(renderer_text, True)
                d.add_attribute(renderer_text, "text", 0)
                #d.set_entry_text_column(0)

                if self.empty_series_label is not None and default_text is not None:
                    d.set_active(1)
                else:
                    d.set_active(0)

                d.set_name(meta)

            else:
                d=Gtk.Entry()
                d.set_name(meta)
                try:
                    d.set_text(mp.metadata_episode[meta] or '')
                except KeyError:
                    d.set_text('')

            if meta in blocked:
                d.set_sensitive(False)

            if meta in mandatory:
                d.connect_after('changed', self.check_mandatory, button)
                self.mandatory[d] = t

            if meta == "created": # currently Unused
                d.connect("button-press-event",self.edit_date)
            if meta == "title":
                d.set_tooltip_text(d.get_text())

            d.modify_font(Pango.FontDescription(modification))

            table.attach(t,0,1,row-1,row,False,False,0,0)
            table.attach(d,1,2,row-1,row,Gtk.AttachOptions.EXPAND|Gtk.AttachOptions.FILL,False,0,0)
            row=row+1

    def check_mandatory(self, item, button, check_all = False):
        entries = self.mandatory.keys()
        if not check_all:
            # Put 'item' at the beginning of the list
            entries.insert(0, entries.pop(entries.index(item)))

        button.set_sensitive(True)
        for elem in entries:
            try:
                content = elem.get_text()
            except AttributeError:
                # It's the ComboBoxEntry
                try:
                    content = elem.get_model()[elem.get_active_iter()][1]
                except (AttributeError, TypeError):
                    content = None

            # The style has been changed so that labels marked as 'insensitive' will be displayed in red
            self.mandatory[elem].set_sensitive(bool(content))

            # Set button's sensitivity. If there is no content, it should be greyed out
            if not bool(content):
                button.set_sensitive(False)
                # Since the item that changed is at the beginning of the list, we do not need to check the others
                # (unless, of course, we force checking the whole list --to initialize the entries status, for instance--)
                if not check_all:
                    break

        return False

    def strip_spaces(self,value):
        """Remove spaces before and after a value"""
        return value.strip()

    def update_metadata(self,table,mp):
        """Write data back to the mediapackage"""
        for child in table.get_children():
            name = child.get_name()
            if name in DCTERMS:
                if name in ["creator", "contributor", "subject"]:
                    if child.get_text() == "":
                        mp.metadata_episode[name] = None
                    else:
                        mp.metadata_episode[name] = child.get_text().strip()

                elif name in [ "ispartof", "isPartOf" ]:
                    identifier = child.get_model()[child.get_active_iter()][1]
                    series = listseries.getSeriesbyId(identifier)
                    if series:
                        mp.setSeries(series["list"])
                        if not mp.getCatalogs("dublincore/series") and mp.getURI():
                            new_series = mediapackage.Catalog(os.path.join(mp.getURI(),"series.xml"),mimetype="text/xml",flavor="dublincore/series")
                            mp.add(new_series)
                    else:
                        mp.setSeries(None)
                        catalog= mp.getCatalogs("dublincore/series")
                        if catalog:
                            mp.remove(catalog[0])
                else:
                    mp.metadata_episode[name]=child.get_text()

    def edit_date(self,element,event):
        """Filter a Right button double click, show calendar and update date"""

        if event.type == Gdk._2BUTTON_PRESS and event.button==1:
            text= element.get_text()
            try:
                date=datetime.datetime.strptime(text,"%Y-%m-%dT%H:%M:%S")
            except ValueError:
                date=0
            v = CalendarWindow(date)
            v.run()
            if v.date != None:
                element.set_text(v.date.isoformat())
        return True

GObject.type_register(MetadataClass)
