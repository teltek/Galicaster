#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#      setup.py
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.


import os
from distutils.core import setup
from distutils.cmd import Command

from unittest import TestLoader, TextTestRunner, TestSuite

import galicaster
import tests

packagetestdir = os.path.dirname(os.path.abspath(tests.__file__))

def pynames_iter(pkdir, pkname = None):
    """
    Recursively yield dotted names for *.py files in directory *pydir*.
    """
    try:
        names = sorted(os.listdir(pkdir))
    except StandardError:
        return
    if not os.path.isfile(os.path.join(pkdir, '__init__.py')):
        return
    if pkname is None:
        pkname = os.path.basename(pkdir)
    yield pkname
    for name in names:
        if name == '__init__.py':
            continue
        if name.startswith('.') or name.endswith('~'):
            continue
        fullname = os.path.join(pkdir, name)
        if os.path.islink(fullname):
            continue
        if os.path.isfile(fullname) and name.endswith('.py'):
            parts = name.split('.')
            if len(parts) == 2:
                yield '.'.join([pkname, parts[0]])
        elif os.path.isdir(fullname):
            for n in pynames_iter(fullname, '.'.join([pkname, name])):
                yield n


class Test(Command):
    description = 'run unit tests and doc tests'

    user_options = [
        ('names=', None, 'comma-sperated list of modules to test'),
    ]

    def _pynames_iter(self):
        for pyname in pynames_iter(packagetestdir):
            if not self.names:
                yield pyname
            else:
                for name in self.names:
                    if name in pyname:
                        yield pyname
                        break
    
    def run(self):
        pynames = tuple(self._pynames_iter())

        # Add unit-tests:
        loader = TestLoader()
        suite = loader.loadTestsFromNames(pynames)
    
        # FIXME ADD doctests
    
        # Run the tests:
        runner = TextTestRunner(verbosity=2)
        result = runner.run(suite)
        if not result.wasSuccessful():
            raise SystemExit(1)
    
    def initialize_options(self):
        self.names = ''
    
    def finalize_options(self):
        self.names = self.names.split(',')


setup(
    name = 'galicaster',
    url = 'http://galicaster.com',
    version = galicaster.__version__,
    cmdclass={
        'test': Test,
        },
    packages=[
        'galicaster',
        'galicaster.player',
        'galicaster.recorder',
        'galicaster.recorder.pipeline',
        'galicaster.scheduler',
        'galicaster.core',
        'galicaster.classui',
        'galicaster.mediapackage',
        'galicaster.utils',
        'galicaster.plugins',
        ],
    requires=["pygst", "pycurl", "icalendar"],
)

