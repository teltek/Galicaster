#!/bin/bash

# kill galicaster
echo "----Running restart script----> `date`"  >> /var/log/galicaster/restart-galicaster.log
date
echo "Killing Galicaster"
pkill -u $USER python

echo "Waiting 10 sec for network to be established"
sleep 10

echo "Checking if rtsp2v4l2 is running"
/opt/galicaster/rtsp_keeprunning.sh >> /var/log/galicaster/rtsp_keeprunning.log

echo "Waiting 10 sec for rtsp2v4l2 to be established"
sleep 10

# start galicaster again
echo "Restarting Galicaster"
/opt/galicaster/run_galicaster.py & >> /var/log/galicaster/restart-galicaster.log
