import sys

import common.runtime as rt
import common.logger as logger

rt.set_service_name("recon")
log = logger.get_logger()

from common.version import mri4all_version


def run():
    log.info(f"-- MRI4ALL {mri4all_version.get_version_string()} --")
    log.info("Recon service started")
    log.info("Recon service terminated")
    log.info("-------------")
    sys.exit()


if __name__ == "__main__":
    run()
