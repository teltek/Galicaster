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
all:
	@echo '   _____       _ _               _            '
	@echo '  / ____|     | (_)             | |           '
	@echo ' | |  __  __ _| |_  ___ __ _ ___| |_ ___ _ __ '
	@echo ' | | |_ |/ _` | | |/ __/ _` / __| __/ _ \ "__|'
	@echo ' | |__| | (_| | | | (_| (_| \__ \ ||  __/ |   '
	@echo '  \_____|\__,_|_|_|\___\__,_|___/\__\___|_|   '
	@echo ''
	@echo ''
	@echo 'make test                    - Run all the unit test (using nosetest)'
	@echo 'make test-with-coverage      - Run all the unit test (using nosetest) and gen coverage info'
	@echo 'make test-with-coverage-html - Run all the unit test (using nosetest) and gen coverage info as an html page'
	@echo 'make test-opencast           - Run the opencast test (network access needed)'
	@echo 'make test-recorder           - Run the recorder test (gstreamer needed)'
	@echo 'make test-functional         - Run functional tests'
	@echo 'make test-all                - Run all the test (using nosetest)'
	@echo 'make check                   - Check the python source code (using pychecker)'
	@echo 'make doblecheck              - Check the python source code (using pyflakes)'
	@echo 'make pep8                    - Run PEP8 compliance tests(using pep8)'
test:
	nosetests --all-modules -a '!nodefault'
test-travis: check
	nosetests --all-modules -a '!nodefault,!notravis' --with-coverage --cover-inclusive --cover-package=galicaster
test-with-coverage:
	nosetests --all-modules -a '!nodefault' --with-coverage --cover-inclusive --cover-package=galicaster
test-with-coverage-html:
	nosetests --all-modules -a '!nodefault' --with-coverage --cover-inclusive --cover-package=galicaster --cover-html
test-opencast:
	nosetests --all-modules -a 'opencast'
test-recorder:
	nosetests --all-modules -a 'recorder'
	#python -m unittest tests.recorder.recorder
test-functional:
	nosetests --all-modules -a 'functional'
test-all:
	nosetests --all-modules --no-skip
check:
	flake8 --ignore=E,W --builtins="int,long,unicode" --format pylint `find galicaster -name '*.py'`
doblecheck:
	pyflakes `find galicaster -name '*.py'`
	pyflakes `find test -name '*.py'`
pep8:
	-pep8 -r --ignore=E501,E221,W291,W391,E302,E251,E203,W293,E231,E303,E201,E225,E261,E241 galicaster
