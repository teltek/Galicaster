# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/i18n
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

import os
import gettext
import gtk
import gtk.glade


t = gettext.translation('galicaster', 'i18n', fallback=True)
_ = t.ugettext

gtk.glade.bindtextdomain('galicaster', os.path.join(os.getcwd(), 'i18n'))
gtk.glade.textdomain('galicaster')

