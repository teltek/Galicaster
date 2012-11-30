Blackmagic cards configuration
===================================

To capture with Blackmagic cards we need to use a exclusive gstreamer element called 'decklinksrc'. In case we don't have it installed, we should do it manually. To do so follow these instructions: 


Compile the Gstreamer element
-----------------------------

Run in a shell:
$ svn checkout http://gforge.unl.edu/svn/gst-decklink
Use 'anonymous' as user and leave the password blank to checkout.

Before compiling, install the development tools for Gstreamer:

$ sudo aptitude install libgstreamer0.10-dev libgstreamer0.10-dev

Compile the element: 

$ ./configure
$ make
$ sudo make install 

To load the compiled module:

$ sudo cp -v /usr/local/lib/gstreamer-0.10/libgstdecklink.* /usr/lib/gstreamer-0.10/

Delete the Gstreamer registry and force it to reload:
sudo rm ~/.gstreamer-0.10/registry.*.bin
gst-inspect-0.10


Driver installation
------------------

Now you should proceed with the card driver. To install their driver you should download the latest one on:

http://blackmagic-design.com/support/
Choose Linux, your card series and your Model and press Search. Download the latest Desktop Video for Linux.

To install it:

$ dpkg -i <name_of_driver_package.deb>
$ modprobe blackmagic

There is a full guide on how to install the driver and other information on:
http://blackmagic-design.com/media/3397979/Blackmagic_Desktop_Video_Linux_9.2.txt

Check the driver's installation
-------------------------------

Run on a terminal:

$ lspci | grep Blackmagic
$ lsmod | grep blackmagic
$ ls dev/blackmagic/*

You will receive messages like:

$ 02:00.0 Multimedia video controller: Blackmagic Design Device a11b
$ blackmagic 2082944 1
$ /dev/blackmagic/card0

URL's
-----------------------------------
http://blackmagic-design.com/media/3913819/Blackmagic_Desktop_Video_Linux_9.5.tar.gz
http://blackmagic-design.com/media/3397912/Blackmagic_Desktop_Video_Linux_9.2.tar.gz
http://blackmagic-design.com/media/2432845/Blackmagic_Desktop_Video_Linux_9.0.tar.gz
