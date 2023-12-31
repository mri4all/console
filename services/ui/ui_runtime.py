import os
import datetime

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta

from typing import Tuple, List, cast
from typing import Any

from common.types import (
    PatientInformation,
    ExamInformation,
    SystemInformation,
    ScanQueueEntry,
    ScanStatesType,
    ScanTask,
)
import common.runtime as rt
import common.logger as logger

log = logger.get_logger()

import common.helper as helper
import common.queue as queue
import common.task as task
from common.constants import *
from common.config import Configuration, DicomTarget
from sequences import SequenceBase


app = None
stacked_widget = None
registration_widget = None
examination_widget = None

patient_information = PatientInformation()
exam_information = ExamInformation()
system_information = SystemInformation()

scan_queue_list: List[ScanQueueEntry] = []
editor_sequence_instance: SequenceBase = SequenceBase()
editor_active: bool = False
editor_readonly: bool = False
editor_queue_index: int = -1
editor_scantask: ScanTask = ScanTask()

status_acq_active = False
status_recon_active = False
status_last_completed_scan = ""
status_viewer_last_autoload_scan = ""

status_received_acqdata = False
status_start_time: datetime = datetime.datetime.now()
status_expected_duration_sec: int = -1
status_disable_statustimer: bool = False


def get_screen_size() -> Tuple[int, int]:
    screen = QDesktopWidget().screenGeometry()
    return screen.width(), screen.height()


def shutdown():
    """Shutdown the MRI4ALL console."""
    global app

    msg = QMessageBox()
    dialog_icon = qta.icon("fa5s.power-off", color="#E0A526")
    msg.setIconPixmap(dialog_icon.pixmap(64, 64))
    msg.setWindowTitle("Shutdown Console?")
    msg.setText("Do you really want to shutdown the console?")
    msg.setStandardButtons(QMessageBox.Yes)
    msg.addButton(QMessageBox.No)
    msg.setDefaultButton(QMessageBox.No)
    msg.setContentsMargins(12, 12, 12, 6)

    if msg.exec() == msg.Yes:
        registration_widget.clear_form()
        examination_widget.clear_examination_ui()
        if not queue.clear_folders():
            log.error("Error while clearing data folders.")
        if app is not None:
            app.quit()
            app = None


def register_patient():
    global exam_information
    global status_last_completed_scan
    global status_viewer_last_autoload_scan
    global status_start_time
    global status_expected_duration_sec
    global status_disable_statustimer
    global status_received_acqdata

    if not queue.clear_folders():
        log.error("Failed to clear data folders. Cannot start exam.")
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Critical Error")
        msg.setText(
            "Failed to clear data folders. Cannot start exam. Check log files for details."
        )
        msg.exec_()
        return

    scan_queue_list.clear()
    examination_widget.prepare_examination_ui()
    stacked_widget.setCurrentIndex(1)
    status_last_completed_scan = -1
    status_viewer_last_autoload_scan = -1

    status_received_acqdata = False
    status_start_time = datetime.datetime.now()
    status_expected_duration_sec = -1
    status_disable_statustimer = False

    log.info(f"Registered patient {patient_information.get_full_name()}")
    log.info(f"Started exam {exam_information.id}")
    rt.set_current_task_id(exam_information.id)


def close_patient():
    global patient_information
    global exam_information
    global scan_queue_list

    msg = QMessageBox()
    dialog_icon = qta.icon("fa5s.sign-out-alt", color="#E0A526")
    msg.setIconPixmap(dialog_icon.pixmap(64, 64))
    msg.setWindowTitle("End Exam?")
    msg.setText("Do you really want to close the active exam?")
    msg.setStandardButtons(QMessageBox.Yes)
    msg.addButton(QMessageBox.No)
    msg.setDefaultButton(QMessageBox.No)
    msg.setContentsMargins(12, 12, 12, 6)

    if msg.exec() == msg.Yes:
        registration_widget.clear_form()
        stacked_widget.setCurrentIndex(0)
        examination_widget.clear_examination_ui()
        log.info(f"Closed patient {patient_information.get_full_name()}")
        rt.clear_current_task_id()
        patient_information.clear()
        exam_information.clear()
        scan_queue_list.clear()

        if not queue.clear_folders():
            log.error("Error while clearing data folders.")


def is_exam_active() -> bool:
    if stacked_widget.currentIndex() == 1:
        return True
    else:
        return False

def get_scan_queue_entry(index: int) -> Any:
    global scan_queue_list

    if index < 0 or index >= len(scan_queue_list):
        return None

    return scan_queue_list[index]


def update_scan_queue_list() -> bool:
    global scan_queue_list
    global status_acq_active
    global status_recon_active
    global status_last_completed_scan

    acq_active = False
    recon_active = False

    updated_list = []

    status_last_completed_scan = ""

    for entry in scan_queue_list:
        folder = entry.folder_name
        old_state = entry.state
        current_state = ""

        # Check the current location of the task folder to determine the state
        if os.path.isdir(mri4all_paths.DATA_QUEUE_ACQ + "/" + folder):
            if os.path.isfile(
                mri4all_paths.DATA_QUEUE_ACQ
                + "/"
                + folder
                + "/"
                + mri4all_files.PREPARED
            ):
                current_state = mri4all_states.SCHEDULED_ACQ
            else:
                current_state = mri4all_states.CREATED
        if os.path.isdir(mri4all_paths.DATA_ACQ + "/" + folder):
            current_state = mri4all_states.ACQ
            acq_active = True
        if os.path.isdir(mri4all_paths.DATA_QUEUE_RECON + "/" + folder):
            current_state = mri4all_states.SCHEDULED_RECON
            recon_active = True
        if os.path.isdir(mri4all_paths.DATA_RECON + "/" + folder):
            current_state = mri4all_states.RECON
            recon_active = True
        if os.path.isdir(mri4all_paths.DATA_COMPLETE + "/" + folder):
            current_state = mri4all_states.COMPLETE
            status_last_completed_scan = entry.folder_name
            if current_state != old_state:
                # State has changed to complete. Check if the cas has results. In that
                # case, an icon will be showed in the UI
                temp_scan = task.read_task(mri4all_paths.DATA_COMPLETE + "/" + folder)
                if len(temp_scan.results) > 0:
                    entry.has_results = True
        if os.path.isdir(mri4all_paths.DATA_FAILURE + "/" + folder):
            current_state = mri4all_states.FAILURE

        # Jobs that have not been found will fall out of the list
        if current_state:
            entry.state = cast(ScanStatesType, current_state)
            updated_list.append(entry)

    scan_queue_list = updated_list
    status_acq_active = acq_active
    status_recon_active = recon_active
    return True


def create_new_scan(requested_sequence: str) -> bool:
    global system_information
    global exam_information
    global patient_information

    exam_information.scan_counter += 1
    scan_uid = helper.generate_uid()
    default_protocol_name = SequenceBase.get_sequence(
        requested_sequence
    ).get_readable_name()
    default_seq_parameters = SequenceBase.get_sequence(
        requested_sequence
    ).get_default_parameters()
    seq_description = SequenceBase.get_sequence(requested_sequence).get_description()

    task_folder = task.create_task(
        exam_information.id,
        scan_uid,
        exam_information.scan_counter,
        requested_sequence,
        patient_information,
        default_seq_parameters,
        default_protocol_name,
        system_information,
        exam_information,
    )

    if not task_folder:
        return False

    # Add entry to the scan queue
    new_scan = ScanQueueEntry()
    new_scan.id = scan_uid
    new_scan.sequence = requested_sequence
    new_scan.protocol_name = default_protocol_name
    new_scan.scan_counter = exam_information.scan_counter
    new_scan.state = "created"
    new_scan.has_results = False
    new_scan.folder_name = task_folder
    new_scan.description = seq_description
    scan_queue_list.append(new_scan)

    # Check if all entries of the scan queue are up-to-date
    update_scan_queue_list()
    return True


def duplicate_sequence(index: int) -> bool:
    template_scan_path = get_scan_location(index)
    return duplicate_sequence_dir(template_scan_path)


def duplicate_sequence_dir(template_path: str) -> bool:
    template_scan_data = task.read_task(template_path)

    if not create_new_scan(template_scan_data.sequence):
        log.error("Failed to create new scan of same sequence.")
        return False

    new_scan_path = get_scan_location(len(scan_queue_list) - 1)
    new_scan_data = task.read_task(new_scan_path)
    new_scan_data.protocol_name = template_scan_data.protocol_name
    new_scan_data.parameters = template_scan_data.parameters
    new_scan_data.adjustment = template_scan_data.adjustment
    new_scan_data.processing = template_scan_data.processing
    new_scan_data.other = template_scan_data.other

    if not task.write_task(new_scan_path, new_scan_data):
        log.error("Failed to write new scan task. Cannot create sequence")
        return False

    return True


def get_scan_location(index_queue: int) -> str:
    global scan_queue_list

    entry = get_scan_queue_entry(index_queue)
    if not entry:
        return ""

    if entry.state == "created":
        return mri4all_paths.DATA_QUEUE_ACQ + "/" + entry.folder_name
    if entry.state == "scheduled_acq":
        return mri4all_paths.DATA_QUEUE_ACQ + "/" + entry.folder_name
    if entry.state == "acq":
        return mri4all_paths.DATA_ACQ + "/" + entry.folder_name
    if entry.state == "scheduled_recon":
        return mri4all_paths.DATA_QUEUE_RECON + "/" + entry.folder_name
    if entry.state == "recon":
        return mri4all_paths.DATA_RECON + "/" + entry.folder_name
    if entry.state == "complete":
        return mri4all_paths.DATA_COMPLETE + "/" + entry.folder_name
    if entry.state == "failure":
        return mri4all_paths.DATA_FAILURE + "/" + entry.folder_name

    return ""
