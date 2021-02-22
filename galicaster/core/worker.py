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
import tempfile
import queue
import json

from datetime import datetime

from galicaster.mediapackage import serializer
from galicaster.mediapackage import mediapackage
from galicaster.utils import sidebyside
from galicaster.utils.mediainfo import get_info

from galicaster.utils.queuethread import T

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

F_OPERATION = {}
F_OPERATION_QUEUED = {}
"""
This class manages the long operations to be done with a mediapackage:
    Ingest it into opencast server.
    Save it as a zip.
    Do side by side.
This operations are threads concurrently done with the rest of galicaster tasks to avoid blocking them.
"""
class Worker(object):

    def __init__(self, dispatcher, repo, logger, oc_client=None, export_path=None, tmp_path=None,
                 use_namespace=True, sbs_layout='sbs', hide_ops=[], hide_nightly=[], min_length=0):
        """Initializes a worker that manages the mediapackages of the repository in order to do long operations concurrently by throwing Threads when necessay.
        Args:
            dispacher (Dispatcher): the galicaster event-dispatcher to emit signals.
            repo (Repository): the galicaster mediapackage repository.
            logger (Logger): the object that prints all the information, warning and error messages.
            oc_client (OCHTTPClient): the opencast HTTP client.
            export_path (str): the absolute path where galicaster exports zip and sidebyside.
            tmp_path (str): temporary path (needed if /tmp partition is small).
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
        self.min_length = min_length * 1000

        for dir_path in (self.export_path, self.tmp_path):
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)

        self.add_operation(SBS, SBS_CODE, self._side_by_side)
        self.add_operation(INGEST, INGEST_CODE, self._ingest)
        self.add_operation(ZIPPING, ZIPPING_CODE, self._export_to_zip)

        self.jobs = queue.Queue()

        self.t = T(self.jobs)
        self.t.setDaemon(True)
        self.t.start()

        self.dispatcher.connect('timer-nightly', self.exec_nightly)

    def get_all_job_types(self):
        """Gets all the possible mediapackage operations.
        Returns:
            List[str]: List of the possible operations (including nightly mode)
        """
        nn = ' Nightly'

        operation_list = []
        for k in list(JOBS.keys()):
            operation_list.extend([k, k+nn])

        return operation_list


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

        for key,value in list(JOBS.items()):
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

        for key,value in list(JOBS.items()):
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


    def do_job_by_name(self, name, mp, params={}):
        """Does a particular operation for a particular mediapackage.
        Args:
            name (str): the name of the operation (code).
            mp_id (str): the mediapackage id.
        Returns:
            Bool: True if success. False otherwise.
        """
        try:
            if isinstance(mp, str):
                mp = self.repo[mp]
            f = F_OPERATION[name]
        except Exception as exc:
            self.logger.error("Fail get MP {0} or operation with name {1}. Exception: {2}".format(mp, name, exc))
            return False
        f(mp, params)
        return True


    def enqueue_job_by_name(self, name, mp, params={}):
        """Enqeues a particular mediapackage operation to be done.
        Args:
            name (str): the name of the operation (code).
            mp_id (str): the mediapackage id.
        Returns:
            Bool: True if success. False otherwise.
        """
        try:
            if isinstance(mp, str):
                mp = self.repo[mp]
            f = F_OPERATION_QUEUED[name]
        except Exception as exc:
            self.logger.error("Fail get MP {0} or operation with name {1}. Exception: {2}".format(mp, name, exc))
            return False
        f(mp, params)
        return True

    def enqueue_nightly_job_by_name(self, operation, mp, params={}):
        """Adds a mediapackage operation to be done at nightly configured time.
        Args:
            mp (Mediapackage): the mediapackage with a operation to be processed.
            operation (str): name of the nighly operation to be done.
        """
        self.logger.info("Set nightly operation {} for MP {}".format(operation, mp.getIdentifier()))
        mp.setOpStatus(operation,mediapackage.OP_NIGHTLY)
        mp.setProperty("enqueue_params", json.dumps(params))
        self.repo.update(mp)
        self.dispatcher.emit('action-mm-refresh-row', mp.identifier)

    def do_job(self, name, mp, params={}):
        """Calls a particular method of this class with a given argument.
        The method should execute an operation with the same name.
        Args:
            name (str): the name of a worker method.
            mp (Mediapackage): the mediapackage.
        """
        try:
            # Do not perform immediately operations (it blocks)
            f = F_OPERATION_QUEUED[name]
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
                # getattr(self, name.replace('cancel',''))
                if not name.replace('cancel','') in list(JOB_NAMES.keys()):
                    raise Exception('Unknown operation named {}'.format(name))

                self.cancel_nightly(name.replace('cancel',''), mp)
            else:
                # getattr(self, name)
                if not name in list(JOB_NAMES.keys()):
                    raise Exception('Unknown operation named {}'.format(name))

                self.enqueue_nightly_job_by_name(name, mp, params)
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


    def _ingest(self, mp, params={}):
        """Tries to immediately ingest the mediapackage into opencast.
        If the ingest cannot be done, logger prints it properly.
        Args:
            mp(Mediapackage): the mediapackage to be immediately ingested.
        """
        if not self.oc_client:
            raise Exception('Opencast client is not enabled')

        workflow = None if not "workflow" in params else params["workflow"]
        workflow_parameters = None if not "workflow_parameters" in params else params["workflow_parameters"]

        self.dispatcher.emit('action-mm-refresh-row', mp.identifier)

        if workflow or workflow_parameters:
            self.logger.info("Ingest for MP {}: workflow:{}   workflow_parameters:{} (None means default values)".format(mp.getIdentifier(), workflow, workflow_parameters))

        ifile = tempfile.NamedTemporaryFile(dir=self.tmp_path)
        self._export_to_zip(mp, params={"location" : ifile, "is_action": False})

        if mp.manual:
            if mp.getDuration() > self.min_length or self.min_length == 0:
                self.oc_client.ingest(ifile.name, mp.getIdentifier(), workflow=workflow, workflow_instance=None, workflow_parameters=workflow_parameters)
            else:
                self.logger.info("NOT Ingesting MP {}: duration:{} less than {}".format(mp.getIdentifier(), mp.getDuration(), self.min_length))
        else:
            if not workflow:
                properties = mp.getOCCaptureAgentProperties()

                try:
                    workflow = properties['org.opencastproject.workflow.definition']
                except Exception as exc:
                    self.logger.error(exc)
                    workflow = None

                workflow_parameters = {}
                for k, v in list(properties.items()):
                    if k[0:36] == 'org.opencastproject.workflow.config.':
                        workflow_parameters[k[36:]] = v

            if mp.getDuration() > self.min_length or self.min_length == 0:
                self.oc_client.ingest(ifile.name, mp.getIdentifier(), workflow, mp.getIdentifier(), workflow_parameters)
            else:
                self.logger.info("NOT Ingesting MP {}: duration:{} less than {}".format(mp.getIdentifier(), mp.getDuration(), self.min_length))

        ifile.close()

        self.dispatcher.emit('action-mm-refresh-row', mp.identifier)


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

        if not is_action:
            self.logger.info("Zipping MP {} to {}".format(mp.getIdentifier(), location if type(location) in [str,str] else location.name))

        serializer.save_in_zip(mp, location, self.use_namespace, self.logger)

    def add_operation(self, name, code, handler):
        """Sets an operation in the worker
        Args:
            name (str): operation name.
            code (str): operation identifier.
            handler (function): function to be executed
        """

        JOBS.update({name: code})
        JOB_NAMES.update({code: name})

        operation = self.__create_operation(name, code, handler)
        F_OPERATION.update({code : operation})

        operation_queued = self.__create_operation_queued(name, code, operation)
        F_OPERATION_QUEUED.update({code: operation_queued})


    def __create_operation(self, name, code, handler):

        def handler_template(mp, params={}):
            self.logger.info('Executing {} for MP {}'.format(name, mp.getIdentifier()))
            mp.setOpStatus(code,mediapackage.OP_PROCESSING)
            self.repo.update(mp)
            self.dispatcher.emit('operation-started', code, mp)

            try:
                pending_process = handler(mp, params)
                if not pending_process:
                    self.operation_success(mp, code)
                else:
                    self.logger.info('Completed first part of {} for MP {} (It is not marked as completed until the whole process is done)'.format(name, mp.getIdentifier()))
            except Exception as exc:
                self.operation_error(mp, code, exc)

        return handler_template


    def __create_operation_queued(self, name, code, handler):

        def queued_handler_template(mp, params={}):
            self.logger.info('Creating {} Job for MP {}'.format(name, mp.getIdentifier()))
            mp.setOpStatus(code,mediapackage.OP_PENDING)
            self.repo.update(mp)
            self.jobs.put((handler, (mp, params)))

        return queued_handler_template



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
            self.logger.warning("SideBySide for MP {}: unknown value {} for parameter 'audio', default to auto-mode".format(mp.getIdentifier(), audio_mode))
            audio_mode = "auto"

        audio = None  #'camera'
        camera = screen = None

        for track in mp.getTracksVideoMaster():
            if track.getFlavor()[0:9] == 'presenter':
                camera = track.getURI()
            if track.getFlavor()[0:12] == 'presentation':
                screen = track.getURI()

        if mp.getTracksAudio():
            audio = mp.getTracksAudio()[0].getURI()

        if not camera or not screen:
            raise IOError('Error in SideBySide process: Two videos needed (with presenter and presentation flavors)')

        if audio_mode == "auto":
            self.logger.info('SideBySide for MP {0}: auto audio-mode'.format(mp.getIdentifier()))
            # Look for embedded audio track, if this not exists use external audio
            info = get_info(camera)
            if 'audio-codec' in info.get_stream_info().get_streams()[0].get_tags().to_string():
                self.logger.info('SideBySide for MP {0}: embedded audio detected'.format(mp.getIdentifier()))
                audio = None
            else:
                self.logger.info('SideBySide for MP {0}: embedded audio NOT detected, trying to use external audio...'.format(mp.getIdentifier()))

        elif audio_mode == "embedded":
            self.logger.info('SideBySide for MP {0}: embedded audio-mode'.format(mp.getIdentifier()))
            # Look for embedded audio track, if this not exists use external audio
            info = get_info(camera)
            if 'audio-codec' in info.get_stream_info().get_streams()[0].get_tags().to_string():
                self.logger.info('SideBySide for MP {0}: embedded audio detected'.format(mp.getIdentifier()))
                audio = None
            else:
                self.logger.info('SideBySide for MP {0}: embedded audio NOT detected, trying to use external audio...'.format(mp.getIdentifier()))

        else:
            self.logger.info('SideBySide for MP {0}: external audio-mode'.format(mp.getIdentifier()))
            if not audio:
                self.logger.info('SideBySide for MP {0}: external audio NOT detected, trying to use embedded audio...'.format(mp.getIdentifier()))

        sidebyside.create_sbs(location, camera, screen, audio, sbs_layout, self.logger)



    def operation_error(self, mp, OP_CODE, exc):
        self.logger.error("Failed {} for MP {}. Exception: {}".format(JOB_NAMES[OP_CODE], mp.getIdentifier(), exc))
        mp.setOpStatus(OP_CODE, mediapackage.OP_FAILED)
        self.dispatcher.emit('operation-stopped', OP_CODE, mp, False, exc)
        self.repo.update(mp)


    def operation_success(self, mp, OP_CODE):
        self.logger.info("Finalized {} for MP {}".format(JOB_NAMES[OP_CODE], mp.getIdentifier()))
        mp.setOpStatus(OP_CODE, mediapackage.OP_DONE)
        self.dispatcher.emit('operation-stopped', OP_CODE, mp, True, None)
        self.repo.update(mp)


    def cancel_nightly(self, operation, mp):
        """Removes a mediapackage operation to be done at nightly configured time.
        Args:
            mp (Mediapackage): the mediapackage with a operation to be processed.
            operation (str): name of the nightly operation to be canceled.
        """
        self.logger.info("Cancel nightly operation {} for MP {}".format(operation, mp.getIdentifier()))
        mp.setOpStatus(operation,mediapackage.OP_IDLE)
        self.repo.update(mp)
        self.dispatcher.emit('action-mm-refresh-row', mp.identifier)


    def exec_nightly(self, sender=None):
        """Executes immediately all the nightly operations of all the mediapackages in the repository.
        Args:
            sender (Dispatcher): instance of the class in charge of emitting signals.
        """
        self.logger.info('Executing nightly process')
        for mp in list(self.repo.values()):
            for (op_name, op_status) in list(mp.operations.items()):
                if op_status == mediapackage.OP_NIGHTLY:
                    params = {}
                    if mp.getProperty("enqueue_params"):
                        params = json.loads(mp.getProperty("enqueue_params"))
                    self.enqueue_job_by_name(op_name, mp, params)
