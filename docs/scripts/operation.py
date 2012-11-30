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
import argparse
from galicaster.core import context
from galicaster.core.worker import JOBS

worker = context.get_worker()
repo = context.get_repository()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=JOBS.values(), 
                        help='Galicaster operation')
    parser.add_argument('mp_id', help='MediaPackage Id in Galicaster Repository')
    
    args = parser.parse_args()

    try:
        mp = repo[args.mp_id]
    except KeyError:
        print "Mediapackage does not exit"
        return -1
    print mp.title
    # TODO change worker._export_to_zip and worker._side_by_side only one parametar
    worker.do_job_by_name(args.operation, args.mp_id)
    return 0

if __name__ == '__main__':
    sys.exit(main())

