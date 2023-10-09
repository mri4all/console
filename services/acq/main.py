import sys

import common.logger as logger
import common.runtime as rt

rt.set_service_name("acq")
log = logger.get_logger()

from common.version import mri4all_version


def run():
    log.info(f"-- MRI4ALL {mri4all_version.get_version_string()} --")
    log.info("Acquisition service started")
    log.debug("This is a debug message")
    rt.set_current_task_id("1234")
    log.info("Acquisition service terminated")
    log.info("-------------")
    sys.exit()


if __name__ == "__main__":
    run()
