# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/utils/ical
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.


"""
Unit tests for `galicaster.mediapackage` module.
"""
from os import path
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase
from datetime import datetime

from tests import get_resource
from galicaster.mediapackage import repository
from galicaster.utils import ical

class TestFunctions(TestCase):

    base_dir = get_resource('ical')

    def setUp(self):
        self.tmppath = mkdtemp()

    def tearDown(self):
        rmtree(self.tmppath)

    def test_ical_create_mp(self):
        repo = repository.Repository(self.tmppath)

        events = ical.get_events_from_file_ical(path.join(self.base_dir, 'test.ical'))

        for event in events:
            ical.create_mp(repo, event)

        next = repo.get_next_mediapackage()
        self.assertEqual(next.getDate(), datetime.strptime('3016-04-05 11:00:00', '%Y-%m-%d %H:%M:%S'))
        self.assertEqual(len(next.getElements()), 2)
        self.assertEqual(len(next.getAttachments()), 1)
        self.assertTrue(next.getAttachment('org.opencastproject.capture.agent.properties'))
        self.assertEqual(len(next.getCatalogs()), 1)

        nexts = repo.get_next_mediapackages()
        self.assertEqual(nexts[0].getDate(), datetime.strptime('3016-04-05 11:00:00', '%Y-%m-%d %H:%M:%S'))
        self.assertEqual(nexts[0].getDuration(), 1000*60*10)

    def test_ical_create_mp_update(self):
        repo = repository.Repository(self.tmppath)

        events = ical.get_events_from_file_ical(path.join(self.base_dir, 'create_mp_original.ical'))

        for event in events:
            ical.create_mp(repo, event)
        next = repo.get_next_mediapackage()
        self.assertEqual(next.getDate(), datetime.strptime('3018-10-17 08:00:00', '%Y-%m-%d %H:%M:%S'))
        self.assertEqual(len(next.getElements()), 3)
        self.assertEqual(len(next.getAttachments()), 1)
        self.assertTrue(next.getAttachment('org.opencastproject.capture.agent.properties'))
        self.assertEqual(len(next.getCatalogs()), 2)
        self.assertEqual(next.getTitle(), "EVENTO ORIGINAL")
        self.assertEqual(next.getSeriesTitle(), "New")
        self.assertEqual(next.getDuration(), 1000*60*83) # 1h 23min

        events = ical.get_events_from_file_ical(path.join(self.base_dir, 'create_mp_updated.ical'))

        for event in events:
            ical.create_mp(repo, event)
        next = repo.get_next_mediapackage()
        self.assertEqual(next.getDate(), datetime.strptime('3018-10-17 08:00:00', '%Y-%m-%d %H:%M:%S'))
        self.assertEqual(len(next.getElements()), 3)
        self.assertEqual(len(next.getAttachments()), 1)
        self.assertTrue(next.getAttachment('org.opencastproject.capture.agent.properties'))
        self.assertEqual(len(next.getCatalogs()), 2)
        self.assertEqual(next.getTitle(), "EVENTO MODIFICADO")
        self.assertEqual(next.getSeriesTitle(), "New")
        self.assertEqual(next.getDuration(), 1000*60*83) # 1h 23min

    def test_ical_get_events(self):
        events = ical.get_events_from_file_ical(path.join(self.base_dir, 'past_unordered_events.ical'))
        self.assertEqual(len(events), 6)

        events = ical.get_events_from_file_ical(path.join(self.base_dir, 'past_unordered_eventsv2.ical'))
        self.assertEqual(len(events), 4)

    def test_ical_get_deleted_events(self):
        old_events = ical.get_events_from_file_ical(path.join(self.base_dir, 'test.ical'))
        new_events = ical.get_events_from_file_ical(path.join(self.base_dir, 'none.ical'))

        delete_events = ical.get_deleted_events(old_events, new_events)

        self.assertEqual(len(delete_events), 1)


    def test_ical_get_updated_events(self):
        old_events = ical.get_events_from_file_ical(path.join(self.base_dir, 'test.ical'))
        new_events = ical.get_events_from_file_ical(path.join(self.base_dir, 'test_update.ical'))

        update_events = ical.get_updated_events(old_events, new_events)

        self.assertEqual(len(update_events), 0)

    def test_ical_get_updated_events_updates(self):
        old_events = ical.get_events_from_file_ical(path.join(self.base_dir, 'testv2.ical'))
        new_events = ical.get_events_from_file_ical(path.join(self.base_dir, 'testv2_update.ical'))

        update_events = ical.get_updated_events(old_events, new_events)

        self.assertEqual(len(update_events), 6)
