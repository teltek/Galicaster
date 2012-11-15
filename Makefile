all: check
check:
	pychecker `find galicaster -name '*.py'`
	pychecker `find test -name '*.py'`
