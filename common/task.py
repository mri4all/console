import json
import os
from pathlib import Path

import common.logger as logger

log = logger.get_logger()

import common.helper as helper
from common.constants import *
from common.types import ScanTask, PatientInformation

# Incomplete


def create_task(
    exam_id: str,
    scan_id: str,
    scan_counter: int,
    sequence: str,
    patient_information: PatientInformation,
    default_seq_parameters: dict = {},
) -> str:
    """
    Creates a new scan task for the given exam ID. Returns empty string on failure.
    """
    # New jobs are always created in the ACQ folder. Tasks won't be touched by the acq service until
    # a file with name PREPARED is found in the folder.
    folder_name = Path(mri4all_paths.DATA_ACQ) / str(exam_id + mri4all_defs.SEP + f"scan_{scan_counter}")
    lock_file = Path(folder_name) / mri4all_files.LOCK
    task_filename = Path(folder_name) / mri4all_files.TASK

    try:
        os.mkdir(folder_name)
    except Exception:
        log.error(f"Unable to create task folder {folder_name}")
        return ""

    # Create lock file in the folder to prevent other services from accessing it
    try:
        lock = helper.FileLock(lock_file)
    except:
        # Can't create lock file, so something must be seriously wrong
        log.error(f"Unable to create lock file {lock_file}")
        return ""

    # Create new task object that will be written into the json file
    scan_task = ScanTask()
    scan_task.id = scan_id
    scan_task.sequence = sequence
    scan_task.patient = patient_information
    scan_task.parameters = default_seq_parameters

    try:
        with open(task_filename, "w") as task_file:
            json.dump(scan_task.dict(), task_file, indent=4)
    except:
        log.error(f"Unable to scan task file {task_filename}")
        return ""

    # Create the sub-folders for the scan task
    current_subfolder = Path(folder_name)
    try:
        current_subfolder = Path(folder_name) / mri4all_taskdata.RAWDATA
        os.mkdir(current_subfolder)
        current_subfolder = Path(folder_name) / mri4all_taskdata.DICOM
        os.mkdir(current_subfolder)
        current_subfolder = Path(folder_name) / mri4all_taskdata.OTHER
        os.mkdir(current_subfolder)
    except Exception:
        log.error(f"Unable to create sub-folders in task {current_subfolder}")
        return ""

    try:
        lock.free()
    except Exception:
        log.error(f"Unable to remove lock file {lock_file}")
        return ""

    return str(folder_name)


def read_task(folder) -> ScanTask:
    """
    Reads the task file from the provided dictionary.
    """
    task_filename = Path(folder) / mri4all_files.TASK
    scan_task = ScanTask()

    try:
        with open(task_filename, "r") as task_file:
            scan_task = ScanTask(**json.load(task_file))
    except Exception:
        log.error(f"Unable to read task file {task_filename}")
        return None

    return scan_task


def write_task(folder, scan_task: ScanTask) -> bool:
    """
    Writes the provided task file to the dictionary.
    """
