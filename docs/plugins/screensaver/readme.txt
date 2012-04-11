Configure and control the Screensaver with Galicaster
====================================================

Galicaster controls the screensaver using Xorg tools. In order for this to work correctly, any other screensaver tool must be disabled (i.e. power management, dpms, gnome-screensaver, etc.)

The screensaver will be disabled one minute before the start of a scheduled recording, and as long as there is an active recording.

The screensaver will hide the screen after a given period of inactivity. This period can be configured using the 'screensaver' parameter in the conf.ini file, indicating the seconds of inactivity:

[screensaver]
inactivity = 60


To activate/deactivate the screensaver:

[plugins]
screensaver = True
