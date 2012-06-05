#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       run_galicaster
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import optparse, sys
import gtk
import threading
from threading import _Timer

from galicaster.core import core
from galicaster.utils.dbusservice import DBusService

def main(args):
    parser = optparse.OptionParser()
    parser.add_option('-c', '--config', 
                      dest="conf_file", 
                      default=None,
                      )
    parser.add_option('-d', '--config_dist', 
                      dest="conf_dist_file", 
                      default=None,
                      )
    options, remainder = parser.parse_args()

    try:
        v = core.Class(options.conf_file, options.conf_dist_file)
        service = DBusService(v)
        gtk.main()
    except KeyboardInterrupt:
        print "Interrupted by user!"
        # FIXME call Scheduler.do_stop_timers()
        for t in threading.enumerate():
            if isinstance(t, _Timer):
                t.cancel()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv)) 
