#!/bin/bash

# kill galicaster
pkill -u mca python

sleep 5

# start galicaster again
/opt/galicaster/run_galicaster.py -c ~mca/.galicaster/`hostname`.conf.ini -d ~mca/.galicaster/conf-dist.ini &
