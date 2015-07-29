import sys
import os
import galiconf
import re

from cStringIO import StringIO

class GCDevice:
    def __init__(self):
        self.name = "empty" # Device nam, i. e.  Hauppage WinTW 350
        self.type = "none" # v4l or v4l2  
        self.location = "" # path
        self.source = "videotestrc" # type of gstreamer soure (file,v4l...)
        self.input = -1 # chosen input to receive data, usually 0 or 1
        self.standard = "not defined yet" # palette format or standard 

def main(args):
    
    def usage():
        sys.stderr.write("usage: %s file_name \n" % args[0])
	#ejemplo python configurador.py epiphan.cgc
        return 1    

    def conf(Device):
        if Device.type=="v4l" :
            os.system("dov4l -d " + Device.location + " -i " + Device.input + " -p  " + Device.standard)
            return 0
        elif Device.type=="v4l2" :
            os.system("v4l2-ctl -d " + Device.location + " -i " + Device.input + " -s  " + Device.standard)
            return 0
        else: 
            return -1

    if len(args) != 2:
        return usage()
    else:
        dev = GCDevice()
        f = open(args[1], 'r')
        for line in f:
            lista = line.split('=')
            lista[1]=lista[1].replace("\n","") # del breakline
            if lista[0] == "type" : dev.type=lista[1]
            elif lista[0] == "name": dev.name = lista[1]
            elif lista[0] == "device": dev.location = lista[1]
            elif lista[0] == "source": dev.source = lista[1]
            elif lista[0] == "input": dev.input = lista[1]
            elif lista[0] == "standard": dev.standard = lista[1]
            elif lista[0] == "palette": dev.standard = lista[1]            
#for ends here
        print dev.source #DELETE
        comando = conf(dev)
        if comando!=0: print "ERROR: not a proper device or unknow error"

    return comando

if __name__ == '__main__':
    sys.exit(main(sys.argv))
