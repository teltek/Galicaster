Blackmagic Device module configuration
======================================

Compatibility
-------------

Blackmagic Intesity Series
Blackmagic Decklink Series (PCIe only)
Blackmagic Multibridge Series


Admitted values:
---------------

name: Name assigned to the device.
device: Device type: blackmagic
location: Device's mount point in the system.
file: The file name where the track will be recorded.
flavor: Opencast "flavor" associated to the track. (presenter|presentation|other)
input: Input signal format. (sdi|hdmi|opticalsdi|component|composite|svideo)
input-mode: Input video mode and framerate (eg. 1080i60). More information here.
audio-input: Input audio mode (none|auto|embedded|aes|analog). More information here.
subdevice: Select a Blackmagic card from a maximum of 4 devices (0-3, Default: 0)
audio-input: Input audio mode (none|auto|embedded|aes|analog). More information here.
vumeter: Activates data sending to the program's vumeter. (True|False) Only one device should be activated.
player: Whether the audio input would be played on preview. (True|False)
amplification: Gstreamer amplification value: < 1 decreases and > 1 increases volume. Values between 1 and 2 are commonly used. (0-10)

Examples
--------

--Decklink with SDI and audio automatic

[track1]
name = Decklink
device = blackmagic
flavor = presenter
file = CAMERA.avi
location = /dev/blackmagic0
input = sdi
input-mode = 720p50
audio-mode = auto
subdevice=0
vumeter = True
player = False
amplification = 1.0

--HDMI at 1080p 50 fps without audio

[track2]
name = BlackmagicHDMI
device = blackmagic
location = /dev/blackmagic1
file = CAMERA.avi
flavor = presentation
input = hdmi
input-mode = 1080p50
audio-mode = none
subdevice = 0
