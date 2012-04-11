#!/bin/bash

#Check versions
python -c "import pygtk; pygtk.require('2.0')"
python -c "import pygst; pygst.require('0.10')"
python -c "import pycurl"
python -c "import icalendar"

#GST Play
gst-launch v4l2src num-buffers=25 ! video/x-raw-yuv,width=800,framerate=24/1 ! ffmpegcolorspace ! xvimagesink

# GST Rec
gst-launch v4l2src num-buffers=25 ! video/x-raw-yuv,width=800,framerate=24/1 ! ffmpegcolorspace ! x264enc pass=5 quantizer=22 speed-preset=4 profile=1 ! queue ! avimux ! filesink location=out.avi
file out.avi
rm out.avi