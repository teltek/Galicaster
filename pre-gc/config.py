import sys
import os
import galiconf
import re

from cStringIO import StringIO


def main(args):

    def usage():
        sys.stderr.write("usage: %s device input_number STD_number format_number \n" % args[0])
        return 1


    if len(args) != 5:
        return usage()
            
    cap=galiconf.Capture(args[1])
    cap.setInput(int(args[2]))
    cap.setStd(int(args[3]))
    formats = cap.getFormats()
    cap.setFormat(int(args[4]))
    
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
