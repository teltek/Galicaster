noaudiodialog plugin
====================

Pops a warning dialog when the audio is low or muted.
--------------------------------------------


This plugin triggers a pop-up dialog on the Recorder Area when the audio is muted, the microphone batteries are depleted or the audio is too low.

Behaviour
---------

The dialog shows up when:

* An audio recording device is muted.
* An audio recording device does not have enough power or battery charge.
* The audio input level is too low. The threshold is configurable and defaults to -80dB (see the configuration section for details).

The dialog hides when:

* The audio input level goes +5dB above the configured threshold.
* The "Close" button is clicked. It will stay closed until the audio level goes over the threshold and falls again.
* [Disabled by default] The "Keep Closed" button is clicked. The dialog will remain closed, regardless the audio level, until:
  * A new recording is started.
  * The current recording is stopped.
  * A new profile is loaded.
  * The current profile is reloaded.
  * The application is restarted

Loading and configuration
-------------------------

In the configuration files, include the following sections with your values of choice:

[plugins]
noaudiodialog = True

[screensaver]
min = -80
keepclosed = False

True: Enables plugin.
False: Disables plugin.
min: A negative integer representing the 'silence' level in dB. Accepted values range between -100 and 0. Normal values are between -100 and -60. Defaults to -80.
keepclosed: Wether the "keep closed" feature is active or not. True | False
