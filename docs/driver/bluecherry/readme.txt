Bluecherry cards configuration
===================================

Test Bluecherry BC-H04120A 4 port H.264 video and audio encoder / decoder captura card


INSTALL
--------------------------------------
sudo aptitude install linux-source
git clone git://github.com/bluecherrydvr/solox10.git
cd solo6x10
make
sudo make install
sudo depmod -a
echo "options solo6x10 video_type=1" > /etc/modprobe.d/solo6x10.conf
echo "softdep solo6x10 pre: videobuf-core videobuf-dma-sg snd-pcm snd videodev videobuf-dma-contig v4l2-common post:" >> /etc/modprobe.d/solo6x10.conf




CONFIG
--------------------------------------
v4l2-ctl --list-devices
v4l2-ctl --list-inputs -d /dev/video2
v4l2-ctl -d /dev/video2 -i 0
#TEST ROW 704x576
gst-launch-0.10 -v v4l2src device=/dev/video2 ! video/x-raw-yuv, width=704, height=576 ! ffmpegcolorspace ! xvimagesink

#TEST H264 352x288
gst-launch-0.10 -v filesrc location=/dev/video3 ! h264parse ! ffdec_h264 ! ffmpegcolorspace ! xvimagesink

#TEST H264 704x576
v4l2-ctl -d /dev/video3 -v width=704,height=576,pixelformat=MPEG
gst-launch-0.10 -v filesrc location=/dev/video3 ! h264parse ! ffdec_h264 ! ffmpegcolorspace ! xvimagesink


URL'S
--------------------------------------
http://community.bluecherrydvr.com/responses/ubuntu1204-fail-install
