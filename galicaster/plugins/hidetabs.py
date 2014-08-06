# -*- coding:utf-8 -*- 
# Galicaster, Multistream Recorder and Player   
#  
#  galicaster/plugins/hidecontrols.py
#  
# Copyright (c) 2013, Teltek Video Research <galicaster@teltek.es>  
#  
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of  
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/  
# or send a letter to Creative Commons, 171 Second Street, Suite 300,    
# San Francisco, California, 94105, USA.   
"""
Hides controls from the Galicaster UI
"""

from galicaster.core import context
import gtk

ALL_TABS = { "events": "eventpanel",
             "status": "status_panel",
             "recording": "rec_panel",
             }



def init():
    dispatcher = context.get_dispatcher()
    dispatcher.connect("galicaster-init", post_init)


def post_init(source=None):
    conf = context.get_conf()

    recorder_ui = context.get_mainwindow().nbox.get_nth_page(0).gui

    data_panel = recorder_ui.get_object('data_panel')

    #rec_button = recorder_ui.gui.get_object('recbutton')
    #edit_button = recorder_ui.gui.get_object('editbutton')
    #help_button = recorder_ui.gui.get_object('helpbutton')
    #pause_button = recorder_ui.gui.get_object('pausebutton')
    #stop_button = recorder_ui.gui.get_object('stopbutton')

    # Customize tabs in the recorder UI
    try: 
        tabs_to_hide = set( x for x in set(conf.get('hidetabs', 'hide').split()) if x in ALL_TABS )
        if tabs_to_hide:
            for tab, obj_name in ALL_TABS.iteritems():
                page = recorder_ui.get_object(obj_name)
                if tab in tabs_to_hide:
                    page.hide_all()
                else:
                    data_panel.set_tab_label_packing(page, False, True,gtk.PACK_START)
    except AttributeError as e:
        # The conf parameter isn't defined. Ignore
        print "Attribute error"
        pass


    default_tab = conf.get('hidetabs', 'default') or None
    try:
        page = recorder_ui.get_object(ALL_TABS[default_tab])
        data_panel.set_current_page(data_panel.page_num(page))
    except KeyError:
        # The conf parameter isn't defined. Ignore
        pass
    
