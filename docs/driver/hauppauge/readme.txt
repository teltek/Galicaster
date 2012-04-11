Hauppauge Cards Configuration
=============================

The Hauppauge cards can be easily configured using the utility "v4l2-ctl" in the package "ivtv-utils" (until Ubuntu 10.10) or "v4l-utils" (Ubuntu 11.04 and above).


* Finding the right virtual device

Most Hauppauge cards create several virtual devices (i.e. several entries under the /dev directory).
Even though they correspond to the same physical device, each one has a different function (typically one for raw video and other for MPEG-encoded video), so you must make sure which is the right virtual device before proceeding. You can do this with the following command:

$ udevadm info --attribute-walk --name /dev/<device_file>

The first paragraph usually contains an attribute labelled "ATTR{name}" indicating the device function, e.g. "ivtv0 encoder MPG". Use it to know which specific device you want to connect to, or configure. 


* Setting the video standard

You can get the card's current video standard with

$ v4l2-ctl -S -d /dev/<device_file>

If you want to change it (e.g. you get NTSC but you want PAL), you can get a list of the supported video standards with:

$ v4l2-ctl --list-standards -d /dev/<device_file>

Find your preferred standard in the list and remember its index number. Then set the card to using that standard with:

$ v4l2-ctl -s <index> -d /dev/<device_file>


* Setting the input type

Most Hauppauge cards have composite video and supervideo inputs, but they can only fed from one of them at a time. To see the active input use:

$ v4l2-ctl -I -d /dev/<device_file>

You can get a list of available inputs with:

$ v4l2-ctl --list-inputs -d /dev/<device_file>

To set one of those inputs as active, you need the index number of the input (provided by the previous command):

$ v4l2-ctl -i <index> -d /dev/<device_file>

Note: Sometimes you may get several inputs for the same connector (e.g. "Composite1", "Composite2" and "Composite3"), but just one of them is fully operational. You have to guess the right one by trial and error.


* Additional tweaking

You may apply additional settings to your card with the v4l2-ctl tool. Just type "v4l2-ctl" in your shell and you will get a comprehensive list of available commands. 


* Making settings permanent

The settings applied with this tool will disappear between reboots. You can, however, write a script file with the appropriate commands and set it to run when the system starts.
