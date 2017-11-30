# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/checkrepo
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""This plugin check repository mediapackages. If anyone it's SCHEDULED when must be RECORDING, change start_time and duration, then start recording
"""

import datetime
import os
import subprocess
import shutil
import uuid


from galicaster.core import context
from galicaster.mediapackage import mediapackage
from galicaster.plugins import failovermic

logger = context.get_logger()
worker = context.get_worker()
conf = context.get_conf()
recorder = context.get_recorder()


def init():	
    try:
        dispatcher = context.get_dispatcher()
        findrecs = FindRecordings()
        dispatcher.connect('ical-processed', findrecs.check_repository)
        dispatcher.connect('recorder-stopped', findrecs.find_recordings)
        dispatcher.connect('timer-nightly', findrecs.merge_delayed)

    except ValueError:
        pass

class FindRecordings(object):

    def __init__(self):
        self.rectemp_exists = False
        self.check_attachment = 'check.attach'
        self.rectemp_uris_attachment = 'rectempURIs.attach'
        self.delay = conf.get_boolean('checkrepo', 'delay_merge') or False
        self.to_merge = conf.get_boolean('checkrepo', 'to_merge') or False
        self.pause_state_file = os.path.join(context.get_repository().get_rectemp_path(), "paused")
        if os.path.exists(self.pause_state_file):
            os.remove(self.pause_state_file)

    def find_recordings(self, signal, mpid):
        mp = recorder.current_mediapackage
        mpUri = mp.getURI()
        dest = os.path.join(mpUri, self.check_attachment)
        repofile = os.path.join(mpUri, self.rectemp_uris_attachment)

        if os.path.isfile(dest):
            mp_list = context.get_repository()
            rectemp = mp_list.get_rectemp_path()
            timesfile = open(dest, "r")
            timespan = timesfile.readline()
            times = timespan.split(',')
            start = datetime.datetime.strptime(times[0], "%Y-%m-%d %H:%M:%S")
            end = datetime.datetime.strptime(times[1], "%Y-%m-%d %H:%M:%S")
            timesfile.close()
            repocheck = open(repofile, "a")
            for fname in os.listdir(rectemp):
                filepath = os.path.join(rectemp, fname)
                if os.path.isdir(filepath):
                    for item in (os.listdir(filepath)):
                        fileitem = os.path.join(filepath, item)
                        timestamp = os.path.getmtime(fileitem)
                        time = datetime.datetime.utcfromtimestamp(timestamp)
                        if start < time and end > time:
                            self.rectemp_exists = True
                            repocheck.write(filepath+"\n")
                            # FIXME could write this better
                            break
            repocheck.close()
            # check for real rectemp files, stops merge happening on mp's that started after start time
            if self.rectemp_exists:
                if self.to_merge:
                    if self.delay:
                        # stop ingest for now, set to delayed
                        logger.info('delaying merge of mp parts and ingest')
                        mp.setOpStatus('ingest', mediapackage.OP_NIGHTLY)
                        mp_list.update(mp)
                    else:
                        self.merge(mp, repofile, dest, mp_list)
            else:
                self.rectemp_exists = False
                # clean up temp files
                os.remove(dest)
                os.remove(repofile)


    def merge(self, mp, repofile, dest, mp_list):
        mpUri = mp.getURI()
        logger.info("merging recovered files into mediapackage:" + mpUri)
        # while merging, create a paused file, this can be used by other systems as a signal
        # to know galicaster is currently processing a mediapackage.
        wait = False
        if os.path.exists(self.pause_state_file):
            os.utime(self.pause_state_file, None)
        else:
            wait = True
            open(self.pause_state_file, 'a').close()
        with open(repofile) as f:
            rectemps = f.read().splitlines()
        # get list of rectemp files
        rectemps_list = sorted(rectemps)
        rectemps_list.append(mpUri)
        # get the track file names + mimetype
        tracks = context.get_conf().get_current_profile().tracks
        for track in tracks:
            # get all the rectemp and final mp files into a list to be concatenated by ffmpeg
            track_file = track.file
            add_track = [s + '/{}'.format(track_file) for s in rectemps_list]
            # check if its a real file, if not remove from the list
            real_tracks = []
            for fullpath_t in add_track:
                if os.path.isfile(fullpath_t):
                    real_tracks.append(fullpath_t)
            rectemps_fmted = ('|').join(real_tracks)
            temp_track_file = 'temp_{}.{}'.format(str(uuid.uuid4())[:8], track_file.split(".")[-1])
            # do a file concat per track into the mp
            full_cmd = 'ffmpeg -i "concat:{}" -c copy {}/{}'.format(rectemps_fmted, mpUri, temp_track_file)
            subprocess.call(full_cmd, shell=True)
            # remove existing track files
            os.remove(mpUri + '/' + track_file)
            # replace with new, merged files
            shutil.move(mpUri + '/' + temp_track_file, mpUri + '/' + track_file)

        # clean up temp files
        os.remove(dest)
        os.remove(repofile)
        # update mp with correct duration
        mp.discoverDuration()
        mp_list.update(mp)
        logger.info("merging complete for UID: {} - URI: {}".format(mp.getIdentifier(), mpUri))
        if wait:
            os.remove(self.pause_state_file)

    def merge_delayed(self, signal):
        # merge and ingest the delayed mp's
        if self.delay:
            repo = context.get_repository()
            for mp_id, mp in repo.iteritems():
                if not (mp.status == mediapackage.SCHEDULED or mp.status == mediapackage.RECORDING):
                    mpUri = mp.getURI()
                    dest = os.path.join(mpUri, self.check_attachment)
                    repofile = os.path.join(mpUri, self.rectemp_uris_attachment)
                    if os.path.exists(repofile):
                        self.merge(mp, repofile, dest, repo)
                        logger.info('Starting Ingest of merge delayed mediapackage: {}'.format(mp_id))
                        worker.enqueue_job_by_name('ingest', mp)

    def check_repository(self, signal):
        # mp_list is collection of mediapackages ID's
        # don't check when recording already
        if recorder.is_recording():
            return

        mp_list = context.get_repository()
        for uid,mp in mp_list.iteritems():
            start = mp.getDate()
            end = start + datetime.timedelta(seconds=(mp.getDuration()/1000))
            if mp.status == mediapackage.SCHEDULED and start < datetime.datetime.utcnow() and end > datetime.datetime.utcnow():
                # make a check attachment in the mp to mark the mp as having restarted recording
                dest = os.path.join(mp.getURI(),self.check_attachment)
                if not os.path.isfile(dest):
                    repocheck = open(dest, "w")
                    repocheck.write(str(start) + "," + str(end) + ",\n")
                    repocheck.close()
                # duration update
                x = datetime.datetime.utcnow() - start
                x = x.seconds-2
                mp.setDuration(mp.getDuration() - x*1000)
                # start-datetime update
                mp.setDate(datetime.datetime.utcnow()+datetime.timedelta(seconds=2))
                # repository update
                mp_list.update(mp)

                scheduler = context.get_scheduler()
                try:
                    scheduler.create_timer(mp)
                    logger.info("Mediapackage with UID: {} have been reprogrammed".format(uid))
                except Exception as exc:
                    logger.error("Error trying to create a new timer for MP {}: {}".format(uid, exc))
