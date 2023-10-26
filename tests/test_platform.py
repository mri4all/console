import os
import sys

sys.path.append("../")
sys.path.append("/opt/mri4all/console/external/")

import common.logger as logger
import common.runtime as rt

rt.set_service_name("tests")
log = logger.get_logger()


import common.helper as helper
from common.constants import *
import common.queue as queue


def run_platform_tests() -> bool:
    log.info("Running tests for platform...")
    log.info("")

    if not queue.check_and_create_folders():
        log.error("Failed to create data folders")
        return False

    return True


if __name__ == "__main__":
    run_platform_tests()
