#!/bin/bash

# kill galicaster
pkill -u mca python

sleep 20
date

# start galicaster again
/opt/galicaster/run_galicaster.py &
