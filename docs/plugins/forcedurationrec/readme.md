forcedurationrec plugin
=======================

Limits recording duration.
--------------------------

This plugin is meant to stop manual recordings missed by the lecturer.

All recordings stop when they reach the maximum duration configured. 

Loading and configuring
-----------------------

In the configuration file, include the following code with your values of choice:

[plugins]
forcedurationrec = True

[forcedurationrec]
duration = 240

True: Enables plugin.
False: Disables plugin.
duration: An integer representing the maximum duration allowed for a recording, in minutes. Defaults 240 minutes (4 hours).
