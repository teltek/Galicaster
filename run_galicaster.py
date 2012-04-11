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

import sys
import gtk
import threading
from threading import _Timer

from galicaster.core import core
from galicaster.utils.dbusservice import DBusService

def main(args):
    def usage():
        sys.stderr.write("usage: %s\n" % args[0])
        return 1

    if len(args) != 1:
        return usage()
    try:
        v = core.Class()
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
