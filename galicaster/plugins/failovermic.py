# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/failovermic
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.

"""This plugin will record an audio gstreamer pipeline of the specified device. if the audio file in the media package
is quite then it is replaced with the recorded audio file"""

from gi.repository import Gst
import os
import shutil
from galicaster.core import context
from galicaster.mediapackage import mediapackage

logger = context.get_logger()
rms_list = []
FAIL_DIR = os.getenv('HOME') + '/gc_failover'
FAILOVER_FILE = FAIL_DIR + '/presenter.mp3'
FAILOVER_MIMETYPE = 'audio/mp3'
default_max_amplitude = '-50'
default_device = 'default'
default_track = '1'
# gstreamer pipeline amplitude temp file
temp_amp = os.getenv('HOME') + '/gc_pipeline_amp'
# gstreamer pipeline
pipe = Gst.Pipeline.new("failover_pipeline")

device = None
MAX_AMPLITUDE = None
audio_track = None

def init():
    try:
        global device
        global MAX_AMPLITUDE
        global audio_track
        dispatcher = context.get_dispatcher()
        device = context.get_conf().get('failovermic', 'device')
        MAX_AMPLITUDE = context.get_conf().get('failovermic', 'failover_threshold')
        audio_track = context.get_conf().get('failovermic', 'audio_track')
        dispatcher.connect('recorder-vumeter', check_pipeline_amp)
        dispatcher.connect('recorder-stopped', failover_audio)
        dispatcher.connect('recorder-starting', record)
        dispatcher.connect('restart-preview', stop)
        set_pipeline()
    except ValueError:
        pass


def set_pipeline():
    # create the gstreamer elements; pulse source mp3 192kbps cbr
    faudiosrc = Gst.ElementFactory.make("pulsesrc", "pulsesrc")
    if device is None:
        faudiosrc.set_property("device", "{0}".format(default_device))
    else:
        faudiosrc.set_property("device", "{0}".format(device))
    faudioamp = Gst.ElementFactory.make('audioamplify', "audioamplify")
    faudioamp.set_property("amplification", 1)
    faudiocon = Gst.ElementFactory.make("audioconvert", "audioconvert")
    faudioenc = Gst.ElementFactory.make("lamemp3enc", "lamemp3enc")
    faudioenc.set_property("target", 1)
    faudioenc.set_property("bitrate", 192)
    faudioenc.set_property("cbr", "true")
    faudiosink = Gst.ElementFactory.make("filesink", "filesink")
    faudiosink.set_property("location", "{0}".format(FAILOVER_FILE))
    # add elements to the pipeline
    pipe.add(faudiosrc, faudioamp, faudiocon, faudioenc, faudiosink)
    Gst.element_link_many(faudiosrc, faudioamp, faudiocon, faudioenc, faudiosink)


def record(self):
    # check to see if temp dir exists if not make one
    if not os.path.exists(FAIL_DIR):
        os.makedirs(FAIL_DIR)
    # if temp mp3 file exists move and rename incrementally
    if os.path.exists(FAILOVER_FILE):
        # logger.info("renaming file")
        shutil.move(FAILOVER_FILE, FAILOVER_FILE + "_" + str(filecount(FAIL_DIR)))
    # start recording
    pipe.set_state(Gst.State.PLAYING)


def stop(self):
    # stop recording
    pipe.set_state(Gst.State.NULL)


def filecount(files):
    #count number of files in the failover temp dir
    count = 0
    for f in os.listdir(files):
        count += 1
    return count


def merge(tempdir):
    # merge temp files
    x = sorted(os.listdir(tempdir))
    y = []
    for i in x:
        y.append(tempdir + '/' + i)
    y.append(y.pop(0))
    input_files = '"' + 'concat:' + '|'.join(y) + '"'
    output_file = FAIL_DIR + '/tempmerge.mp3'
    cmd = "avconv -y -i {0} -acodec copy {1}".format(input_files, output_file)
    os.system(cmd)
    shutil.move('{0}'.format(output_file), FAILOVER_FILE)
    logger.info("merged failover audio files")


def get_audio_track():
    track_list = []
    tracks = context.get_conf().get_current_profile().tracks
    for track in tracks:
        if track.flavor == 'presenter':
            track_list.append(track.file)
    if audio_track is None:
        t = default_track
    else:
        t = audio_track
    return track_list[int(t)-1]


def remove_temp(tempdir, tmpf):
    shutil.rmtree(tempdir)
    os.remove(tmpf)


def failover_audio(self, mp):
    mpUri = mp.getURI()
    flavour = 'presenter/source'
    mp_list = context.get_repository()
    for uid,mp in mp_list.iteritems():
        if mp.getURI() == mpUri:
            logger.debug('Found MP')
            #compare rms from pipeline with set threshold
            with open(temp_amp) as f:
                amp_list = f.readlines()
            f.close()
            pipeline_amp = float(max(amp_list))
            if MAX_AMPLITUDE is None:
                threshold = default_max_amplitude
            else:
                threshold = MAX_AMPLITUDE
            if pipeline_amp <= float(threshold):
                # if multiple temp mp3 files, merge
                if filecount(FAIL_DIR) > 1:
                    merge(FAIL_DIR)
                logger.info('audio quiet - will be replaced')
                filename = get_audio_track()
                dest = os.path.join(mpUri, os.path.basename(filename))
                shutil.copyfile(FAILOVER_FILE, dest)
                mp.add(dest, mediapackage.TYPE_TRACK, flavour, FAILOVER_MIMETYPE, mp.getDuration())
                mp_list.update(mp)
                logger.info('Replaced quite audio with failover recording UID:%s - URI: %s', uid, mpUri)
                remove_temp(FAIL_DIR, temp_amp)
            else:
                remove_temp(FAIL_DIR, temp_amp)


def check_pipeline_amp(self, valor, valor2, stereo):
    if context.get_recorder().is_recording():
        rms = valor
        rms_list.append(rms)
        if os.path.exists(temp_amp):
            f = open(temp_amp, 'a')
        else:
            f = open(temp_amp, 'w')
        if len(rms_list) > 100:
            f.write(str(max(rms_list)) + '\n')
            f.close()
            del rms_list[:]
