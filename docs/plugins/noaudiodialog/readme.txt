Dialog warning that the audio is too low
========================================

If this plugin is active, a dialog will pop up, warning the audio level is too low. This dialog is only shown in the recording screen. It is useful for the lecturers to notice the state of Galicaster easily, or to let them have a warning when there are problems with the microphone.

When the audio is recovered, the dialog disappears. If necessary, it can also be closed manually.


To activate/deactivate this warning:

[plugins]
noaudiodialog = True

Once activated the default configuration sets the threshold to 0 and -60 dB. 
This configuration is commom with the vu-meter, so values inferior to -60 dB will be shown as -40 dB (empty bar).

To set the threshold values add this lines with your choice levels to the configuration files, for example:

[audio]
min = -40
max = -10
