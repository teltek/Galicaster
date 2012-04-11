# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
# Based on:
#       galicaster/recorder/pipeline/v4l2
#       Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
#
#       galicaster/recorder/pipeline/blackmagic
#
# Copyright (c) 2012, Sami Andberg & Tero Karkkainen, University of Helsinki <atk-verkkovideo@helsinki.fi>
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

pipestr = (' decklinksrc input=SDI input-mode=12 name=gc-blackmagic-src ! capsfilter name=gc-blackmagic-filter ! '
          ' videorate ! capsfilter name=gc-blackmagic-vrate ! videocrop name=gc-blackmagic-crop ! '
          ' tee name=tee-cam2  ! queue !  xvimagesink async=false qos=false name=gc-blackmagic-preview'
          ' tee-cam2. ! queue ! valve drop=false name=gc-blackmagic-valve ! ffmpegcolorspace ! queue ! '
          #' xvidenc bitrate=50000000 ! queue ! avimux ! '
          ' x264enc quantizer=22 speed-preset=2 profile=1 ! queue ! avimux ! '
          #' ffenc_mpeg2video quantizer=4 gop-size=1 bitrate=10000000 ! queue ! avimux ! '
          ' queue ! filesink name=gc-blackmagic-sink async=false')


class GCblackmagic(gst.Bin):

   gc_parameters = {
       "caps": "Forced capabilities",
       "videocrop-right": "Right  Cropping",
       "videocrop-left": "Right  Cropping",
       "videocrop-top": "Right  Cropping",
       "videocrop-bottomt": "Right  Cropping",
       "input": "Video input to capture from",
       "input-mode": "Video input mode (resolution and frame rate)"
       # "codificaton": "Not implemented yet"
       }

   is_pausable = False # TODO check

   __gstdetails__ = (
       "Galicaster blackmagic Bin",
       "Generic/Video",
       "Add descripcion",
       "University of Helsinki & Teltek Video Research",
       )

   def __init__(self, name=None, devicesrc=None, filesink=None, options={}):
       if not path.exists(devicesrc):
           raise SystemError('Device error in blackmagic bin: path %s not exists' % (devicesrc,) )

       if name == None:
           name = 'blackmagic'

       gst.Bin.__init__(self, name)
       self.options = options

       aux = pipestr.replace('gc-blackmagic-preview', 'sink-' + name)
       bin = gst.parse_bin_from_description(aux, True)
       # replace identity
       self.add(bin)

       if filesink != None:
           element = self.get_by_name('gc-blackmagic-sink')
           element.set_property('location', filesink)

       if 'input' in options:
           element = self.get_by_name('gc-blackmagic-src')
           element.set_property('input', options['input'])
       if 'input-mode' in options:
           element = self.get_by_name('gc-blackmagic-src')
           element.set_property('input-mode', gst.Caps(options['input-mode']))
       if 'videocrop-right' in options:
           element = self.get_by_name('gc-blackmagic-crop')
           element.set_property('right', int(options['videocrop-right']))
       if 'videocrop-left' in options:
           element = self.get_by_name('gc-blackmagic-crop')
           element.set_property('left', int(options['videocrop-left']))
       if 'videocrop-top' in options:
           element = self.get_by_name('gc-blackmagic-crop')
           element.set_property('top', int(options['videocrop-top']))
       if 'videocrop-bottom' in options:
           element = self.get_by_name('gc-blackmagic-crop')
           element.set_property('bottom', int(options['videocrop-bottom']))

   def getValve(self):
       return self.get_by_name('gc-blackmagic-valve')

   def getVideoSink(self):
       return self.get_by_name('gc-blackmagic-preview')

   def send_event_to_src(self, event):
       src1 = self.get_by_name('gc-blackmagic-src')
       src1.send_event(event)


gobject.type_register(GCblackmagic)
gst.element_register(GCblackmagic, 'gc-blackmagic-bin')
