Configure and control the Camera Control with Galicaster
====================================================

Galicaster controls the camera using the serial port, so we need to add the user galicaster to the group dialout, like follows (otherwise galicaster would need root privileges):

sudo usermod -a -G dialout galicaster


In order to activate the plugin:

[plugins]
cameracontrol = True

[cameracontrol]
path = /dev/ttyUSB0
zoom_levels = 7
max_speed_pan_tilt = 0x18
