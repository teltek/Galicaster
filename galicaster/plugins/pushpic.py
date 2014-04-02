# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/pushpic
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import gtk
from StringIO import StringIO
import pycurl

from galicaster.core import context

"""
Description: Galicaster Dashboard PUSH mode. It fetchs a screenchoot of the window through gtk and sends it with Galicaster's Matterhorn HTTP client to the Dashboard endpoint.
This module can work as a plugin or as a separated application.
Status: Experimental 
"""

def init():
    dispatcher = context.get_dispatcher()
    dispatcher.connect('galicaster-notify-timer-long', push_pic)


def get_screenshot():
    """makes screenshot of the current root window, yields gtk.Pixbuf"""
    window = gtk.gdk.get_default_root_window()
    size = window.get_size()
    pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, size[0], size[1])
    pixbuf.get_from_drawable(window, window.get_colormap(),
                                    0, 0, 0, 0, size[0], size[1])
    b = StringIO()
    pixbuf.save_to_callback(b.write, 'png')
    return b.getvalue()    


def push_pic(sender=None):
    conf = context.get_conf()
    mhclient = context.get_mhclient()

    endpoint = "/dashboard/rest/agents/{hostname}/snapshot.png".format(hostname=conf.hostname)
    postfield = [ ("snapshot", get_screenshot() ) ]
    
    try:
        aux = mhclient._MHHTTPClient__call('POST', endpoint, {}, {}, postfield, False, None, False)
    except IOError as e:
        # This endpoint return 204, not 200.
        aux = None
        


    
