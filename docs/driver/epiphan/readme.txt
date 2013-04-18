Epiphan Driver installation
===========================

* Download the drivers at [http://www.epiphan.com/downloads/linux/index.php?dir=deb/]
You should choose the driver according with some characteristics of your computer and operating system. Newer drivers are in the form of DEB packages.

* Run the following commands to retrieve the kernel release and architecture:
uname -rm
>3.2.0-38-generic x86_64

To install the driver double-click in the DEB package. Ignore the error given by the Ubuntu Software Center. We recommend using the 3.27.7.25 version or upper.

Driver configuration
====================

To work with Epiphan USB and PCI based devices with Galicaster a certain configuration should be set that ensures a continuos stream, even on unplugging, and a fix resolution, with scaling activated.

* Scaling options:
0: V2UScaleNone -No scaling
1: V2UScaleModeNearestNeighbor - Nearest neighbor algorithm
2: V2UScaleModeWeightedAverage - Weighted average algorithm
3: V2UScaleModeFastBilinear - Fast bilinear
4: V2UScaleModeBilinear - Bilinear
5: V2UScaleModeBicubic - Bicubic
6: V2UScaleModeExperimental - Experimental
7: V2UScaleModePoint - Nearest neighbour 2
8: V2UScaleModeArea - Weighted average
9: V2UScaleModeBicubLin - Luma bicubic, chroma bilinear
10: V2UScaleModeSinc - Sinc
11: V2UScaleModeLanczos - Lanczos
12: V2UScaleModeSpline - Natural bicubic spline


VGA2USB and DVI2USB
-------------------

* Minimum configuration:
echo options vga2usb v4l2_err_on_nosignal=0 > /etc/modprobe.d/epiphan.conf

* Fix the resolution by adding the following lines with your target resolution to the previous file:

options vga2usb v4l_default_width=1280
options vga2usb v4l_default_height=720
options vga2usb v4l_nosig_img_width=1280
options vga2usb v4l_nosig_img_height=720
options vga2usb v4l_scalemode=4

Note: Default and nossig resolutions must match.

* Restart the computer to load the driver, or execute as root 
modprobe vga2pci

VGA2PCI and DVI2PCI
-------------------

* Minimum configuration:
echo options vga2pci v4l2_err_on_nosignal=0 > /etc/modprobe.d/epiphan.conf

* Fix the resolution by adding the following lines with your target resolution to the previous file:
options vga2pci v4l_default_width=1280
options vga2pci v4l_default_height=1024
options vga2pci v4l_nosig_img_width=1280
options vga2pci v4l_nosig_img_height=1024
options vga2pci v4l_scalemode=4

Note: Default and nossig resolutions must match.

* Restart the computer to load the driver, or execute as root:
modprobe vga2pci

Device identification
====================

Find the Device name attribute:
* udevadm info --attribute-walk --name=/dev/video0 | grep name
Usual Device IDs:
* vga2usb, vga2pci, dvi2pci
Fix access path
* Create or modify the file /etc/udev/rules.d/galicaster.rules.
* Add the line: KERNEL=="video\[0-9\]*", ATTR\{name\}=="DVI2PCIe", GROUP="video", SYMLINK+="webcam"


Module configuration
====================

Admitted values:
----------------

{name}: Name assigned to the device.
{device}: Device type: epiphan
{flavor}: Matterhorn "flavor" associated to the track. (*presenter|presentation|other)
{location}}: Device's mount point in the system (e.g. /dev/screen).
{file}}: The file name where the track will be recorded. (default:CAMERA.avi)
{drivertype}}: Wheter the device use a v4l or a v4l2 interface to guarantee compatibility (v4l|v4l2)
As for Ubuntu 10.10 use 'v4l'. Otherwise 'v4l2' (default value)
{resolultion}:Output resolution
{framerate}: Output framerate

Example:
--------

[track1]
name = Epiphan
device = epiphan
flavor = presentation
location = /dev/screen
file = SCREEN.avi
active = True
drivertype = v4l2

Troubleshooting
===============

* Incompatibility with Blackmagic capture cards
Due to a conflict between the drivers of Blackmagic and Epiphan cards drivers, their devices are incompatible one to the other. Combinations of these devices with ones or other vendor others has been succesfully tested.

* Problems with resolution change
If you expirience problems with resolution changes please make sure all the parameters on the driver configurartion match the syntax. Resolutions should be scaled to the default resolution defined. Also, check your driver version, drivers older than 3.27.7.5 may present scaling problems.

* Panoramic resolution scaling
Panoramic resolution aspect won't be respected when default resolution is 4:3. To use panoramic resoultion better use a panoramic default resolution. When combining 4:3 and 16:9 and other ratios introduce auxiliary hardware such as VGA scalers.
