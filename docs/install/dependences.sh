#!/bin/bash

# Gstreamer
sudo apt-get install --yes gstreamer0.10-ffmpeg gstreamer0.10-alsa gstreamer0.10-plugins-bad gstreamer0.10-plugins-bad-multiverse gstreamer0.10-plugins-base gstreamer0.10-plugins-base-apps gstreamer0.10-plugins-good 
sudo apt-get install --yes gstreamer0.10-plugins-ugly 
# python-setuptools y pip
sudo apt-get install --yes python-pip python-setuptools
# iCalendar
sudo pip install icalendar
# pyCurl
sudo apt-get install --yes python-pycurl
# Herramientas de configuración de tarjetas capturadoras
sudo apt-get install --yes v4l-conf v4l-utils guvcview
# Paquete para usar glade en python (i18n)
sudo apt-get install --yes phyton-glade2
# Python-bottle for the REST plugin
sudo apt-get install --yes python-bottle
