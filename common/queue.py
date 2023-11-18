import os
import time
from typing import Dict
from pathlib import Path
import common.runtime as rt
import common.logger as logger

log = logger.get_logger()

import common.helper as helper
from common.constants import *


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
    if not create_folder(mri4all_paths.DATA_STATE):
        return False
    if not prepare_state():
        return False

    log.info("All folders exist")
    return True


def move_task(folder_path, target) -> bool:
    log.info(f"Moving folder {folder_path} to {target}")

    if not os.path.isdir(folder_path):
        log.warn(f"Folder not found at {folder_path}")
        return False

    # Check if the folder already exists in the target path
    if os.path.isdir(target + "/" + os.path.basename(folder_path)):
        log.error(f"Folder already exists at {target}")
        return False

    # Create lock file to make sure that no other service is accessing the folder
    lock_file = Path(folder_path + "/" + mri4all_files.LOCK)
    try:
        lock_file.touch(exist_ok=False)
    except Exception:
        log.error(f"Error locking folder to be moved {folder_path}")
        return False

    # Move the folder to the target location
    try:
        os.rename(folder_path, target + "/" + os.path.basename(folder_path))
    except Exception:
        log.error(f"Error moving folder {folder_path}")
        return False

    # Remove the lock file (note: the lockfile is at a different location now)
    lock_file = Path(
        target + "/" + os.path.basename(folder_path) + "/" + mri4all_files.LOCK
    )
    try:
        lock_file.unlink()
    except Exception:
        log.error(f"Error unlocking folder to be moved {folder_path}")
        return False

    return True


def clear_folder(folder_path, target_path=mri4all_paths.DATA_ARCHIVE) -> bool:
    if not os.path.isdir(folder_path):
        log.warn(f"Unable to access folder {folder_path}")
        return True

    # Iterate over all folders in the given path and move them to the archive folder
    for folder in os.listdir(folder_path):
        if folder == "." or folder == "..":
            continue

        # Check if the folder contains a lock file. If so, the folder is currently being processed
        # and should not be moved
        if os.path.isfile(folder_path + "/" + folder + "/" + mri4all_files.LOCK):
            log.warn(f"Folder {folder} is locked. Skipping...")
            continue

        log.info(f"Moving folder {folder} to {target_path}")
        if not move_task(folder_path + "/" + folder, target_path):
            log.error(f"Failed to move folder {folder} to archive {target_path}")
            return False

    return True


def prepare_state() -> bool:
    folder_path = mri4all_paths.DATA_STATE
    if not os.path.isdir(folder_path):
        log.warn(f"Unable to access STATE folder")
        return True

    if os.path.isfile(folder_path + "/" + mri4all_files.LOCK):
        # Wait one second and try again
        time.sleep(1)
        if os.path.isfile(folder_path + "/" + mri4all_files.LOCK):
            log.warn(f"State folder is locked. Unable to prepare state folder...")
            return False

    # Iterate over all files and delete everything except the tune-up file
    for file in os.listdir(folder_path):
        if file == "." or file == "..":
            continue

        # TODO

        # log.info(f"Moving folder {folder} to {target_path}")
        # if not move_task(folder_path + "/" + folder, target_path):
        #     log.error(f"Failed to move folder {folder} to archive {target_path}")
        #     return False

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
    if not prepare_state():
        return False

    return True


def get_scan_ready_for_acq() -> str:
    scanpath_ready_for_acq = ""

    folders = sorted(Path(mri4all_paths.DATA_QUEUE_ACQ).iterdir(), key=os.path.getmtime)
    for entry in folders:
        if (
            entry.is_dir()
            and (entry / mri4all_files.PREPARED).exists()
            and (not (entry / mri4all_files.EDITING).exists())
            and (not (entry / mri4all_files.LOCK).exists())
        ):
            scanpath_ready_for_acq = entry.name
            break

    return scanpath_ready_for_acq


def get_scan_ready_for_recon() -> str:
    scanpath_ready_for_recon = ""

    folders = sorted(
        Path(mri4all_paths.DATA_QUEUE_RECON).iterdir(), key=os.path.getmtime
    )
    for entry in folders:
        if entry.is_dir() and (not (entry / mri4all_files.LOCK).exists()):
            scanpath_ready_for_recon = entry.name
            break

    return scanpath_ready_for_recon
