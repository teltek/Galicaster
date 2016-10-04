#!/bin/bash

# Gstreamer
sudo apt-get install gstreamer1.0-alsa gstreamer1.0-plugins-bad gstreamer1.0-plugins-base gstreamer1.0-plugins-base-apps gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly
# python-setuptools y pip
sudo apt-get install --yes python-pip python-setuptools
# iCalendar
sudo pip install icalendar
# LDAP
sudo apt-get install libsasl2-dev python-dev libldap2-dev libssl-dev
sudo pip install python-ldap
# pyCurl
sudo apt-get install --yes python-pycurl
# Herramientas de configuración de tarjetas capturadoras
sudo apt-get install --yes v4l-conf v4l-utils guvcview
# Python-bottle for the REST plugin
sudo apt-get install --yes python-bottle
# The Python 2.x binding generator for libraries that support gobject-introspection
sudo apt-get install python-gi
# Python-dbus
sudo apt-get install python-dbus
# Libav
sudo apt-get install gstreamer1.0-libav
# Serial com
sudo pip install pyserial
