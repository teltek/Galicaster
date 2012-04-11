Galicaster UDEV
===============

Create the file /etc/udev/rules.d/galicaster.rules [1] where the udev rules to be applied to the devices will be added.

These are some configuration examples:

KERNEL=="video[0-9]*", ATTR{name}=="Epiphan VGA2USB #V2U19350", GROUP="video", SYMLINK+="screen"
KERNEL=="video[0-9]*", ATTR{name}=="ivtv0 encoder MPG", GROUP="video", SYMLINK+="camera"
KERNEL=="video[0-9]*", ATTR{name}=="UVC Camera (046d:0821)", GROUP="video", SYMLINK+="webcam"
KERNEL=="video[0-9]*", ATTR{name}=="ivtv0 encoder MPG", GROUP="video", SYMLINK+="haucamera"
KERNEL=="video[0-9]*", ATTR{name}=="ivtv0 encoder YUV", GROUP="video", SYMLINK+="hauprevideo"
KERNEL=="video[0-9]*", ATTR{name}=="ivtv0 encoder PCM", GROUP="audio", SYMLINK+="haupreaudio"

Use the following command to find out the value of ATTR{name}:
   
   $ udevadm info --attribute-walk --name=${device}

substituting "${device}" for the device's mount point (e.g. /dev/video0)


------------------------------------------------
[1] If this is a hybrid Galicaster-Matterhorn installation, the file 

       /etc/udev/rules.d/matterhorn.rules

    may be used instead, if it exists, by modifying it according to our needs.
    In this case, Matterhorn configuration may need to be also adjusted.
