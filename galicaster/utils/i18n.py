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
from gettext import bindtextdomain, textdomain

i18n_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "i18n"))

t = gettext.translation("galicaster", i18n_path, fallback=True)
_ = t.ugettext

bindtextdomain("galicaster", i18n_path)
textdomain("galicaster")

