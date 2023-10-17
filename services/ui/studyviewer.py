import json
import numpy as np
from pathlib import Path
from pydantic import BaseModel
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
from typing import List, Dict

from common.task import read_task
from common.types import (
    ScanTask,
)
from common.version import mri4all_version
import common.runtime as rt
import common.logger as logger
log = logger.get_logger()


def show_viewer():
    w = StudyViewer()
    w.exec_()

class ScanData(BaseModel):
    id: str
    dicom: List[float]
    rawdata: List[float]
    metadata: ScanTask

class ExamData(BaseModel):
    id: str
    scans: List[ScanData]

class PatientData(BaseModel):
    id: str
    exams: List[ExamData]

class OrganizedData(BaseModel):
    patients: List[PatientData]


class StudyViewer(QDialog):
    def __init__(self):
        super(StudyViewer, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/studyviewer.ui", self)
        self.setWindowTitle("Study Viewer")

        self.archive_path = Path('/opt/mri4all/data/archive')
        self.organized_data = self.organize_scan_data_from_folders()

        self.patientComboBox.addItems([p.id for p in self.organized_data.patients])
        self.patientComboBox.currentIndexChanged.connect(self.patient_selected)

        self.patient_selected(0)

    def patient_selected(self, index):
        self.examListWidget.clear()
        the_patient = self.organized_data.patients[index]
        for exam_obj in the_patient.exams:
            self.examListWidget.addItem(exam_obj.id)
        pass

    def organize_scan_data_from_folders(self):
        organized_data = OrganizedData(patients=[])
        for exam_dir in self.archive_path.iterdir():
            if not exam_dir.is_dir():
                continue
            
            exam_id, scan_num = str(exam_dir.name).split('#')
            scan_task = read_task(exam_dir)
            patient_id = f"{scan_task.patient.last_name}, {scan_task.patient.first_name}"
            #exam_id = scan_task["exam"]["id"] # should be same as id found in dir_name
            scan_id = scan_task.id

            # create a new patient object if not found
            patient = next((p for p in organized_data.patients if p.id == patient_id), None)
            if not patient:
                patient = PatientData(id=patient_id, exams=[])
                organized_data.patients.append(patient)
            
            # create a new exam object if not found
            exam = next((e for e in patient.exams if e.id == exam_id), None)
            if not exam:
                exam = ExamData(id=f'{scan_id}_{exam_id}', scans=[])
                patient.exams.append(exam)

            dicom_data = np.array([])
            rawdata = np.array([])

            scan = ScanData(id=scan_id, dicom=dicom_data, rawdata=rawdata, metadata=scan_task)
            exam.scans.append(scan)

        return organized_data

    def close_clicked(self):
        self.close()
