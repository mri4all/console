import numpy as np
from pathlib import Path
from pydantic import BaseModel
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore

from common.task import read_task
from common.types import (
    ScanTask,
)
import common.runtime as rt
import common.logger as logger

log = logger.get_logger()


def show_viewer():
    w = StudyViewer()
    w.exec_()


class ScanData(BaseModel):
    id: str
    dicom: list[float]
    rawdata: list[float]
    metadata: ScanTask


class ExamData(BaseModel):
    id: str
    scans: list[ScanData]


class PatientData(BaseModel):
    id: str
    exams: list[ExamData]


class StudyViewer(QDialog):
    patientComboBox: QComboBox
    examListWidget: QListWidget
    scanListWidget: QListWidget

    def __init__(self):
        super(StudyViewer, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/studyviewer.ui", self)
        self.setWindowTitle("Study Viewer")

        self.archive_path = Path("/opt/mri4all/data/archive")
        self.patients = self.organize_scan_data_from_folders()

        self.patientComboBox.addItems([p.id for p in self.patients])
        self.patientComboBox.currentIndexChanged.connect(self.patient_selected)

        self.examListWidget.currentRowChanged.connect(self.exam_selected)
        self.scanListWidget.currentRowChanged.connect(self.scan_selected)

        self.patient_selected(0)

    def scan_selected(self, row):
        pass

    def exam_selected(self, row):
        self.scanListWidget.clear()
        the_patient = self.patients[self.patientComboBox.currentIndex()]
        the_exam = the_patient.exams[row]

        for scan_obj in the_exam.scans:
            self.scanListWidget.addItem(scan_obj.metadata.protocol_name)
        self.scanListWidget.setCurrentRow(0)
        self.scan_selected(0)

    def patient_selected(self, index):
        self.examListWidget.clear()
        the_patient = self.patients[index]
        for exam_obj in the_patient.exams:
            self.examListWidget.addItem(exam_obj.id)
        pass

    def organize_scan_data_from_folders(self):
        patients = []
        for exam_dir in self.archive_path.iterdir():
            if not exam_dir.is_dir():
                continue

            exam_id, scan_num = str(exam_dir.name).split("#")
            scan_task = read_task(exam_dir)
            patient_id = (
                f"{scan_task.patient.last_name}, {scan_task.patient.first_name}"
            )
            # exam_id = scan_task["exam"]["id"] # should be same as id found in dir_name
            scan_id = scan_task.id

            # create a new patient object if not found
            patient = next((p for p in patients if p.id == patient_id), None)
            if not patient:
                patient = PatientData(id=patient_id, exams=[])
                patients.append(patient)

            # create a new exam object if not found
            exam = next((e for e in patient.exams if e.id == exam_id), None)
            if not exam:
                exam = ExamData(id=f"{scan_id}_{exam_id}", scans=[])
                patient.exams.append(exam)

            dicom_data = np.array([])
            rawdata = np.array([])

            scan = ScanData(
                id=scan_id, dicom=dicom_data, rawdata=rawdata, metadata=scan_task
            )
            exam.scans.append(scan)

        return patients

    def close_clicked(self):
        self.close()
