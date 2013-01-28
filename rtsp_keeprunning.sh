#!/bin/bash
#make-run.sh
#make sure a process is always running.

#export DISPLAY=:0 #needed if you are running a simple gui app.
room=`cat /opt/galicaster/roomname`
process=v4l2sink
makerun="/opt/galicaster/rtsp2v4l2"

if ps ax | grep -v grep | grep $process > /dev/null
then
	echo "OK is running"
 	exit
else
	echo "NOK trying to start room $room"		
        $makerun $room &
fi

exit
