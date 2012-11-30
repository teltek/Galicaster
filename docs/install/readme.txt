INSTALL
========

Dependencies
------------

# Python, Glib, Gobject and GTK2 in Linux

# Gstreamer
$ sudo apt-get install \
    gstreamer0.10-ffmpeg gstreamer0.10-alsa gstreamer0.10-plugins-bad gstreamer0.10-plugins-bad-multiverse \
    gstreamer0.10-plugins-base gstreamer0.10-plugins-base-apps gstreamer0.10-plugins-good \
    gstreamer0.10-plugins-ugly 
$ sudo apt-get install libfaac0 

# python-setuptools and pip
$ sudo apt-get install python-pip python-setuptools

# iCalendar
$ sudo pip install icalendar=

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
   * export:  absolute path to the export folder for operations. If not specified, exported files will be placed at the user's home will be used.
   * stopdialog: Enable/Disable a dialog requesting confirmation to stop the recording. Defaults to True. (True|False)
   * quit: Shows or hides the quit button. (True|False)
   * admin: enables admin mode (True|False)
      - False: By default, the user will only be allowed to make recordings. Galicaster will operate as a GClass
      - True: Apart from recording, the user can edit metadata, play and manage the recordings. Galicaster will behave as a GMobile

-- screen
   * left: Name of the video device in the track list to be shown in the left screen (None to deactivate).
   * right: Name of the video device in the track list to be shown in the right screen (None to deactivate).
   Note that if a profile differnt from default is selected, they will be ordered automatically via track position

-- ingest
   The data to connect Galicaster to an Opencast-Matterhorn server.
   * active: Enables the connection to a Opencast-Matterhorn server (True|False).
   * manual: Configure the method to automatically ingest the manual recordings. The possible options are: disable the automatic ingestion (none), ingest immediately after the recording (immediately) or ingest nightly all the recordings of the previous day (nightly). Defaults to 'none'. (none|immediately|nightly)
   * scheduled: Configure the method to automatically ingest the scheduled recordings. The possible options are: disable the automatic ingestion (none), ingest immediately after the recording (immediately) or ingest nightly all the recordings of the previous day (nightly). Defaults to 'none'. (none|immediately|nightly)
   * host: Matterhorn server URL.
   * username: Name of the Galicaster unit. Defaults to the host name as defined in the OS, prepended by "GC-" if it is a Galicaster Class or "GCMobile-" if it is a Galicaster Mobile.
   * password: Password for the account  used to operate the Matterhorn REST endpoints service.
   * hostname: Nombre del equipo galicaster. Por defacto se obtiene del sistema operativo
   * workflow: name of the workflow used to ingest the recordings.
   * workflow-parameters: pairs of parameter and value (parameter:value) to be parsed on the Matterhorn workflow, separated by semicolon.

-- track
   A section for each device used in the capturer. Each section is set according to the device type: test, v4l2, pulse, vga2usb, hauppauge or blackmagic:

 [] videotest: Mock video device.
       * name: Name assigned to the device.
       * device: Device type: videotest
       * flavor: Matterhorn "flavor" associated to the track. (presenter|presentation|other)
       * location: Device's mount point in the system (e.g. /dev/video0).
       * file: The file name where the track will be recorded.
       * active: Whether the device will be played and recorded. (True|False)
       * caps:  GStreamer capabilities of the device.
       * pattern: type of pattern to show. Run gst-inspect-0.10 videotestsrc fore more information. (0-20)
       * color1:  pattern foreground color, indicated on Big endian ARGB. Run gst-inspect-0.10 videotestsrc fore more information. (0,4294967495)
       * color2: pattern background color, indicated on Big endian ARGB. Run gst-inspect-0.10 videotestsrc fore more information. (0,4294967495)


       Pattern options
       	 	 	   (0): smpte            - SMPTE 100% color bars
                           (1): snow             - Random (television snow)
                           (2): black            - 100% Black
                           (3): white            - 100% White
                           (4): red              - Red
                           (5): green            - Green
                           (6): blue             - Blue
                           (7): checkers-1       - Checkers 1px
                           (8): checkers-2       - Checkers 2px
                           (9): checkers-4       - Checkers 4px
                           (10): checkers-8       - Checkers 8px
                           (11): circular         - Circular
                           (12): blink            - Blink
                           (13): smpte75          - SMPTE 75% color bars
                           (14): zone-plate       - Zone plate
                           (15): gamut            - Gamut checkers
                           (16): chroma-zone-plate - Chroma zone plate
                           (17): solid-color      - Solid color
                           (18): ball             - Moving ball
                           (19): smpte100         - SMPTE 100% color bars
                           (20): bar              - Bar

 [] audiotest: Mock audio device.
       * name: Name assigned to the device.
       * device: Device type: pulse
       * flavor: Matterhorn "flavor" associated to the track. (presenter|presentation|other)
       * location: PulseAudio source name. Use default to select the same Input as the Sound Control. To list PulseAudio devices run: `pactl list | grep "Source" -A 5` and use "Name:" as the location field.
       * file: The file name where the track will be recorded.
       * wave: Generated waveform sample. Run gst-inspect-0.10 audiotestsrc fore more information. (0-12)
       * frequency: Test signal central frequency. (0-20000)
       * volume: Percent volume of the pattern. (0-1)
       * active: Whether the device will be played and recorded. (True|False)
       * vumeter: Activates data sending to the program's vumeter. (True|False) Only one device should be activated.
       * amplification: Gstreamer amplification value: < 1 decreases and > 1 increases volume. Values between 1 and 2 are commonly used. (0-10)
       * player:  Whether the audio input would be played on preview. (True|False)  

       Wave options
			   (0): sine             - Sine
                           (1): square           - Square
                           (2): saw              - Saw
                           (3): triangle         - Triangle
                           (4): silence          - Silence
                           (5): white-noise      - White uniform noise
                           (6): pink-noise       - Pink noise
                           (7): sine-table       - Sine table
                           (8): ticks            - Periodic Ticks
                           (9): gaussian-noise   - White Gaussian noise
                           (10): red-noise        - Red (brownian) noise
                           (11): blue-noise       - Blue noise
                           (12): violet-noise     - Violet noise



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
       * player:  Whether the audio input would be played on preview. (True|False)  
       * amplification: Gstreamer amplification value: < 1 decreases and > 1 increases volume. Values between 1 and 2 are commonly used. (0-10)

   [] v4l2: Video device.
       * name: Name assigned to the device.
       * device: Device type: v4l2
       * flavor: Matterhorn "flavor" associated to the track. (presenter|presentation|other)
       * location: Device's mount point in the system (e.g. /dev/video0).
       * file: The file name where the track will be recorded.
       * active: Whether the device will be played and recorded. (True|False)
       * caps:  GStreamer capabilities of the device.
       * Videocrop: Margin in pixels to be cutted. Useful to set a 4:3 proportion on a HD webcam.videocrop-top, videocrop-bottom, videocrop-left, videocrop-right (optional).

    [] vga2usb: Video device
       * name: Name assigned to the device.
       * device: Device type: vga2usb
       * flavor: Matterhorn "flavor" associated to the track. (presenter|presentation|other)
       * location: Device's mount point in the system (e.g. /dev/video0).
       * file: The file name where the track will be recorded.
       * active: Whether the device will be played and recorded. (True|False)
       * drivertype: Wheter the device use a v4l or a v4l2 interface to guarantee compatibility (v4l|v4l2)

    [] blackmagic: Video device.
       * name: Name assigned to the device.
       * device: Device type: blackmagic
       * flavor: Matterhorn "flavor" associated to the track. (presenter|presentation|other)
       * location: Device's mount point in the system (e.g. /dev/video0).
       * file: The file name where the track will be recorded.
       * active: Whether the device will be played and recorded. (True|False)
       * videocrop: Margin in pixels to be cutted. Useful to set a 4:3 proportion on a HD webcam.videocrop-top, videocrop-bottom, videocrop-left, videocrop-right (optional).  
       * input: Input signal format. (sdi|hdmi|opticalsdi|component|composite|svideo)
       * input-mode: Input vidoe mode and framerate (1-20). Run 'gst-inpect-0.10 decklink' on a shell for more information.
       * audio-input: Wheter the audio is recorded and type. (auto|aes|analog|none)
       * subdevice: In case several Blackmagic cards are avaliable - up to 4-, select which to run. (0-3)
       * vumeter: Activates data sending to the program's vumeter. (True|False) Only one device should be activated.
       * player:  Whether the audio input would be played on preview. (True|False)  
       * amplification: Gstreamer amplification value: < 1 decreases and > 1 increases volume. Values between 1 and 2 are commonly used. (0-10)
       
    [] firewire: Video and audio device.
       * name: Name assigned to the device.
       * device: Device type: blackmagic
       * flavor: Matterhorn "flavor" associated to the track. (presenter|presentation|other)
       * location: Device's mount point in the system (e.g. /dev/video0).
       * file: The file name where the track will be recorded.
       * active: Whether the device will be played and recorded. (True|False)
       * format: Input signal format. (dv|hdv,iidc)
       * vumeter: Activates data sending to the program's vumeter. (True|False) Only one device should be activated.
       * player:  Whether the audio input would be played on preview. (True|False)  


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
