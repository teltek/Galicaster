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
# debug
# import traceback

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstPbutils', '1.0')
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk     # noqa: ignore=E402
from gi.repository import GLib    # noqa: ignore=E402
from gi.repository import Gst     # noqa: ignore=E402

from galicaster.core import core  # noqa: ignore=E402
from galicaster.core import context
from galicaster.utils.dbusservice import AlreadyRunning

def main(args):
    def usage():
        sys.stderr.write("usage: %s\n" % args[0])
        return 1

    if len(args) != 1:
        return usage()
    try:
        Gst.init(None)
        gc = core.Main()
        # Bug with Gtk.main() not raising a KeyboardInterrupt(SIGINT) exception
        # https://bugzilla.gnome.org/show_bug.cgi?id=622084
        # Calling GObject.MainLoop.run() instead could be an option.
        # Sadly, Gtk.main_quit() does not work with it.
        # This workaround will stay until a better solution
        # is found or the bug is fixed.

        def handler(gc):
            print("SIGINT sent. Interrupted by user!")
            gc.quit()
        GLib.unix_signal_add(GLib.PRIORITY_HIGH, 2, handler, gc)  # 2 = SIGINT
        Gtk.main()
    except KeyboardInterrupt:
        gc.emit_quit()
        print("Interrupted by user!")

    except AlreadyRunning as exc:
        #Added custom exception when galicaster it's already running
        msg = "Error starting Galicaster: {0}".format(exc)
        print(msg)

        d = context.get_dispatcher()
        d.emit("quit")
        return -2

    except Exception as exc:
        # debug
        # print traceback.format_exc()

        msg = "Error starting Galicaster: {0}".format(exc)
        print(msg)

        logger = context.get_logger()
        logger and logger.error(msg)

        d = context.get_dispatcher()
        d.emit("quit")
        return -1

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
