Dumping Pipeline Graphs
=======================

Recent versions of GStreamer have the ability to list the elements contained in a pipeline and their connections to a dot file. Dot files are used by GraphViz to create graphs in PNG, postscript, or other formats.

Dumping a simple GStreamer pipeline:

$GST_DEBUG_DUMP_DOT_DIR=~/tmp/ gst-launch videotestsrc ! xvimagesink

This created three files for each of the transitions between element states:

0:00:00.060896159-gst-launch.NULL_READY.dot
0:00:00.066840070-gst-launch.READY_PAUSED.dot
0:00:00.073951462-gst-launch.PAUSED_PLAYING.dot

The actual filenames may vary.

Converting the dot files to PNG files:

$ dot ~/tmp/0\:00\:00.073951462-gst-launch.PAUSED_PLAYING.dot -Tpng -o out.png
