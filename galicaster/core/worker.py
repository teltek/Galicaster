# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/core/worker
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import os
import threading
import tempfile
import Queue

from datetime import datetime

from galicaster.mediapackage import serializer
from galicaster.mediapackage import mediapackage
from galicaster.utils import sidebyside
from galicaster.utils.mediainfo import get_info

INGEST = 'Ingest'
ZIPPING = 'Export to Zip'
SBS = 'Side by Side'

INGEST_CODE = 'ingest'
ZIPPING_CODE = 'exporttozip'
SBS_CODE = 'sidebyside'

JOBS = { INGEST: INGEST_CODE, 
         ZIPPING: ZIPPING_CODE, 
         SBS:  SBS_CODE}

JOB_NAMES = { INGEST_CODE: INGEST, 
              ZIPPING_CODE: ZIPPING, 
              SBS_CODE:  SBS}

"""
This class manages the long operations to be done with a mediapackage:
    Ingest it into opencast server.
    Save it as a zip.
    Do side by side.
This operations are threads concurrently done with the rest of galicaster tasks to avoid blocking them.
"""
class Worker(object):

    class T(threading.Thread):

        def __init__(self, queue):
            """
            Initializes a Thread with a queue of jobs to be done concurrently with other Galicaster tasks.
            Args:
            	queue (Queue): queue of jobs.
            Attributes:
                queue (Queue): queue of jobs.
            """
            threading.Thread.__init__(self)
            self.queue = queue

        def run(self):
            """Runs and removes a job from the queue.
            Marks the job as done. 
            """
            while True: 
                job, params = self.queue.get()
                job(*params)
                self.queue.task_done()
    

    def __init__(self, dispatcher, repo, logger, oc_client=None, export_path=None, tmp_path=None, 
                 use_namespace=True, sbs_layout='sbs', hide_ops=[], hide_nightly=[]):
        """Initializes a worker that manages the mediapackages of the repository in order to do long operations concurrently by throwing Threads when necessay.
        Args:
            dispacher (Dispatcher): the galicaster event-dispatcher to emit signals. 
            repo (Repository): the galicaster mediapackage repository.
            logger (Logger): the object that prints all the information, warning and error messages.
            oc_client (OCHTTPClient): the opencast HTTP client.
            export_path (str): the absolute path where galicaster exports zip and sidebyside.
            tmp_path (str): temporal path (needed if /tmp partition is small).
            use_namespace (bool): if true the manifest attribute xmlns has 'http://mediapackage.opencastproject.org' value.
            sbs_layout (str): the identifier of side by side layout. See notes.
            hide_ops (List[str]): List of hidden mediapackage operations.
            hide_nightly (List[str]): List of nightly hidden mediapackage operations.
        Attributes:
            jobs (Queue): queue of jobs.
            t (Thread)
        Note:
            sbs_layouts possible values:
                'sbs': screen and camera have the same size. 
                'pip_screen': screen smaller than camera.
                'pip_camera:': camera smaller than screen.
            """


        self.repo = repo
        self.oc_client = oc_client
        self.export_path = export_path or os.path.expanduser('~')
        self.tmp_path = tmp_path or tempfile.gettempdir()
        self.use_namespace = use_namespace
        self.sbs_layout = sbs_layout
        self.dispatcher = dispatcher
        self.logger = logger
        self.hide_ops = hide_ops
        self.hide_nightly = hide_nightly

        for dir_path in (self.export_path, self.tmp_path):
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)

        self.jobs = Queue.Queue()
        
        self.t = self.T(self.jobs)
        self.t.setDaemon(True)
        self.t.start()

        self.dispatcher.connect('timer-nightly', self.exec_nightly)

    def get_all_job_types(self):
        """Gets all the possible mediapackage operations.
        Returns:
            List[str]: List of the possible operations (including nightly mode) 
        """
        nn = ' Nightly'
        return [INGEST, ZIPPING, SBS, INGEST+nn, ZIPPING+nn, SBS+nn]


    def get_ui_job_types(self):
        """Gets the mediapackage operations that are going to be showed in the user's interface.
        Returns:
            List[str]: List of the possible operations (including nightly mode) in user's interface. 
        """
        nn = ' Nightly'
        return [INGEST, ZIPPING, SBS, INGEST+nn, ZIPPING+nn, SBS+nn]


    def get_all_job_types_by_mp(self, mp):
        """Gets all the jobs (even nigthly) that are not pending or processing.
        Args:
            mp (Mediapackage): the mediapackage.
        Returns:
            List[Str]: not hidden jobs that are not in pending or precessing status.	
            List[Str]: not hidden nightly jobs that are not pending or processing status.
        """
        nn = ' Nightly'
        cc = 'Cancel '
        jobs = []
        jobs_night = []

        for key,value in JOBS.iteritems():
            if key==INGEST and not self.oc_client:
                continue
            if mp.getOpStatus(value) not in [mediapackage.OP_PENDING, mediapackage.OP_PROCESSING]:
                if value not in self.hide_ops:
                    jobs.append(key)
                if value not in self.hide_nightly:
                    night = cc+key+nn if mp.getOpStatus(value) == mediapackage.OP_NIGHTLY else key+nn
                    jobs_night.append(night)            

        return jobs, jobs_night


    def get_ui_job_types_by_mp(self, mp):
        """Gets all the jobs (even nigthly) that are not pending or processing.
        Args:
            mp (Mediapackage): the mediapackage.
        Returns:
            List[Str]: not hidden jobs that are not in pending or precessing status.	
            List[Str]: not hidden nightly jobs that are not pending or processing status.
        """
        nn = ' Nightly'
        cc = 'Cancel '
        jobs = []
        jobs_night = []

        for key,value in JOBS.iteritems():
            if key==INGEST and not self.oc_client:
                continue

            if key not in [INGEST, ZIPPING, SBS]:
                continue

            if mp.getOpStatus(value) not in [mediapackage.OP_PENDING, mediapackage.OP_PROCESSING]:
                if value not in self.hide_ops:
                    jobs.append(key)
                if value not in self.hide_nightly:
                    night = cc+key+nn if mp.getOpStatus(value) == mediapackage.OP_NIGHTLY else key+nn
                    jobs_night.append(night)            

        return jobs, jobs_night

    
    def get_job_name(self, job=None):
        jobname = None
        if job:
            if job in JOB_NAMES:
                jobname = JOB_NAMES[job]
        return jobname


    def do_job_by_name(self, name, mp_id, params={}):
        """Does a particular operation for a particular mediapackage.
        Args:
            name (str): the name of the operation (code).
            mp_id (str): the mediapackage id.
        Returns:
            Bool: True if success. False otherwise.
        """
        f_operation = {
            INGEST_CODE: self._ingest,
            ZIPPING_CODE: self._export_to_zip,
            SBS_CODE: self._side_by_side}
        try:
            mp = self.repo[mp_id]
            f = f_operation[name]
        except Exception as exc:
            self.logger.error("Fail get MP with id {0} or operation with name {1}. Exception: {2}".format(mp_id, name, exc))
            return False
        f(mp, params)
	return True

    
    def enqueue_job_by_name(self, name, mp_id, params={}):
        """Enqeues a particular mediapackage operation to be done.
        Args:
            name (str): the name of the operation (code).
            mp_id (str): the mediapackage id.
        Returns:
            Bool: True if success. False otherwise.
        """
        f_operation = {
            INGEST_CODE: self.ingest,
            ZIPPING_CODE: self.export_to_zip,
            SBS_CODE: self.side_by_side}
        try:
            mp = self.repo[mp_id]
            f = f_operation[name]
        except Exception as exc:
            self.logger.error("Fail get MP with id {0} or operation with name {1}. Exception: {2}".format(mp_id, name, exc))
            return False
        f(mp, params)
	return True


    def do_job(self, name, mp, params={}):
        """Calls a particular method of this class with a given argument.
        The method should execute an operation with the same name.
        Args:
            name (str): the name of a worker method.
            mp (Mediapackage): the mediapackage.
        """
        try:
            f = getattr(self, name)
            f(mp, params)
        except Exception as exc:
            self.logger.error("Failure performing job {0} for MP {1}. Exception: {2}".format(name, mp, exc))
            return False
        return True

    
    def do_job_nightly(self, name, mp, params={}):
        """Calls cancel_nightly or operation_nithly depending on the argument's value.
        Args:
            name (str): the name of a nightly operation. It must contain the word "cancel" in order to cancel the operation. 
            mp (Mediapackage): the mediapackage.
        """
        name=name.replace('nightly','')
        try:
            if name.count('cancel'):
                getattr(self, name.replace('cancel',''))
                self.cancel_nightly(mp, name.replace('cancel',''))
            else:
                getattr(self, name)
                self.operation_nightly(mp, name, params)
        except Exception as exc:
            self.logger.error("Failure performing nightly job {0} for MP {1}. Exception: {2}".format(name, mp, exc))
            return False
        return True
    

    def gen_location(self, extension):
        """Gets the path of a non existing file in the exports' directory.
        The file would be called with the actual datetime, a particular extension and a identifier if necessary.
        Args:
            extension (str): the new exporting file extension.
        Returns:
            Str: the absolute path of a exporting file to be generated.
        """
        name = datetime.now().replace(microsecond=0).isoformat()
        while os.path.exists(os.path.join(self.export_path, name + '.' + extension)):
            name += '_2'
        return os.path.join(self.export_path, name + '.' + extension)

    def ingest_nightly(self, mp):
        """Ingests nigthly a mediapackage into opencast.
        Args:
            mp (Mediapackage): the mediapackage to be nightly ingested.
        """
        self.operation_nightly(mp, INGEST_CODE)

    def ingest(self, mp, params={}):
        """Sets mediapackage status to be ingested.
        Adds the ingest operation to the threads queue.
        Args:
            mp (Mediapackage): the mediapackage to be immediately ingested.
        """
        self.logger.info('Creating Ingest Job for MP {0}'.format(mp.getIdentifier()))
        mp.setOpStatus('ingest',mediapackage.OP_PENDING)
        self.repo.update(mp)
        self.jobs.put((self._ingest, (mp, params)))

    def _ingest(self, mp, params={}):
        """Tries to immediately ingest the mediapackage into opencast.
        If the ingest cannot be done, logger prints it properly.
        Args:
            mp(Mediapackage): the mediapackage to be immediately ingested.
        """
        if not self.oc_client:
            self.operation_error(mp, INGEST, 'MH client is not enabled')
            return
            
        workflow = None if not "workflow" in params else params["workflow"]
        workflow_parameters = None if not "workflow_parameters" in params else params["workflow_parameters"]

        self.logger.info('Executing Ingest for MP {0}'.format(mp.getIdentifier()))
        mp.setOpStatus('ingest',mediapackage.OP_PROCESSING)
        self.repo.update(mp)

        self.dispatcher.emit('operation-started', 'ingest', mp)
        self.dispatcher.emit('action-mm-refresh-row', mp.identifier)

        if workflow or workflow_parameters:
            self.logger.info("Ingest for MP {}: workflow:{}   workflow_parameters:{} (None means default values)".format(mp.getIdentifier(), workflow, workflow_parameters))

        ifile = tempfile.NamedTemporaryFile(dir=self.tmp_path)
        self._export_to_zip(mp, params={"location" : ifile, "is_action": False})

        if mp.manual:
            try:
                self.oc_client.ingest(ifile.name, mp.getIdentifier(), workflow=workflow, workflow_instance=None, workflow_parameters=workflow_parameters)
                self.operation_success(mp, INGEST)
            except Exception as exc:
                self.operation_error(mp, INGEST, exc)
        else:
            if not workflow:
                properties = mp.getOCCaptureAgentProperties()

                try:
                    workflow = properties['org.opencastproject.workflow.definition']
                except Exception as exc:
                    self.logger.error(exc)
                    workflow = None

                workflow_parameters = {}
                for k, v in properties.iteritems():
                    if k[0:36] == 'org.opencastproject.workflow.config.':
                        workflow_parameters[k[36:]] = v

            try:
                self.oc_client.ingest(ifile.name, mp.getIdentifier(), workflow, mp.getIdentifier(), workflow_parameters)
                self.operation_success(mp, INGEST)
            except Exception as exc:
                self.operation_error(mp, INGEST, exc)
            
        ifile.close()
        self.repo.update(mp)
            
        self.dispatcher.emit('action-mm-refresh-row', mp.identifier)


    def export_to_zip(self, mp, params={}):
        """Sets mediapackage status to be exported as a zip.
        Adds the export operation to the threads queue.
        Args:
            mp (Mediapackage): the mediapackage to be exported as a zip.
            location (str): absolute path of the destination export file.
        """
        self.logger.info('Creating ExportToZIP Job for MP {0}'.format(mp.getIdentifier()))
        mp.setOpStatus('exporttozip',mediapackage.OP_PENDING)
        self.repo.update(mp)
        self.jobs.put((self._export_to_zip, (mp, params)))


    def _export_to_zip(self, mp, params={}):
        """Tries to immediately export the mediapackage to a particular location as a zip.
        If the exportation cannot be done, logger prints it properly.
        Args:
            mp (Mediapackage): the mediapackage to be exported as a zip.
            location (str): absolute path of the destination export file.
            is_action (bool): true if the action was done by the user. False if is a subtask. 
        """
        location = self.gen_location('zip') if not "location" in params else params["location"]
        is_action = True if not "is_action" in params else params["is_action"]

        if is_action:
            self.logger.info("Executing ExportToZIP for MP {} to {}".format(mp.getIdentifier(), location if type(location) in [str,unicode] else location.name))
            mp.setOpStatus('exporttozip',mediapackage.OP_PROCESSING)
            self.dispatcher.emit('operation-started', 'exporttozip', mp)
            self.repo.update(mp)
        else:
            self.logger.info("Zipping MP {} to {}".format(mp.getIdentifier(), location if type(location) in [str,unicode] else location.name))
        try:
            serializer.save_in_zip(mp, location, self.use_namespace, self.logger)
            if is_action:
                self.operation_success(mp, ZIPPING)        
        except Exception as exc:
            if is_action:
                self.operation_error(mp, ZIPPING, exc)
            else:
                pass
        self.repo.update(mp)


    def side_by_side(self, mp, params={}):
        """Sets the mediapackage status in order to do side by side operation.
            Adds the side by side operation to the threads queue.
        Args:
            mp (Mediapackage): the mediapackage.
            location (str): the location for the new video file.
        """
        self.logger.info('Creating SideBySide Job for MP {0}'.format(mp.getIdentifier()))
        mp.setOpStatus('sidebyside',mediapackage.OP_PENDING)
        self.repo.update(mp)
        self.jobs.put((self._side_by_side, (mp, params)))


    def _side_by_side(self, mp, params={}):
        """Tries to immediately do the side by side operation to a mediapackage.
        If the side by side operation cannot be done, logger prints it properly.
        Args:
            mp (Mediapackage): the mediapackage.
            location (str): the location for the new video file.
        """
        location = self.gen_location('mp4') if not "location" in params else params["location"]
        audio_mode    = "auto" if not "audio" in params else params["audio"]
        sbs_layout    = self.sbs_layout if not "layout" in params else params["layout"]

        if audio_mode not in ["embedded", "external", "auto"]:
            self.logger.warning("SideBySide for MP {}: unknown value {} for parameter 'audio', default to auto-mode".format(mp.getIdentifier(), audio))
            audio_mode = "auto"

        self.logger.info('Executing SideBySide for MP {0}'.format(mp.getIdentifier()))
        mp.setOpStatus('sidebyside',mediapackage.OP_PROCESSING)
        self.repo.update(mp)
        self.dispatcher.emit('operation-started', 'sidebyside', mp)

        audio = None  #'camera'
        camera = screen = None

        for track in mp.getTracksVideoMaster():
            if track.getFlavor()[0:9] == 'presenter':
                camera = track.getURI()
            if track.getFlavor()[0:12] == 'presentation':
                screen = track.getURI()

        if mp.getTracksAudio():
            audio = mp.getTracksAudio()[0].getURI()

        try:
            
            if not camera or not screen:
                raise IOError, 'Error in SideBySide proccess: Two videos needed (with presenter and presentation flavors)'

            if audio_mode == "auto":                
                self.logger.debug('SideBySide for MP {0}: auto audio-mode'.format(mp.getIdentifier()))

                # Look for embedded audio track, if this not exists use external audio
                info = get_info(camera)
                if 'audio-codec' in info.get_stream_info().get_streams()[0].get_tags().to_string():
                    self.logger.debug('SideBySide for MP {0}: embedded audio detected'.format(mp.getIdentifier()))
                    audio = None
                else:
                    self.logger.debug('SideBySide for MP {0}: embedded audio NOT detected, trying to use external audio...'.format(mp.getIdentifier()))

            elif audio_mode == "embedded":
                self.logger.debug('SideBySide for MP {0}: embedded audio-mode'.format(mp.getIdentifier()))

                # Look for embedded audio track, if this not exists use external audio
                info = get_info(camera)                
                if 'audio-codec' in info.get_stream_info().get_streams()[0].get_tags().to_string():
                    self.logger.debug('SideBySide for MP {0}: embedded audio detected'.format(mp.getIdentifier()))
                    audio = None
                else:
                    self.logger.debug('SideBySide for MP {0}: embedded audio NOT detected, trying to use external audio...'.format(mp.getIdentifier()))

            else:
                self.logger.debug('SideBySide for MP {0}: external audio-mode'.format(mp.getIdentifier()))
                if not audio:
                    self.logger.debug('SideBySide for MP {0}: external audio NOT detected, trying to use embedded audio...'.format(mp.getIdentifier()))

            sidebyside.create_sbs(location, camera, screen, audio, sbs_layout, self.logger)
            self.operation_success(mp, SBS)
        except Exception as exc:
            self.operation_error(mp, SBS, exc)

        self.repo.update(mp)


    def operation_error(self, mp, OP_NAME, exc):
        self.logger.error("Failed {} for MP {}. Exception: {}".format(OP_NAME, mp.getIdentifier(), exc))
        mp.setOpStatus(JOBS[OP_NAME], mediapackage.OP_FAILED)
        self.dispatcher.emit('operation-stopped', JOBS[OP_NAME], mp, False, None)
        self.repo.update(mp)

    def operation_success(self, mp, OP_NAME):
        self.logger.info("Finalized {} for MP {}".format(OP_NAME, mp.getIdentifier()))
        mp.setOpStatus(JOBS[OP_NAME], mediapackage.OP_DONE)
        self.dispatcher.emit('operation-stopped', JOBS[OP_NAME], mp, True, None)
        self.repo.update(mp)


    def operation_nightly(self, mp, operation, params={}):
        """Adds a mediapackage operation to be done at nightly configured time.
        Args:
            mp (Mediapackage): the mediapackage with a operation to be processed.
            operation (str): name of the nighly operation to be done.
        """
        self.logger.debug("Set nightly operation {} for MP {}".format(operation, mp.getIdentifier()))
        mp.setOpStatus(operation,mediapackage.OP_NIGHTLY)
        self.repo.update(mp)
        self.dispatcher.emit('refresh_row', mp.identifier)


    def cancel_nightly(self, mp, operation):
        """Removes a mediapackage operation to be done at nightly configured time.
        Args:
            mp (Mediapackage): the mediapackage with a operation to be processed.
            operation (str): name of the nightly operation to be canceled.
        """
        self.logger.debug("Cancel nightly operation {} for MP {}".format(operation, mp.getIdentifier()))
        mp.setOpStatus(operation,mediapackage.OP_IDLE)
        self.repo.update(mp)
        self.dispatcher.emit('refresh_row', mp.identifier)
    

    def exec_nightly(self, sender=None): 
        """Executes immediately all the nightly operations of all the mediapackages in the repository.
        Args:
            sender (Dispatcher): instance of the class in charge of emitting signals.
        """
        self.logger.info('Executing nightly process')
        for mp in self.repo.values():
            for (op_name, op_status) in mp.operation.iteritems():
                if op_status == mediapackage.OP_NIGHTLY:
                    if op_name == INGEST_CODE:
                        self.ingest(mp)
                    elif op_name == ZIPPING_CODE:
                        self.export_to_zip(mp)
                    elif op_name == SBS_CODE:
                        self.side_by_side(mp)                    
        
