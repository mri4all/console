import common.logger as logger
import common.runtime as rt

log = logger.get_logger()

import common.queue as queue
from common.constants import *
import common.task as task
from common.types import ScanTask

import services.recon.utils as utils
import time


def run_reconstruction(folder: str, task: ScanTask) -> bool:
    """
    Perform the reconstruction of the scan contained in the given folder. Scan information such
    as sequence, protocol name, patient information and system information can be found in the
    task object.
    """
    log.info("Hello recon team, here is your entry point!")
    log.info(f"Folder where the task is = {folder}")
    log.info(f"JSON information = {task}")
    log.info(f"Access data in the JSON like this: {task.protocol_name}")

    # To see what's available in the JSON, take a look at common/types.py

    if task.processing.recon_mode == "fake_dicoms":
        utils.generate_fake_dicoms(folder, task)
        time.sleep(2)

    return True
