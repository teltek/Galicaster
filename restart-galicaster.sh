#!/bin/bash
log="/var/log/galicaster/restart-galicaster.log"
rtsp_log="/var/log/galicaster/rtsp_keeprunning.log"
# kill galicaster
echo "----Running restart script----> `date`"  >> $log
date
echo "Killing Galicaster"
pkill  -9 -u $USER python

echo "Waiting 10 sec for network to be established"
sleep 10

echo "Checking if rtsp2v4l2 is running"
file=/opt/galicaster/rtsp_keeprunning.sh
if [ -f $file ];
then
	echo "file exist"
	$file >> $rtsp_log
fi

echo "Waiting 10 sec for rtsp2v4l2 to be established"
sleep 10

# start galicaster again
echo "Restarting Galicaster"
/opt/galicaster/run_galicaster.py & >> $log
