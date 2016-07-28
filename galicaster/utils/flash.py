# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/utils/flash
#
# Copyright (c) 2011, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California, 94105, USA.


"""
Se genera un flash en la pantalla usando las librerias de Xxf86vm en Linux.

Se usa parte de la implementacion de pyglet para obtener el Display que se usa en
la funcion XF86VidModeSetGamma.

Se ha detectado un comportamiento anonimo y para que funciones bien es necesario
llamar a XF86VidModeGetGamma despues que XF86VidModeSetGamma.
"""

import ctypes
from ctypes import *
from ctypes.util import find_library
import thread
import time

try:
    from pyglet import window
    from pyglet.gl.glx import Display
    has_pyglet = True
except:
    has_pyglet = False



if has_pyglet:
    #######################################################
    #######################################################
    #######################################################

    ##
    # Def C types
    ##
    # xf86vmode.h:171
    class XF86VidModeGamma(Structure):
        __slots__ = [
            'red',
            'green',
            'blue',
        ]
    XF86VidModeGamma._fields_ = [
        ('red', c_float),
        ('green', c_float),
        ('blue', c_float),
    ]

    # /usr/include/X11/Xlib.h:519
    # Display

    ##
    # Load LIB
    ##
    library_so_path = find_library('Xxf86vm')
    _lib = ctypes.cdll.LoadLibrary(library_so_path)

    ##
    # Desc FUNC
    ##
    # xf86vmode.h:289
    XF86VidModeSetGamma = _lib.XF86VidModeSetGamma
    XF86VidModeSetGamma.restype = c_int
    XF86VidModeSetGamma.argtypes = [POINTER(Display), c_int, POINTER(XF86VidModeGamma)]

    XF86VidModeGetGamma = _lib.XF86VidModeGetGamma
    XF86VidModeGetGamma.restype = POINTER(Display) # c_int
    XF86VidModeGetGamma.argtypes = [POINTER(Display), c_int, POINTER(XF86VidModeGamma)]



    ##
    # START
    ##
    def _do_flash():
        platform = window.get_platform()
        display = platform.get_default_display()
        x_display = display._display

        gamma_old = XF86VidModeGamma()
        XF86VidModeGetGamma(x_display, 0, gamma_old)

        gamma_old = XF86VidModeGamma()
        XF86VidModeGetGamma(x_display, 0, gamma_old)

        intensities = [ 7.1, 8.1, 9.9]
        #intensities = [ 0.9, 0.6, 0]

        def set_intensity(x_display, inten):
            gamma = XF86VidModeGamma(inten, inten, inten)
            XF86VidModeSetGamma(x_display, 0, gamma)
            XF86VidModeGetGamma(x_display, 0, gamma)

        for inten in sorted(intensities):
            set_intensity(x_display, inten)
            time.sleep(0.05)

        for inten in sorted(intensities, reverse=True):
            set_intensity(x_display, inten)
            time.sleep(0.05)

        XF86VidModeSetGamma(x_display, 0, gamma_old)
        XF86VidModeGetGamma(x_display, 0, gamma_old)



    def _do_flash_in_thread():
        thread.start_new_thread(_do_flash,())


    do_flash = _do_flash_in_thread
else:
    def _do_none():
        pass

    do_flash = _do_none
