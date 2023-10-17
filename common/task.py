import json
import os
from pathlib import Path
from typing import Any

import common.logger as logger

log = logger.get_logger()

import common.helper as helper
from common.constants import *
from common.types import (
    ScanTask,
    ExamInformation,
    PatientInformation,
    SystemInformation,
)


def create_task(
    exam_id: str,
    scan_id: str,
    scan_counter: int,
    sequence: str,
    patient_information: PatientInformation,
    default_seq_parameters: dict,
    default_protocol_name: str,
    system_information: SystemInformation,
    exam_information: ExamInformation,
) -> str:
    """
    Creates a new scan task for the given exam ID. Returns empty string on failure.
    """
    # New jobs are always created in the ACQ folder. Tasks won't be touched by the acq service until
    # a file with name PREPARED is found in the folder.
    scan_name = str(exam_id + mri4all_defs.SEP + f"scan_{scan_counter}")
    folder_name = Path(mri4all_paths.DATA_QUEUE_ACQ) / scan_name
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
    scan_task.protocol_name = default_protocol_name
    scan_task.system = system_information
    scan_task.exam = exam_information
    scan_task.patient = patient_information
    scan_task.parameters = default_seq_parameters
    scan_task.other = {}

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

    return str(scan_name)


def read_task(folder) -> Any:
    """
    Reads the task file from the provided dictionary.
    """
    task_filename = Path(folder) / mri4all_files.TASK
    lock_file = Path(folder) / mri4all_files.LOCK
    scan_task = ScanTask()

    # Check if lock file exists (should not happen)
    if os.path.isfile(lock_file):
        log.warning(
            f"Lock file {lock_file} exists. Task might be open in other service."
        )

    try:
        with open(task_filename, "r") as task_file:
            scan_task = ScanTask(**json.load(task_file))
    except Exception:
        log.error(f"Unable to read task file {task_filename}")
        return None

    return scan_task


def write_task(folder, scan_task: ScanTask) -> bool:
    """
    Writes the provided scan task into the task file in JSON format.
    """
    task_filename = Path(folder) / mri4all_files.TASK

    lock_file = Path(folder) / mri4all_files.LOCK
    # Create lock file in the folder to prevent other services from accessing it
    try:
        lock = helper.FileLock(lock_file)
    except:
        # Can't create lock file, so something must be seriously wrong
        log.error(f"Unable to create lock file {lock_file}")
        return False

    try:
        with open(task_filename, "w") as task_file:
            json.dump(scan_task.dict(), task_file, indent=4)
    except Exception:
        log.error(f"Unable to write task file {task_filename}")
        return False

    try:
        lock.free()
    except Exception:
        log.error(f"Unable to remove lock file {lock_file}")
        return False

    return True


def set_task_state(folder: str, state: str, value: bool) -> bool:
    """
    Sets the state of the task to the provided value. Returns True on success.
    """
    # Check if valid state is provided
    if state == mri4all_files.PREPARED:
        state_file = Path(folder) / mri4all_files.PREPARED
    elif state == mri4all_files.EDITING:
        state_file = Path(folder) / mri4all_files.EDITING
    else:
        log.error(f"Unknown state {state}.")
        return False

    if not Path(folder).is_dir():
        log.error(f"Task folder {folder} does not exist.")
        return False

    lock_file = Path(folder) / mri4all_files.LOCK
    if lock_file.is_file():
        log.error(f"Task is locked. Unable to set state.")
        return False

    # Create lock file in the folder to prevent other services from accessing it
    try:
        lock = helper.FileLock(lock_file)
    except:
        # Can't create lock file, so something must be seriously wrong
        log.error(f"Unable to create lock file {lock_file}")
        return False

    # Create or remove the state file, depending on the value
    if value == True:
        if not state_file.is_file():
            try:
                open(state_file, "w").close()
            except Exception:
                log.error(f"Unable to create state file {state_file}")
                return False
    else:
        if state_file.is_file():
            try:
                os.remove(state_file)
            except Exception:
                log.error(f"Unable to remove state file {state_file}")
                return False

    try:
        lock.free()
    except Exception:
        log.error(f"Unable to remove lock file {lock_file}")
        return False

    return True
