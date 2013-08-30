pushpic plugin
=======================

Creates and send a screenshoot to Dashboard periodically.
---------------------------------------------------------

This plugin is meant to work together with Galicaster Dashboard.

The periodicity is determined by the long period signal of the galicaster.core.heartbeat module, by default 60 seconds. If used as a script, the periodicity is determined by an internal variable (see 'Loading and configuraing as a script').

Every period a screenshoot is made of the active desktop - regardless the application is present or on fullscreen mode. The image is then send to the agent screenshot endpoint.

This plugin can be used with a script present on the Galicaster installation tree at docs/scripts/run_dashboard_push.py. To run the script copy it into a location of your choice and establish the path to a Galicaster installation:
- by default the folder is the one of a DEB installation: /usr/share/galicaster
- set the path as an enviromental variable: GALICASTER_PATH
- modify the script to use a custom folder instead of /usr/share/galicaster

Loading and configuring as a plugin
-----------------------------------

In the configuration file, include the following code with your values of choice:

[plugins]
pushpic = True

True: Enables plugin.
False: Disables plugin.

Running and configuring as a script
-----------------------------------

The script send a picture periodically, by default 60 seconds. Modify the variable sleep_period in the script if you want to change the time between screenshoots.

You can run the script via:

* python run_dashboard_push.py
* ./run_dashboard_push.py
** You need execution priviledges

The script functioning is independent of the Galicaster instance running. It will work even when Galicaster is not active.
