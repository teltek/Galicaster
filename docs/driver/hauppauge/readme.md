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


* Force 'cardtype' parameter in the 'ivtv' module (advanced)

The list of cards supported by this module can be obtained with the command "modinfo ivtv":

 1 = WinTV PVR 250
 2 = WinTV PVR 350
 3 = WinTV PVR-150 or PVR-500
 4 = AVerMedia M179
 5 = YUAN MPG600/Kuroutoshikou iTVC16-STVLP
 6 = YUAN MPG160/Kuroutoshikou iTVC15-STVLP
 7 = YUAN PG600/DIAMONDMM PVR-550 (CX Falcon 2)
 8 = Adaptec AVC-2410
 9 = Adaptec AVC-2010
 10 = NAGASE TRANSGEAR 5000TV
 11 = AOpen VA2000MAX-STN6
 12 = YUAN MPG600GR/Kuroutoshikou CX23416GYC-STVLP
 13 = I/O Data GV-MVP/RX
 14 = I/O Data GV-MVP/RX2E
 15 = GOTVIEW PCI DVD
 16 = GOTVIEW PCI DVD2 Deluxe
 17 = Yuan MPC622
 18 = Digital Cowboy DCT-MTVP1
 19 = Yuan PG600V2/GotView PCI DVD Lite
 20 = Club3D ZAP-TV1x01
 21 = AverTV MCE 116 Plus
 22 = ASUS Falcon2
 23 = AverMedia PVR-150 Plus
 24 = AverMedia EZMaker PCI Deluxe
 25 = AverMedia M104 (not yet working)
 26 = Buffalo PC-MV5L/PCI
 27 = AVerMedia UltraTV 1500 MCE
 28 = Sony VAIO Giga Pocket (ENX Kikyou)
 0 = Autodetect (default)
 -1 = Ignore this card

The 'cardtype' parameter indicates which type of card is expected by the driver. It defaults to 0 (detect card type automatically), but if this detection fails there is a way to force which card type will be used. The following instructions (need to be the superuser) configure the driver to work with a specific card type:

echo options ivtv cardtype=XX > /etc/modprobe.d/hauppauge.conf
depmod -a

, where XX is the card type, as specified in the list above.
