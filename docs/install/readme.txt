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

# Glade package to use it on Python
$ sudo apt-get install phyton-glade2

  * N.B.: Until Ubuntu 10.10 (included), "ivtv-utils" must be used instead of "v4l-utils".

# (optional)pyGst
$ sudo pip install pygst

# (optional) python-bottle for the REST plugin
$ sudo apt-get install python-bottle

Configuration
-------------
The values are in the files conf-dist.ini and conf.ini. The values on conf.ini prevail over those on conf-dist.ini. Thus, it's posible to keep a default configuration separated from the current configuration, modifying just conf.ini.

Sections:

-- basic
   * repository: absolute path to the working folder. If not specified, a Repository directory in the user's home will be used.
   * export:  absolute path to the export folder for operations. If not specified, exported files will be placed at the user's home will be used.
   * stopdialog: Enable/Disable a dialog requesting confirmation to stop the recording. Defaults to True. (True|False)
   * quit: Shows or hides the quit button. (True|False)
   * admin: enables admin mode. (True|False)
      - False: By default, the user will only be allowed to make recordings. Galicaster will operate as a GClass
      - True: Apart from recording, the user can edit metadata, play and manage the recordings. Galicaster will behave as a GMobile

-- repository
   * Template for folder syntax on the repository. Useful on browsing through the repository via file manager. 
   Default value is gc_{hostname}_{year}-{month}-{day}T{hour}h{minute}m{second}. Los codigos que se puedes usar son:
      - {id}: MP's identifier.
      - {title}: MP's title.
      - {series}: ;MP's series title.
      - {hostname}: Agent name.
      - {type}: 'M' if the MP is recorded manually, 'S' if scheduled.
      - {longtype}: 'manual' if the MP is recorded manually, 'scheduled' if scheduled.
      - {year}: MP's year of recording, with century as a decimal number.
      - {month}: MP's month of recordink, as a decimal number [01,12].
      - {day}: MP's day of recording, as a decimal number [01,31].
      - {hour}: MP's hour of recording, as a decimal number [00,23].
      - {minute}: MP's minute of recording, as a decimal number [00,59].
      - {second}: MP's second of recording, as a decimal number [00,59].
      - {utcyear}: MP's  UTC year of recording, with century as a decimal number.
      - {utcmonth}: MP's UTC month of recordink, as a decimal number [01,12].
      - {utcday}: MP's UTC day of recording, as a decimal number [01,31].
      - {utchour}: MP's UTC hour of recording, as a decimal number [00,23].
      - {utcminute}: MP's UTC minute of recording, as a decimal number [00,59].
      - {utc second}: MP's UTC second of recording, as a decimal number [00,59].

-- ingest
   The data to connect Galicaster to an Opencast-Matterhorn server.
   * active: Enables the connection to a Opencast-Matterhorn server (True|False).
   * legacy: activates Openacast Matterhonr 1.2 and 1.3 compatibility, excluding the namespace field on the xml files from the mediapackages. (True|False) 
   * visible_tracks:Makes tracks visible to Matterhorn. If active, the tracks are selectable so only the chosen ones will be recorded.If not, Galicaster will record the tracks on the profile active at the moment of the scheduled start.
   * manual: Configure the method to automatically ingest the manual recordings. The possible options are: disable the automatic ingestion (none), ingest immediately after the recording (immediately) or ingest nightly all the recordings of the previous day (nightly). Defaults to 'none'. (none|immediately|nightly)
   * scheduled: Configure the method to automatically ingest the scheduled recordings. The possible options are: disable the automatic ingestion (none), ingest immediately after the recording (immediately) or ingest nightly all the recordings of the previous day (nightly). Defaults to 'none'. (none|immediately|nightly)
   * host: Matterhorn server URL.
   * username: Username for the account used to operate the Matterhorn REST endpoints service.
   * password: Password for the account  used to operate the Matterhorn REST endpoints service.
   * hostname: Name of the Galicaster unit. Defaults to the host name as defined in the OS, prepended by "GC-" if it is a Galicaster Class or "GCMobile-" if it is a Galicaster Mobile.
   * workflow: name of the workflow used to ingest the recordings.
   * workflow-parameters: pairs of parameter and value (parameter:value) to be parsed on the Matterhorn workflow, separated by semicolon.

-- track
   A section for each device used in the capturer. Each section is set according to the device type: test, v4l2, pulse, epiphan, datapath, hauppauge, blackmagic, firewire or rtp. For more information on device plugin configuration on docs/device/.  

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
