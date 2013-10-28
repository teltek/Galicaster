import threading
import zbar

from galicaster.core import context
from galicaster.classui.recorderui import RecorderClassUI
import time

class QR_Code(threading.Thread):
    def __init__(self, logger = None):
        threading.Thread.__init__(self)
        self.logger = logger
        self.logger.info("in qrCode init")
        self.running = True;
        
    def run(self):    
        # create a Processor
        proc = zbar.Processor()
        self.logger.info("in qrCode run")
        # configure the Processor
        proc.parse_config('enable')
    
        # initialize the Processor
#        device = RecorderClassUI.get_videoView()
#        proc.init(device)
#        proc.set_data_handler(self.my_handler)
        # initiate scanning
#        proc.active = True
        while (self.running) :
            self.logger.info("in qrCode loop")
            time.sleep(.25)
#            proc.user_wait()

    # setup a callback
    def my_handler(self, proc, image, closure):
        # extract results
        self.logger.info("in qrCode my_handler")
        for symbol in image:
            if not symbol.count:
                self.logger.info('decoded %s - $s',symbol.type,  symbol.data)  # do something useful with results
                print 'decoded', symbol.type, 'symbol', '"%s"' % symbol.data

    def stop(self, signal):
        self.running = False


def init():
    dispatcher = context.get_dispatcher()
    conf = context.get_conf()
    logger = context.get_logger()
    logger.info("got conf %s and dispatcher %s", conf, dispatcher)
    readqr = QR_Code(logger)
#    readqr.daemon(True)
    readqr.start()
    dispatcher.connect('galicaster-quit', readqr.stop)

