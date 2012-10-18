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

import pygtk
pygtk.require('2.0')
import pygst
pygst.require('0.10')


from galicaster.core import core

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
        v = core.Main(options.conf_file, options.conf_dist_file)
        gtk.main()
    except KeyboardInterrupt:
        gc.emit_quit()
        print "Interrupted by user!"

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv)) 
