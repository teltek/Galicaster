# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       tests/core/profile
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import os
import shutil
from os import path
from unittest import TestCase
from unittest import skip

from tests import get_resource
from galicaster.core.conf import Conf
from galicaster.core.conf import Profile
from galicaster.core.conf import Track

class TestFunctions(TestCase):
    def setUp(self):
        self.conf_file = get_resource('profile/conf_good.ini')
        self.backup_conf_file = get_resource('profile/conf_good_backup.ini')
        conf_dist_file = get_resource('profile/conf-dist.ini')
        folder_path = get_resource('profile/folder')

        shutil.copyfile(self.conf_file,self.backup_conf_file)
        self.conf = Conf(self.conf_file,conf_dist_file, folder_path)
        self.conf.reload()

        
    def tearDown(self):
        shutil.copyfile(self.backup_conf_file,self.conf_file)
        os.remove(self.backup_conf_file)
        del self.conf

        
    @skip("out of scope")
    def test_create_profile(self):
        profile=Profile("New profile")
        self.assertEqual(profile.name, "New profile")    


    @skip("out of scope")
    def test_create_and_add_profile(self):
        self.setUp()
        profile=Profile("New")
        self.conf.add_profile(profile)
        self.assertEqual(self.conf.get_profiles().has_key("New"),True)    

    
    @skip("out of scope")
    def test_write_profile(self):
        self.setUp()
        folder_path = path.join(path.dirname(path.abspath(__file__)), 
                                'resources', 'profile', 'folder')

        profile=Profile("New profile", path.join(folder_path,"profile11.ini"))
    
        self.conf.add_profile(profile)
        self.conf.update_profiles()
        path.isfile(path.join(folder_path,"profile11.ini"))
        os.remove(path.join(folder_path,"profile11.ini"))


    @skip("out of scope")
    def test_write_profile_default_naming(self):
        self.setUp()
        folder_path = path.join(path.dirname(path.abspath(__file__)),
                                'resources', 'profile', 'folder')

        profile=Profile("New profile")
        profile.path=self.conf.get_free_profile()
        self.conf.add_profile(profile)
        self.conf.update_profiles()
        path.isfile(path.join(folder_path,"profile1.ini"))
        os.remove(path.join(folder_path,"profile1.ini"))


    @skip("out of scope")
    def test_delete_profile(self):
        self.setUp()
        folder_path = path.join(path.dirname(path.abspath(__file__)),
                                'resources', 'profile', 'folder')

        profile=Profile("New")
        profile.path=self.conf.get_free_profile()
        self.conf.add_profile(profile)
        self.conf.update_profiles()
        profile.to_delete = True
        self.conf.update_profiles()
        self.assertEqual(path.isfile(path.join(folder_path,"profile1.ini")),False)
        #os.remove(path.join(folder_path,"profile1.ini"))
        return True
    
    def change_parameters():
        return True

    def change_properties():
        return True

    def load_default_profile(self):
        return True

    def load_default_profile_on_dist(self):
        return True

    def see_all_tracks_in_conf(self):
        return True

    def look_for_an_unexisting_profile(self):
        return True
    
    def loof_for_an_existing_profile(self):
        return True

    def test_change_current_profile(self):
        self.conf.change_current_profile('test2')
        self.assertEqual(self.conf.get_current_profile().name, 'test2')
        self.assertEqual(self.conf.get('basic', 'profile'), 'test2')
        
        self.conf.change_current_profile('test')
        self.assertEqual(self.conf.get('basic', 'profile'), 'test')

        # Does not exist, so there is no change
        self.conf.change_current_profile('test9999999')
        self.assertEqual(self.conf.get('basic', 'profile'), 'test')

    def delete_current_profile(self):
        return True
    
    def set_default_to_current(self):
        return True

    def add_track():
        return True

    def delete_track():
        return True

    def get_video_areas_on_profile():
        return True

    def get_videos_areas_in_order():
        return True

    def get_video_areas_on_pulse_profile():
        return True
