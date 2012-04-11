Epiphan VGA2PCI Module Installation
===================================

See http://www.epiphan.com/downloads/linux/vga2pci/

Follow the instructions in the README file to complete the driver installation.

Run the following commands in a shell (requires being root) to use the driver like a modprobe.

install -m 0644 vga2pci.ko /lib/modules/$(uname -r)/kernel/drivers/video/
echo options vga2pci v4l_num_buffers=2 v4l_err_on_nosignal=0 > /etc/modprobe.d/vga2pci.conf
echo softdep vga2pci pre: videodev post: >> /etc/modprobe.d/vga2pci.conf
depmod -a
echo vga2pci >> /etc/modules
