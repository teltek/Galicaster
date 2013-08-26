cleanstale plugin
=================

Cleans old recordings
--------------------

This plugin deletes every recording older than a certain threshold. It is meant to keep enough free space on the hard drive, assuming the copies of the media in the recording units are not used as backup.

Loading and configuration
-----------------------

In the configuration file, include the following code with your values of choice:

[plugins]
cleanstale = True

[cleanstale]
maxarchivaldays = 30

True: Enables plugin.
False: Disables plugin.
maxarchivaldays: An integer representing number of days the recording will be kept. Defaults to 30.
