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

from StringIO import StringIO

from galicaster.core import context
from galicaster.utils.miscellaneous import get_screenshot_as_pixbuffer

"""
Description: Galicaster Dashboard PUSH mode. It fetchs a screenchoot of the window through gtk and sends it with Galicaster's Opencast HTTP client to the Dashboard endpoint.
This module can work as a plugin or as a separated application.
Status: Experimental 
"""

def init():
    dispatcher = context.get_dispatcher()
    dispatcher.connect('timer-long', push_pic)


def get_screenshot():
    """makes screenshot of the current root window, yields Gtk.Pixbuf"""
    pixbuf = get_screenshot_as_pixbuffer()

    b = StringIO()
    pixbuf.save_to_callback(b.write, 'png', [], ["100"])
    return b.getvalue()    


def push_pic(sender=None):
    conf = context.get_conf()
    occlient = context.get_occlient()

    endpoint = "/dashboard/rest/agents/{hostname}/snapshot.png".format(hostname=conf.get_hostname())
    postfield = [ ("snapshot", get_screenshot() ) ]
    
    try:
        occlient._OCHTTPClient__call('POST', endpoint, {}, {}, postfield, False, None, False)
    except IOError:
        # This endpoint return 204, not 200.
        pass
        


    
