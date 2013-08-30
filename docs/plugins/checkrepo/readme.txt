Checkrepo Plugin
=================

Checks for a non-started scheduled recording
--------------------------------------------

If the Galicaster unit is turned on after a scheduled recording should had been started, the recording will be lost. This pluging helps mitigating this problem by checking for a recording that should have already been started and starting it immediately for the remaining time.
Behaviour

The plugin looks for recordings that should be currently running. If there is any, it is started immediately with its metadata - duration and start time - modified appropriately. The recovered recording will run for the remaining time only. 

An example:

* Recording scheduled from 10am to 12am.
* Computer started at 10:20.
* The recording will run from 10:20 to 12:00, resulting on a video 1 hour and 40 minutes long.

Loading
-------

To activate the plugin, add the line in the 'plugins' section of your configuration file.

[plugins]
checkrepo = True

True: Enables plugin.
False: Disables plugin.
