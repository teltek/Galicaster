Firewire Device module configuration
====================================

Compatibility
-------------

Most Firewire cardas and DV cameras

Admmited values:
----------------

name: Name assigned to the device.
device: Device type: firewire
flavor: Opencast "flavor" associated to the track. (presenter|presentation|other)
location: Device's mount point in the system (e.g. /dev/video0).
file: The file name where the track will be recorded.
vumeter: Activates data sending to the program's vumeter. (True|False) Only one device should be activated.
player: Whether the audio input would be played on preview. (True|False)
format: Input signal format. (dv|hdv|iidc)

Examples
--------

[track1]
name = Firewire
device = firewire
flavor = presenter
location = /dev/fw0
file = CAMERA.dv
format = dv
vumeter = True
player = True
