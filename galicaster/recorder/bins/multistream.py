# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/bins/multistream
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

from os import path

from gi.repository import Gst

from galicaster.recorder import base
from galicaster.recorder.utils import get_videosink
from galicaster.recorder.utils import get_audiosink

pipestr = (  # video source
           ' v4l2src name=gc-multi-src ! capsfilter name=gc-multi-filter !'
           ' queue ! gc-multi-dec !'
           ' videobox name=gc-multi-videobox top=0 bottom=0 !'
           ' videorate ! videoconvert ! capsfilter name=gc-multi-vrate !'
           ' videocrop name=gc-multi-crop ! gc-videofilter ! '

           # video preview
           ' tee name=gc-multi-tee ! queue ! caps-preview ! gc-vsink '

           # video record
           ' gc-multi-tee. ! queue ! valve drop=false name=gc-multi-valve !'
           ' videoconvert ! queue ! gc-multi-enc ! queue ! gc-multi-muxer ! '
           ' queue ! filesink name=gc-multi-sink async=false'

           # audio source
           ' pulsesrc name=gc-audio-src ! '
           ' queue name=gc-min-threshold-time gc-max-size-time '
           ' gc-max-size-buffers gc-max-size-bytes gc-leaky ! '
           ' audioamplify name=gc-audio-amplify amplification=1 !'
           ' audioconvert ! audio/x-raw,channels=gc-audio-channels !'

           # audio preview
           ' tee name=tee-aud ! queue !'
           ' level name=gc-audio-level message=true interval=100000000 !'
           ' volume name=gc-audio-volumemaster ! volume name=gc-audio-volume !'
           ' gc-asink '

           # audio record
           ' tee-aud. ! queue ! valve drop=false name=gc-audio-valve !'
           ' audioconvert ! gc-audio-enc ! gc-multi-mux.'
          )


class GCmultistream(Gst.Bin, base.Base):

    order = ["name", "flavor", "location", "file", "caps",
             "videoencoder", "muxer", "io-mode", "caps-preview"]

    gc_parameters = {
        "name": {
            "type": "text",
            "default": "Webcam",
            "description": "Name assigned to the device",
            },
        "flavor": {
            "type": "flavor",
            "default": "presenter",
            "description": "Opencast flavor associated to the track",
            },
        "location": {
            "type": "device",
            "default": None,
            "description": "Device's mount point of the output",
            },
        "file": {
            "type": "text",
            "default": "CAMERA.avi",
            "description": "The file name where the track will be recorded.",
            },
        "caps": {
            "type": "caps",
            "default": "video/x-raw,framerate=20/1,width=640,height=480",
            # image/jpeg,framerate=10/1,width=640,height=480",
            "description": "Forced capabilities",
            },
        "videocrop-right": {
            "type": "integer",
            "default": 0,
            "range": (0, 200),
            "description": "Right  Cropping",
            },
        "videocrop-left": {
            "type": "integer",
            "default": 0,
            "range": (0, 200),
            "description": "Left  Cropping",
            },
        "videocrop-top": {
            "type": "integer",
            "default": 0,
            "range": (0, 200),
            "description": "Top  Cropping",
            },
        "videocrop-bottom": {
            "type": "integer",
            "default": 0,
            "range": (0, 200),
            "description": "Bottom  Cropping",
            },
        "videoencoder": {
            "type": "text",
            "default": "x264enc pass=5 quantizer=22 speed-preset=4",
            "description": "Gstreamer encoder element used in the bin",
            },
        "muxer": {
            "type": "text",
            "default": "mpegtsmux",
            "description": "Gstreamer encoder muxer used in the bin",
            },
        "videofilter": {
            "type": "text",
            "default": "",
            "description":
                "Videofilter elements (like: videoflip method=rotate-180)",
            },
        "videosink": {
            "type": "select",
            "default": "xvimagesink",
            "options": ["xvimagesink", "ximagesink", "autovideosink",
                        "fpsdisplaysink", "fakesink"],
            "description": "Video sink",
        },
        "io-mode": {
            "type": "select",
            "default": "auto",
            "options": ["auto", "rw", "mmap", "userptr",
                        "dmabuf", "dmabuf-import"],
            "description": "I/O mode",
        },
        "caps-preview": {
            "type": "text",
            "default": None,
            "description": "Caps-preview",
        },
        "audiolocation": {
            "type": "device",
            "default": 'default',
            "description": "Device's mount point of the output",
            },
        "vumeter": {
            "type": "boolean",
            "default": "True",
            "description": "Activate Level message",
            },
        "player": {
            "type": "boolean",
            "default": "True",
            "description": "Enable sound play",
            },
        "amplification": {
            "type": "float",
            "default": 1.0,
            "range": (1.0, 10),
            "description": "Audio amplification",
            },
        "audioencoder": {
            "type": "text",
            "default": "voaacenc",
            "description": "Gstreamer audio encoder element used in the bin",
            },
        "delay": {
            "type": "float",
            "default": 0.0,
            "range": (0, 10),
            "description": "Audio delay",
            },
        "channels": {
            "type": "integer",
            "default": 2,
            "range": (1, 2),
            "description": "Number of audio channels",
            },
        "audiosink": {
            "type": "select",
            "default": "alsasink",
            "options": ["autoaudiosink", "alsasink", "pulsesink", "fakesink"],
            "description": "Audio sink",
        },
    }

    is_pausable = True
    has_audio = True
    has_video = True

    __gstdetails__ = (
        "Galicaster Multi Bin",
        "Generic/Video",
        "Capture v4l2 and pulse audio in one bin",
        "Keele University",
        )

    def __init__(self, options={}):
        base.Base.__init__(self, options)
        Gst.Bin.__init__(self)

        gcvideosink = get_videosink(videosink=self.options['videosink'],
                                    name='sink-'+self.options['name'])
        gcaudiosink = get_audiosink(audiosink=self.options['audiosink'],
                                    name='sink-'+self.options['name']+'-audio')
        aux = (pipestr.replace('gc-vsink', gcvideosink)
               .replace('gc-multi-enc', self.options['videoencoder'])
               .replace('gc-multi-muxer',
                        self.options['muxer'] + ' name=gc-multi-mux')
               .replace('gc-asink', gcaudiosink)
               .replace("gc-audio-enc", self.options["audioencoder"])
               .replace("gc-audio-channels", str(self.options["channels"])))

        if self.options['videofilter']:
            aux = aux.replace('gc-videofilter', self.options['videofilter'])
        else:
            aux = aux.replace('gc-videofilter !', '')

        if 'image/jpeg' in self.options['caps']:
            aux = aux.replace('gc-multi-dec !',
                              'jpegdec max-errors=-1 ! queue !')
        else:
            aux = aux.replace('gc-multi-dec !', '')

        if self.options["caps-preview"]:
            aux = aux.replace("caps-preview !", "videoscale ! videorate ! " +
                              self.options["caps-preview"] + " !")
        else:
            aux = aux.replace("caps-preview !", "")

        if self.options["delay"] > 0.0:
            aux = aux.replace('gc-max-size-time', 'max-size-time=0')
            aux = aux.replace('gc-max-size-buffers', 'max-size-buffers=0')
            aux = aux.replace('gc-max-size-bytes', 'max-size-bytes=0')
            aux = aux.replace('gc-leaky', 'leaky=0')
        else:
            aux = aux.replace('gc-max-size-time', '')
            aux = aux.replace('gc-max-size-buffers', '')
            aux = aux.replace('gc-max-size-bytes', '')
            aux = aux.replace('gc-leaky', '')

        bin = Gst.parse_launch("( {} )".format(aux))
        self.add(bin)

        if self.options['location']:
            self.set_option_in_pipeline('location', 'gc-multi-src', 'device')

        if self.options['audiolocation'] != "default":
            sink = self.get_by_name("gc-audio-src")
            sink.set_property("device", self.options['audiolocation'])

        self.set_option_in_pipeline('io-mode', 'gc-multi-src', 'io-mode')

        self.set_value_in_pipeline(path.join(self.options['path'],
                                             self.options['file']),
                                   'gc-multi-sink', 'location')

        self.set_option_in_pipeline('caps', 'gc-multi-filter', 'caps', None)

        if "player" in self.options and self.options["player"] is False:
            self.mute = True
            element = self.get_by_name("gc-audio-volumemaster")
            element.set_property("mute", True)
        else:
            self.mute = False

        if "vumeter" in self.options:
            level = self.get_by_name("gc-audio-level")
            if self.options["vumeter"] is False:
                level.set_property("message", False)

        if "amplification" in self.options:
            ampli = self.get_by_name("gc-audio-amplify")
            ampli.set_property("amplification",
                               float(self.options["amplification"]))

        if self.options["delay"] > 0.0:
            delay = float(self.options["delay"])
            minttime = self.get_by_name('gc-min-threshold-time')
            minttime.set_property('min-threshold-time',
                                  long(delay * 1000000000))

    def changeValve(self, value):
        valve1 = self.get_by_name('gc-multi-valve')
        valve1.set_property('drop', value)
        valve2 = self.get_by_name('gc-audio-valve')
        valve2.set_property('drop', value)

    def getVideoSink(self):
        return self.get_by_name('sink-' + self.options['name'])

    def getAudioSink(self):
        return self.get_by_name('sink-' + self.options['name'] + '-audio')

    def getSource(self):
        return self.get_by_name('gc-multi-src')

    def send_event_to_src(self, event):
        src1 = self.get_by_name('gc-multi-src')
        src1.send_event(event)
        src1 = self.get_by_name("gc-audio-src")
        src1.send_event(event)

    def mute_preview(self, value):
        if not self.mute:
            element = self.get_by_name("gc-audio-volumemaster")
            element.set_property("mute", value)

    def disable_input(self):
        src1 = self.get_by_name('gc-multi-videobox')
        src1.set_properties(top=-10000, bottom=10000)
        element = self.get_by_name("gc-audio-src")
        element.set_property("volume", 0)

    def enable_input(self):
        src1 = self.get_by_name('gc-multi-videobox')
        src1.set_property('top', 0)
        src1.set_property('bottom', 0)
        element = self.get_by_name("gc-audio-src")
        element.set_property("volume", 1)

    def disable_preview(self):
        src1 = self.get_by_name('sink-'+self.options['name'])
        src1.set_property('saturation', -1000)
        src1.set_property('contrast', -1000)
        element = self.get_by_name("gc-audio-volume")
        element.set_property("mute", True)

    def enable_preview(self):
        src1 = self.get_by_name('sink-'+self.options['name'])
        src1.set_property('saturation', 0)
        src1.set_property('contrast', 0)
        element = self.get_by_name("gc-audio-volume")
        element.set_property("mute", False)
