# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/recorder/pipeline/v4l2
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.
import logging

import gobject
import gst
import re

from os import path

pipestr = (' v4l2src name=gc-v4l2-src ! capsfilter name=gc-v4l2-filter ! gc-v4l2-dec '
           ' videorate ! capsfilter name=gc-v4l2-vrate ! videocrop name=gc-v4l2-crop ! '
           ' tee name=tee-cam2  ! queue !  xvimagesink async=false qos=false name=gc-v4l2-preview'
           ' tee-cam2. ! queue ! valve drop=false name=gc-v4l2-valve ! ffmpegcolorspace ! queue ! '
           #' xvidenc bitrate=50000000 ! queue ! avimux ! '
           #' x264enc pass=5 quantizer=22 speed-preset=4 profile=1 ! queue ! avimux ! '
           ' ffenc_mpeg2video quantizer=4 gop-size=1 bitrate=10000000 ! queue ! avimux ! '
           ' queue ! filesink name=gc-v4l2-sink async=false')


class GCv4l2(gst.Bin):

    gc_parameters = {
        "caps": "Forced capabilities",
        "videocrop-right": "Right  Cropping",
        "videocrop-left": "Right  Cropping",
        "videocrop-top": "Right  Cropping",
        "videocrop-bottomt": "Right  Cropping",
        # "codificaton": "Not implemented yet"
        }

    is_pausable = True

    __gstdetails__ = (
        "Galicaster V4L2 Bin",
        "Generic/Video",
        "Add descripcion",
        "Teltek Video Research",
        )

    def __init__(self, name=None, devicesrc=None, filesink=None, options={}):
        if not path.exists(devicesrc):
            raise SystemError('Device error in v4l2 bin: path %s not exists' % (devicesrc,) )

        if name == None:
            name = 'v4l2'

        gst.Bin.__init__(self, name)
        self.options = options

        aux = pipestr.replace('gc-v4l2-preview', 'sink-' + name)
        if 'caps' in options and 'image/jpeg' in options['caps']:
            aux = aux.replace('gc-v4l2-dec', 'jpegdec ! queue !')
        else:
            aux = aux.replace('gc-v4l2-dec', '')

        # Para usar con el gtk.DrawingArea
        bin = gst.parse_bin_from_description(aux, True)
        # replace identity
        self.add(bin)

        if devicesrc != None:
            element = self.get_by_name('gc-v4l2-src')
            element.set_property('device', devicesrc)
        if filesink != None:
            element = self.get_by_name('gc-v4l2-sink')
            element.set_property('location', filesink)
        if 'caps' in options:
            element = self.get_by_name('gc-v4l2-filter')
            element.set_property('caps', gst.Caps(options['caps']))
            fr = re.findall("framerate *= *[0-9]+/[0-9]+", options['caps'])
            if fr:
                element2 = self.get_by_name('gc-v4l2-vrate')
                newcaps = 'video/x-raw-yuv,' + fr[0]
                element2.set_property('caps', gst.Caps(newcaps))

        if 'videocrop-right' in options:
            element = self.get_by_name('gc-v4l2-crop')
            element.set_property('right', int(options['videocrop-right']))
        if 'videocrop-left' in options:
            element = self.get_by_name('gc-v4l2-crop')
            element.set_property('left', int(options['videocrop-left']))
        if 'videocrop-top' in options:
            element = self.get_by_name('gc-v4l2-crop')
            element.set_property('top', int(options['videocrop-top']))
        if 'videocrop-bottom' in options:
            element = self.get_by_name('gc-v4l2-crop')
            element.set_property('bottom', int(options['videocrop-bottom']))

    def getValve(self):
        return self.get_by_name('gc-v4l2-valve')

    def getVideoSink(self):
        return self.get_by_name('gc-v4l2-preview')

    def send_event_to_src(self, event):
        src1 = self.get_by_name('gc-v4l2-src')
        src1.send_event(event)


gobject.type_register(GCv4l2)
gst.element_register(GCv4l2, 'gc-v4l2-bin')
