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

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
Gst.init(None)

import os
import shutil
from galicaster.core import context
from galicaster.mediapackage import mediapackage
from galicaster.utils.miscellaneous import count_files

repo = context.get_repository()

FAIL_DIR = os.path.join(repo.get_rectemp_path(), 'gc_failover')
FAILOVER_FILE = os.path.join(FAIL_DIR, 'presenter.mp3')
FAILOVER_MIMETYPE = 'audio/mp3'
default_max_amplitude = '-50'
default_device = 'default'
default_track = '1'
rms_list = []
temp_amp = None

device = None
MAX_AMPLITUDE = None
audio_track = None

dispatcher = None
conf = None
logger = None
repo = None
pipe = None
bus = None

def init():
    try:
        global MAX_AMPLITUDE
        global audio_track
        global pipe, bus
        global dispatcher, logger, repo, conf
        
        dispatcher = context.get_dispatcher()
        logger = context.get_logger()
        conf = context.get_conf()
        
        audio_device = conf.get('failovermic', 'device', 'default')
        MAX_AMPLITUDE = conf.get('failovermic', 'failover_threshold')
        audio_track = conf.get('failovermic', 'audio_track')
        logger.info("Max amplutide: {}".format(MAX_AMPLITUDE))

        dispatcher.connect('recorder-vumeter', check_pipeline_amp)
        dispatcher.connect('recorder-stopped', save_failover_audio)
        dispatcher.connect('recorder-starting', record)
        dispatcher.connect('recorder-stopping', stop)
        pipe, bus = set_pipeline(audio_device)
    except ValueError:
        pass


def set_pipeline(device):
    pipe = Gst.Pipeline.new("failover_pipeline")
    bus = pipe.get_bus()

    # Audio source and converter
    faudiosrc = Gst.ElementFactory.make("pulsesrc", "pulsesrc")
    if device != "default":
        faudiosrc.set_property("device", "{0}".format(device))    
    faudioamp = Gst.ElementFactory.make('audioamplify', "audioamplify")
    faudioamp.set_property("amplification", 1)
    faudioval = Gst.ElementFactory.make("valve", "valve")
    faudiocon = Gst.ElementFactory.make("audioconvert", "audioconvert")
    
    # Encoder
    faudioenc = Gst.ElementFactory.make("lamemp3enc", "lamemp3enc")
    faudioenc.set_property("target", 1)
    faudioenc.set_property("bitrate", 192)
    faudioenc.set_property("cbr", "true")
    
    # Filesink
    faudiosink = Gst.ElementFactory.make("filesink", "filesink")
    faudiosink.set_property("location", "{0}".format(FAILOVER_FILE))

    # Add and link elements
    for element in [faudiosrc, faudioamp, faudioval, faudiocon, faudioenc, faudiosink]:
        pipe.add(element)
    faudiosrc.link(faudioamp)
    faudioamp.link(faudioval)
    faudioval.link(faudiocon)
    faudiocon.link(faudioenc)
    faudioenc.link(faudiosink)

    faudioval.set_property('drop', 'True')
    pipe.set_state(Gst.State.NULL)
    
    return pipe, bus


def record(self):
    global logger
    # check to see if temp dir exists if not make one
    if not os.path.exists(FAIL_DIR):
        os.makedirs(FAIL_DIR)
    # if temp mp3 file exists move and rename incrementally
    # if os.path.exists(FAILOVER_FILE):
    #     # logger.info("renaming file")
    #     shutil.move(FAILOVER_FILE, FAILOVER_FILE + "_" + str(count_files(FAIL_DIR)))
    # start recording
    logger.info("Recording faiolver mic")
    pipe.set_state(Gst.State.PLAYING)
    valve = pipe.get_by_name("valve")
    valve.set_property('drop', 'False')


def stop(self):
    # stop recording
    global pipe, bus
    
    a = Gst.Structure.new_from_string('letpass')
    event = Gst.Event.new_custom(Gst.EventType.EOS, a)
    src = pipe.get_by_name("pulsesrc")
    src.send_event(event)

    msg = bus.timed_pop_filtered(Gst.SECOND*7, Gst.MessageType.EOS)
    if not msg:
        logger.debug("Failover audio: There was an issue trying to receive EOS message (Failover audio) TIMEOUT")
    else:
        logger.debug('Failover audio: EOS message successfully received')

    valve = pipe.get_by_name("valve")
    valve.set_property('drop', 'True')
    pipe.set_state(Gst.State.NULL)


def merge(tempdir):
    global logger
    
    # merge temp files
    x = sorted(os.listdir(tempdir))
    y = []
    for i in x:
        y.append(tempdir + '/' + i)
    y.append(y.pop(0))
    input_files = '"' + 'concat:' + '|'.join(y) + '"'
    output_file = FAIL_DIR + '/tempmerge.mp3'
    cmd = "ffmpeg -y -i {0} -acodec copy {1}".format(input_files, output_file)
    os.system(cmd)
    shutil.move('{0}'.format(output_file), FAILOVER_FILE)
    logger.info("merged failover audio files")


def get_audio_pathname():
    global conf
    audio_tracks = conf.get_current_profile().get_audio_tracks()
    if audio_tracks:
        return audio_tracks[0].file

    return None


def remove_temp(tempdir, tmpf):
    if os.path.exists(tmpf):
        os.remove(tmpf)


def save_failover_audio(self, mp_id):
    global repo, logger, temp_amp
    mp = repo.get(mp_id)

    mpUri = mp.getURI()
    flavour = 'presenter/source'

    #compare rms from pipeline with set threshold
    with open(temp_amp) as f:
        amp_list = f.readlines()
    f.close()

    if not amp_list:
        logger.debug("There is no amplification values, so nothing to do")
    else:
        pipeline_amp = float(max(amp_list))
        if MAX_AMPLITUDE is None:
            threshold = default_max_amplitude
        else:
            threshold = MAX_AMPLITUDE
        if pipeline_amp <= float(threshold):
            # if multiple temp mp3 files, merge
            if count_files(FAIL_DIR) > 1:
                merge(FAIL_DIR)
            logger.info('Audio quiet - will be replaced')
            filename = get_audio_pathname()
            if filename:
                logger.debug("Audio track found, so replacing it...")
                dest = os.path.join(mpUri, os.path.basename(filename))
            else:
                logger.debug("No audio track found, so create a new one")
                dest = os.path.join(mpUri, os.path.basename(FAILOVER_FILE))

            logger.debug("Copying from {} to {}".format(FAILOVER_FILE, dest))
            try:
                shutil.copyfile(FAILOVER_FILE, dest)
                mp.add(dest, mediapackage.TYPE_TRACK, flavour, FAILOVER_MIMETYPE, mp.getDuration())
                repo.update(mp)
                logger.info('Replaced quite audio with failover recording, MP %s and URI: %s', mp_id, mpUri)
            except Exception as exc:
                logger.error("Error trying to save failover audio: {}".format(exc))
        
    remove_temp(FAIL_DIR, temp_amp)


def check_pipeline_amp(self, valor, valor2, stereo):
    global temp_amp, logger

    # gstreamer pipeline amplitude temp file
    temp_amp = os.path.join(FAIL_DIR, 'gc_pipeline_amp')

    if context.get_recorder().is_recording():
        rms = valor
        rms_list.append(rms)
        if os.path.exists(temp_amp):
            f = open(temp_amp, 'a')
        else:
            f = open(temp_amp, 'w')
        if len(rms_list) > 100:
            value = str(max(rms_list))
            logger.debug("Writing data {} to {}".format(value, temp_amp))
            f.write(value + '\n')
            f.close()
            del rms_list[:]
