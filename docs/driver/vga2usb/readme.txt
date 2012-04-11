Epiphan VGA2USB Module Installation
===================================

See http://www.epiphan.com/downloads/linux/

Follow the instructions in the README file to complete the driver installation.

Run the following commands in a shell (requires being root) to use the driver like a modprobe.

install -m 0644 vga2usb.ko /lib/modules/$(uname -r)/kernel/drivers/video/
echo options vga2usb v4l_num_buffers=2 v4l_err_on_nosignal=0 > /etc/modprobe.d/vga2usb.conf
echo softdep vga2usb pre: videodev usbvideo post: >> /etc/modprobe.d/vga2usb.conf
depmod -a
