import os
import common.runtime as rt
import common.logger as logger
from common.constants import *

log = logger.get_logger()


def create_folder(folder_path) -> bool:
    if not os.path.isdir(folder_path):
        log.warn(f"Folder not found at {folder_path}")
        try:
            os.mkdir(folder_path)
            log.info(f"Created data folder at {folder_path}")
        except:
            log.error(f"Failed to create data folder at {folder_path}")
            return False

    return True


def check_and_create_folders() -> bool:
    log.info("Checking for existence of data folders...")

    if not create_folder(mri4all_paths.DATA):
        return False
    if not create_folder(mri4all_paths.DATA_ACQ):
        return False
    if not create_folder(mri4all_paths.DATA_RECON):
        return False
    if not create_folder(mri4all_paths.DATA_QUEUE_ACQ):
        return False
    if not create_folder(mri4all_paths.DATA_QUEUE_RECON):
        return False
    if not create_folder(mri4all_paths.DATA_COMPLETE):
        return False
    if not create_folder(mri4all_paths.DATA_FAILURE):
        return False
    if not create_folder(mri4all_paths.DATA_ARCHIVE):
        return False

    log.info("All folders exist")
    return True


def clear_folder(folder_path) -> bool:
    # TODO
    return True


def move_task(folder_path, target) -> bool:
    # TODO: Incomplete
    return True


def clear_folders() -> bool:
    log.info("Clearing data folders for next exam...")

    if not clear_folder(mri4all_paths.DATA_ACQ):
        return False
    if not clear_folder(mri4all_paths.DATA_RECON):
        return False
    if not clear_folder(mri4all_paths.DATA_QUEUE_ACQ):
        return False
    if not clear_folder(mri4all_paths.DATA_QUEUE_RECON):
        return False
    if not clear_folder(mri4all_paths.DATA_COMPLETE):
        return False
    if not clear_folder(mri4all_paths.DATA_FAILURE):
        return False

    return True
