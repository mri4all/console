import sys
import common.logger as logger

import common.runtime as rt

rt.set_service_name("acq")
log = logger.get_logger()

def run():
    log.info('Acquisition service started')
    log.debug('This is a debug message')    
    sys.exit()

if __name__ == '__main__':
    run()
