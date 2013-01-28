#!/bin/bash

# kill galicaster
echo "" >> /tmp/restart-galicaster.log
echo "----Running restart script----> `date`"  >> /tmp/restart-galicaster.log
date
echo "Killing Galicaster"
pkill -u $USER python

echo "Checking if rtsp2v4l2 is running"
/opt/galicaster/rtsp_keeprunning.sh

echo "Waiting 10 sec for network to be established"
sleep 10

# start galicaster again
echo "Restarting Galicaster"
/opt/galicaster/run_galicaster.py >> /tmp/restart-galicaster.log &
