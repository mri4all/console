from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
from typing import Tuple, Dict, List
from pathlib import Path

from common.types import PatientInformation, ExamInformation, ScanQueueEntry
import common.logger as logger

log = logger.get_logger()

import common.helper as helper
import common.queue as queue
import common.task as task
from sequences import SequenceBase

app = None
stacked_widget = None
registration_widget = None
examination_widget = None

patient_information = PatientInformation()
exam_information = ExamInformation()

scan_queue_list: List[ScanQueueEntry] = []
editor_sequence_instance = None
editor_active = False


def shutdown():
    """Shutdown the MRI4ALL console."""
    global app

    msg = QMessageBox()
    ret = msg.question(
        None,
        "Shutdown Console?",
        "Do you really want to shutdown the console?",
        msg.Yes | msg.No,
    )

    if ret == msg.Yes:
        registration_widget.clear_form()
        examination_widget.clear_examination_ui()
        if app is not None:
            app.quit()
            app = None


def register_patient():
    global exam_information

    if not queue.clear_folders():
        log.error("Failed to clear data folders. Cannot start exam.")
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Critical Error")
        msg.setText("Failed to clear data folders. Cannot start exam. Check log files for details.")
        msg.exec_()
        return

    exam_information.initialize()
    examination_widget.prepare_examination_ui()
    stacked_widget.setCurrentIndex(1)

    log.info(f"Registered patient {patient_information.get_full_name()}")
    log.info(f"Started exam {exam_information.id}")


def close_patient():
    msg = QMessageBox()
    ret = msg.question(
        None,
        "End Exam?",
        "Do you really want to close the active exam?",
        msg.Yes | msg.No,
    )

    if ret == msg.Yes:
        registration_widget.clear_form()
        stacked_widget.setCurrentIndex(0)
        examination_widget.clear_examination_ui()
        log.info(f"Closed patient {patient_information.get_full_name()}")
        patient_information.clear()
        exam_information.clear()


def get_screen_size() -> Tuple[int, int]:
    screen = QDesktopWidget().screenGeometry()
    return screen.width(), screen.height()


def update_scan_queue_list() -> bool:
    global scan_queue_list
    # TODO
    return True


def create_new_scan(requested_sequence: str) -> bool:
    global exam_information

    exam_information.scan_counter += 1

    scan_uid = helper.generate_uid()
    default_protocol_name = SequenceBase.get_sequence(requested_sequence).get_readable_name()

    default_seq_parameters = SequenceBase.get_sequence(requested_sequence).get_default_parameters()

    task_folder = task.create_task(
        exam_information.id,
        scan_uid,
        exam_information.scan_counter,
        requested_sequence,
        patient_information,
        default_seq_parameters,
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
    new_scan.folder = Path(task_folder)
    scan_queue_list.append(new_scan)

    # Check if all entries of the scan queue are up-to-date
    update_scan_queue_list()
    return True
