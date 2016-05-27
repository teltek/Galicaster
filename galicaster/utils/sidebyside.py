# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/sidebyside
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

# TODO:
#  - Add background picture to mixer.

from os import path

from gi.repository import Gst
Gst.init(None)

layouts = {'sbs': 
           {'screen_width': 640, 'screen_height': 480, 'screen_aspect': '4/3', 'screen_xpos': 640,'screen_ypos': 0, 'screen_zorder': 0, 
            'camera_width': 640, 'camera_height': 480, 'camera_aspect': '4/3', 'camera_xpos': 0, 'camera_ypos':  0, 'camera_zorder': 0, 
            'out_width': 1280, 'out_height': 720},
           'sbsnocrop': 
           {'screen_width': 640, 'screen_height': 480, 'screen_aspect': '0/1', 'screen_xpos': 640,'screen_ypos': 0, 'screen_zorder': 0, 
            'camera_width': 640, 'camera_height': 480, 'camera_aspect': '0/1', 'camera_xpos': 0, 'camera_ypos':  0, 'camera_zorder': 0, 
            'out_width': 1280, 'out_height': 720},
           'pip_screen': 
           {'screen_width': 320, 'screen_height': 180, 'screen_aspect': '16/9', 'screen_xpos': 960,'screen_ypos': 540, 'screen_zorder': 1, 
            'camera_width': 960, 'camera_height': 720, 'camera_aspect': '4/3',  'camera_xpos': 0,  'camera_ypos': 0, 'camera_zorder': 0, 
            'out_width': 1280, 'out_height': 720},
           'pip_camera': 
           {'screen_width': 960, 'screen_height': 720, 'screen_aspect': '4/3', 'screen_xpos': 0,'screen_ypos': 0, 'screen_zorder': 0, 
            'camera_width': 320, 'camera_height': 180, 'camera_aspect': '16/9', 'camera_xpos': 960, 'camera_ypos': 540, 'camera_zorder': 1, 
            'out_width': 1280, 'out_height': 720},}

def create_sbs(out, camera, screen, audio=None, layout='sbs', logger=None):
    """
    Side By Side creator
    
    :param out: output file path
    :param camera: camera video file path
    :param screen: screen video file path 
    :param audio: audio file path or "screen" o "camera" string to re-use files
    """

    pipestr = """
    videomixer name=mix background=1
        sink_0::xpos={screen_xpos} sink_0::ypos={screen_ypos} sink_0::zorder={screen_zorder}
        sink_1::xpos={camera_xpos} sink_1::ypos={camera_ypos} sink_1::zorder={camera_zorder} !
    videoconvert name=colorsp_saida ! 
    videoscale ! videorate ! video/x-raw,width={out_width},height={out_height},framerate=25/1,pixel-aspect-ratio=1/1,interlace-mode=progressive !
    x264enc quantizer=45 speed-preset=6 ! queue ! 
    mp4mux name=mux  ! queue ! filesink location="{OUT}"

    filesrc location="{SCREEN}" ! decodebin name=dbscreen ! deinterlace ! videoconvert name=colorsp_screen !
    aspectratiocrop aspect-ratio={screen_aspect} ! videoscale ! videorate !
    video/x-raw,width={screen_width},height={screen_height},framerate=25/1,pixel-aspect-ratio=1/1,interlace-mode=progressive !
    mix.sink_0 

    filesrc location="{CAMERA}" ! decodebin name=dbcamera ! deinterlace ! videoconvert name=colorsp_camera !
    aspectratiocrop aspect-ratio={camera_aspect} ! videoscale ! videorate !
    video/x-raw,width={camera_width},height={camera_height},framerate=25/1,pixel-aspect-ratio=1/1,interlace-mode=progressive ! queue !
    mix.sink_1 
    """

    pipestr_audio_file = """
    filesrc location="{AUDIO}" ! decodebin name=dbaudio ! 
    audioconvert ! queue ! voaacenc bitrate=128000 ! queue ! mux.
    """

    if not layout in layouts:
        if logger:
            logger.error('Layout not exists')
        raise IOError, 'Error in SideBySide proccess'

    if not camera or not screen:
        if logger:
            logger.error('SideBySide Error: Two videos needed')
        raise IOError, 'Error in SideBySide proccess'

    for track in [camera, screen, audio]:    
        if track and not path.isfile(camera):
            if logger:
                logger.error('SideBySide Error: Not  a valid file %s', track)
            raise IOError, 'Error in SideBySide proccess'

    embeded = False
    if audio:
        pipestr = "".join((pipestr, pipestr_audio_file.format(AUDIO=audio)))
        if logger:
            logger.debug('Audio track detected: %s', audio)
    else:
        if logger:
            logger.debug('Audio embeded')
        embeded = True

    logger and logger.debug("Output file {} and layout {}".format(out, layout))
    parameters = {'OUT': out, 'SCREEN': screen, 'CAMERA': camera}
    parameters.update(layouts[layout])
    pipeline = Gst.parse_launch(pipestr.format(**parameters))
    bus = pipeline.get_bus()

    # connect callback to fetch the audio stream
    if embeded:
        mux = pipeline.get_by_name('mux')    
        dec_camera = pipeline.get_by_name('dbcamera')
        dec_screen = pipeline.get_by_name('dbscreen')    
        dec_camera.connect('pad-added', on_audio_decoded, pipeline, mux)
        dec_screen.connect('pad-added', on_audio_decoded, pipeline, mux)


    pipeline.set_state(Gst.State.PLAYING)
    msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)
    pipeline.set_state(Gst.State.NULL)
    
    if msg.type == Gst.MessageType.ERROR:
        err, debug = msg.parse_error()
        if logger:
            logger.error('SideBySide Error: %s', err)
        raise IOError, 'Error in SideBySide proccess'

    return True
    

def on_audio_decoded(element, pad, bin, muxer):
    name = pad.query_caps(None).to_string()
    element_name = element.get_name()[:8]
    sink = None

    # only one audio will be muxed
    created=bin.get_by_name('sbs-audio-convert')
    pending = False if created else True

    if name.startswith('audio/x-raw') and pending:
        # db%. audioconvert ! queue ! faac bitrate = 12800 ! queue ! mux.
        convert = Gst.ElementFactory.make('audioconvert', 'sbs-audio-convert-{0}'.format(element_name))
        q1 = Gst.ElementFactory.make('queue','sbs-audio-queue-{0}'.format(element_name))
        f = Gst.ElementFactory.make('voaacenc','sbs-audio-encoder-{0}'.format(element_name))
        f.set_property('bitrate',128000)
        q2 = Gst.ElementFactory.make('queue','sbs-audio-queue2-{0}'.format(element_name))

        #link
        bin.add(convert)
        bin.add(q1)
        bin.add(f)
        bin.add(q2)
        convert.link(q1)
        q1.link(f)
        f.link(q2)
        q2.link(muxer)
        #keep activating
        convert.set_state(Gst.State.PLAYING)
        q1.set_state(Gst.State.PLAYING)
        f.set_state(Gst.State.PLAYING)
        q2.set_state(Gst.State.PLAYING)
        pad.link(convert.get_static_pad('sink'))

    return sink

    

