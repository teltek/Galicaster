# Galicaster, Multistream Recorder and Player
#
# Makefile for developing process: uses ´nosetests´ and ´pychecker´ apps
#
# $ pip install nose pychecker
#
# Copyright (c) 2012, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.
all: test
test:
	nosetests --all-modules -a '!nodefault'
test-matterhorn:
	nosetests --all-modules -a 'matterhorn'
test-recorder:
	nosetests --all-modules -a 'recorder'
test-all:
	nosetests --all-modules --no-skip
check:
	pychecker `find galicaster -name '*.py'`
	pychecker `find test -name '*.py'`
