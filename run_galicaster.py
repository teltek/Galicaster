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

import pygtk
pygtk.require('2.0')
import pygst
pygst.require('0.10')


from galicaster.core import core

def main(args):
    def usage():
        sys.stderr.write("usage: %s\n" % args[0])
        return 1

    if len(args) != 1:
        return usage()
    try:
        gc = core.Main()
        gtk.gdk.threads_enter()
        gtk.main()
    except KeyboardInterrupt:
        gc.emit_quit()
        print "Interrupted by user!"
    except Exception as exc:
        from galicaster.core import context
        logger = context.get_logger()
        logger and logger.error("Error starting Galicaster: {0}".format(exc))

        d = context.get_dispatcher()
        d.emit("galicaster-notify-quit")
        return -1


    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv)) 
