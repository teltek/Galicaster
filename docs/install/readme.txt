INSTALL
========

Dependencies
------------

# Python, Glib, Gobject and GTK2 in Linux

# Gstreamer
$ sudo apt-get install \
    gstreamer0.10-ffmpeg gstreamer0.10-alsa gstreamer0.10-plugins-bad gstreamer0.10-plugins-bad-multiverse \ 
    gstreamer0.10-plugins-base gstreamer0.10-plugins-base-apps gstreamer0.10-plugins-good \
    gstreamer0.10-plugins-ugly gstreamer0.10-plugins-ugly-multiverse

# python-setuptools and pip
$ sudo apt-get install python-pip python-setuptools

# iCalendar
$ sudo pip install icalendar=2.2

# pyCurl
$ sudo apt-get install python-pycurl

# Capture card configuration tools
$ sudo apt-get install v4l-conf v4l-utils guvcview

  * N.B.: Until Ubuntu 10.10 (included), "ivtv-utils" must be used instead of "v4l-utils".

# (optional)pyGst
$ sudo pip install pygst


Configuration
-------------
The values are in the files conf-dist.ini and conf.ini. The values on conf.ini prevail over those on conf-dist.ini. Thus, it's posible to keep a default configuration separated from the current configuration, modifying just conf.ini.

Sections:

-- basic
   * repository: absolute path to the working folder. If not specified, a Repository directory in the user's home will be used.
   * admin: enables admin mode (True|False)
      - False: By default, the user will only be allowed to make recordings. Galicaster will operate as a GClass
      - True: Apart from recording, the user can edit metadata, play and manage the recordings. Galicaster will behave as a GMobile

-- screen
   * left: Name of the video device in the track list to be shown in the left screen (None to deactivate).
   * right: Name of the video device in the track list to be shown in the right screen (None to deactivate).
   * quit: Shows or hides the quit button. (True|False)

-- ingest
   The data to connect Galicaster to an Opencast-Matterhorn server.
   * active: Enables the connection to a Opencast-Matterhorn server (True|False).
   * default: Enables the nocturn ingest of the recordings (True|False)
   * host: Matterhorn server URL.
   * username: Account used to operate the Matterhorn REST endpoints service.
   * password: Password for the account  used to operate the Matterhorn REST endpoints service.
   * workflow: name of the workflow used to ingest the recordings.
   * workflow-parameters: pairs of parameter and value (parameter:value) to be parsed on the Matterhorn workflow, separated by semicolon.

-- track
   A section for each device used in the capturer. Each section is set according to the device type: hauppauge, pulse, v4l2 or vga2usb:

   [] hauppauge: Audio and Video device.
       * name: Name assigned to the device.
       * device: Device type: hauppauge
       * flavor: Matterhorn "flavor" associated to the track. (presenter|presentation|other)
       * location: Device's mount point of the MPEG output  (e.g. /dev/video0).
       * locprevideo: Device's mount point of the RAW output  (e.g. /dev/video32).
       * locpreaudio: Device's mount point of the PCM output  (e.g. /dev/video24).
       * file: The file name where the track will be recorded.
       * active: Whether the device will be played and recorded. (True|False)
       * vumeter: Whether the audio input would be represented on the vumeter. (True|False) 
       * player:  Whether the audio input would be played on preview. (True|False) 

   [] pulse: Audio device.
       * name: Name assigned to the device.
       * device: Device type: pulse
       * flavor: Matterhorn "flavor" associated to the track. (presenter|presentation|other)
       * location: PulseAudio source name. Use default to select the same Input as the Sound Control. To list PulseAudio devices run: `pactl list | grep "Source" -A 5` and use "Name:" as the location field.
       * file: The file name where the track will be recorded.
       * active: Whether the device will be played and recorded. (True|False)
       * vumeter: Activates data sending to the program's vumeter. (True|False) Only one device should be activated.
       * amplification: Gstreamer amplification value: < 1 decreases and > 1 increases volume. Values between 1 and 2 are commonly used.

   [] v4l2: Video device.
       * name: Name assigned to the device.
       * device: Device type: v4l2
       * flavor: Matterhorn "flavor" associated to the track. (presenter|presentation|other)
       * location: Device's mount point in the system (e.g. /dev/video0).
       * file: The file name where the track will be recorded.
       * active: Whether the device will be played and recorded. (True|False)
       * caps:  GStreamer capoabilities of the device.
       * Videocrop: Margin in pixels to be cutted. Useful to set a 4:3 proportion on a HD webcam.videocrop-top, videocrop-bottom, videocrop-left, videocrop-right (optional).

    [] vga2usb: Video device
       * name: Name assigned to the device.
       * device: Device type: vga2usb
       * flavor: Matterhorn "flavor" associated to the track. (presenter|presentation|other)
       * location: Device's mount point in the system (e.g. /dev/video0).
       * file: The file name where the track will be recorded.
       * active: Whether the device will be played and recorded. (True|False)
       * drivertype: Wheter the device use a v4l or a v4l2 interface to guarantee compatibility (v4l|v4l2)

    [] Blackmagic: Video device.
       * name: Name assigned to the device.
       * device: Device type: blackmagic
       * flavor: Matterhorn "flavor" associated to the track. (presenter|presentation|other)
       * location: Device's mount point in the system (e.g. /dev/video0).
       * file: The file name where the track will be recorded.
       * active: Whether the device will be played and recorded. (True|False)
       * input: Input signal format. (sdi|hdmi|opticalsdi|component|composite|svideo)
       * input-mode: Input vidoe mode and framerate (1-20). Run 'gst-inpect-0.10 decklink' on a shell for more information.

-- allows
   Scheduling and UI permissions.
   All "True" by default, except "overlap"
   * manual = If True, the user can start and stop recordings in the user interface.
              If False, those controls depend on the parameters "start" and "stop" values, respectively.
   * stop = When "manual" is False, controls whether the recording can be stopped from the user interface. (True|False)
   * start = When "manual" is False, controls whether the recording can be started from the user interface. (True|False)
   * pause = Controls whether the recording can be paused/resumed from the user interface. (True|False)
             This is independent from the value of the "manual" parameter. 
   * overlap = If "True", the manual recordings take priority over the scheduled ones, and vice-versa. This means: 
                  If, when a scheduled recording has to start, there is another (manual) one running:
                  - If "overlap" is True, the scheduled recording does not start.
               -    If "overlap" is False, the current recording stops, and the scheduled one starts.


Running
---------
Galicaster Class is launched by running the command:
   
   ./run_galicaster.py
