QRcode Plugin
=================

Using a specified string encoded as a QRcode image, while recording the recording can be paused when the QRcode is
displayed on the video.
--------------------------------------------

With QRcode enabled whenever a specific QR code is displayed in the Gstreamer video pipeline in Galicaster it can be
used to pause the recording. no video or audio is written to file during this time. This allows a novel method to do
on-the-fly live editing of captured video and audio. This also removes the need for editing software or editing skills.
the only requirement is to include an agreed QR code image into the slides or to be displayed on camera.

Things to note
--------------

QR codes have up to 30% error correction redundancy, for real world application its worth considering a high-redundnacy
QR code image being used with this plugin. http://blog.qrstuff.com/2011/12/14/qr-code-error-correction

Use of this plugin is optimised with mono-stream video of the slides. using a camera or FMV may have an impact on recording
performance (hardware dependant). Its worth looking at the QRcode config options `rescale`, `drop_frames` and `buffers`
to help tune performance.

Using this plugin to do the editing on the Opencast server was planned but not implemented therefore the options
`mp_add_edits` and `mp_add_smil` are best left as `False`

Loading
-------

To activate the plugin, add the line in the 'plugins' section of your configuration file.

[plugins]
qrcode = True

True: Enables plugin.
False: Disables plugin.

Plugin Options
--------------

[qrcode]
pause_mode = hold
hold_code = pause
stop_code = stop
start_code = start
rescale = 640x360
mp_add_edits = False
mp_force_trimhold = False
mp_add_smil = False
drop_frames = True
buffers = 200
hold_timeout = 1
ignore_track_name =


pause_mode: string [hold, start_stop] specifies the pause behaviour, either pause while a QR code is displayed automatically restarting or pause and start again on two separate QR codes
hold_code: any string. This will match the displayed QR code and pause the recording until the QR code is removed
stop_code: any string. This will match the displayed QR code and will pause a recording indefinitely
start_code: any string. This will match the displayed QR code and will start a paused recording
rescale: string (pixel resolution format). rescales the input frames for analysis. a lower resolution helps ease processing load
mp_add_edits: boolean. Add edit times into the mediapackage for possible further processing in Opencast (NOT IMPLEMENTED)
mp_force_trimhold: boolean. force the mediapackge with the QR code editing recording to use a trimHold workflow in Opencast
mp_add_smil: boolean. Add smil file into the mediapackage to be used for possible further processing in Opencast (NOT IMPLEMENTED)
drop_frames: boolean. Drop frames from the pipeline buffer in the Gstreamer pipeline. useful when processing FMV so the pipeline doesnt slow down with QRcode
buffers: integer [default: 200]. setting the 'max-size-buffers' value for the gstreamer pipeline. useful to configure so pipeline doesnt slow down with QRcode
hold_timeout: integer, time in seconds. The period of time to wait after the 'hold_code' is removed before resuming recording in the pipeline.
ignore_track_name: list of strings, separated by ','. This will turn off QRcode scanning of the track name that matches in this list.