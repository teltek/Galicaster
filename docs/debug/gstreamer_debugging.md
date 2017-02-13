Gstreamer Debugging
===================

 Applications can make use of the extensive GStreamer debugging system to debug pipeline problems. Elements will write output to this system to log what they're doing. It's not used for error reporting, but it is very useful for tracking what an element is doing exactly, which can come in handy when debugging application issues (such as failing seeks, out-of-sync media, etc.).

 Most GStreamer-based applications accept the commandline option --gst-debug=LIST and related family members. The list consists of a comma-separated list of category/level pairs, which can set the debugging level for a specific debugging category. For example, --gst-debug=oggdemux:5 would turn on debugging for the Ogg demuxer element. You can use wildcards as well. A debugging level of 0 will turn off all debugging, and a level of 9 will turn on all debugging. Intermediate values only turn on some debugging (based on message severity; 2, for example, will only display errors and warnings). Here's a list of all available options:

--gst-debug-help will print available debug categories and exit.

--gst-debug-level=LEVEL will set the default debug level (which can range from 0 (no output) to 5 (everything)).

--gst-debug=LIST takes a comma-separated list of category_name:level pairs to set specific levels for the individual categories. Example: GST_AUTOPLUG:5,avidemux:3 or *pulse*:5,*sink*:5,*ring*:5. Alternatively, you can also set the GST_DEBUG environment variable, which has the same effect.

--gst-debug-no-color will disable color debugging. You can also set the GST_DEBUG_NO_COLOR environment variable to 1 if you want to disable colored debug output permanently. Note that if you are disabling color purely to avoid messing up your pager output, try using less -R.

--gst-debug-disable disables debugging altogether.

--gst-plugin-spew enables printout of errors while loading GStreamer plugins.

GStreamer Debug Viewer [1]

[0] http://gstreamer.freedesktop.org/data/doc/gstreamer/head/manual/html/section-checklist-debug.html
[1] http://cgit.freedesktop.org/~cymacs/gst-debug-viewer/
[2] http://cgit.freedesktop.org/gstreamer/gst-devtools/
[3] http://gstconf.ubicast.tv/videos/debugging-gstreamer-pipelines/
