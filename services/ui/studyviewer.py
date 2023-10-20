from typing import List, Optional
import numpy as np
from pathlib import Path
from pydantic import BaseModel
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta  # type: ignore

from common.task import read_task
from common.types import (
    ScanTask,
)
import common.runtime as rt
import common.logger as logger
from services.ui import ui_runtime
from services.ui import dicomexport
from services.ui.viewerwidget import ViewerWidget

log = logger.get_logger()


def show_viewer():
    w = StudyViewer()
    w.exec_()


class ScanData(BaseModel):
    # id: str
    task: ScanTask
    # dicom: list[float]
    # rawdata: list[float]
    # metadata: ScanTask
    dir: Path


class ExamData(BaseModel):
    id: str
    acc: str
    scans: list[ScanData]
    patientName: str


class PatientData(BaseModel):
    name: str
    mrn: str
    exams: list[ExamData]


class StudyViewer(QDialog):
    examListWidget: QListWidget
    scanListWidget: QListWidget
    scanListWidget: QListWidget
    patients: List[PatientData]
    dicomTargetComboBox: QComboBox
    selected_scan: Optional[ScanData]

    def __init__(self):
        super(StudyViewer, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/studyviewer.ui", self)

        screen_width, screen_height = ui_runtime.get_screen_size()
        self.resize(int(screen_width * 0.9), int(screen_height * 0.8))
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.setWindowTitle("Exam Viewer")

        self.archive_path = Path(rt.get_base_path()) / "data/archive"
        self.exams = self.organize_scan_data_from_folders()

        self.examListWidget.addItems([e.patientName + " - " + e.acc for e in self.exams])
        self.examListWidget.currentRowChanged.connect(self.exam_selected)

        self.scanListWidget.currentRowChanged.connect(self.scan_selected)
        self.resultListWidget.currentRowChanged.connect(self.result_selected)

        self.dicomTargetComboBox.addItems(
            [t.name for t in ui_runtime.get_config().dicom_targets]
        )
        self.sendDicomsButton.clicked.connect(self.dicoms_send)
        viewerLayout = QHBoxLayout(self.viewerFrame)
        viewerLayout.setContentsMargins(0, 0, 0, 0)
        self.viewer = ViewerWidget()
        # self.viewer1.setProperty("id", "1")
        viewerLayout.addWidget(self.viewer)
        self.viewerFrame.setLayout(viewerLayout)
        self.exam_selected(0)

        self.closeButton.clicked.connect(self.close_clicked)
        self.closeButton.setProperty("type", "highlight")
        self.closeButton.setIcon(qta.icon("fa5s.check"))
        self.closeButton.setIconSize(QSize(20, 20))

    def dicoms_send(self):
        # TODO: Add mechanism for sending DICOMs in background task

        if not self.selected_scan:
            return

        try:
            dicomexport.send_dicoms(
                self.selected_scan.dir / "dicom",
                ui_runtime.get_config().dicom_targets[
                    self.dicomTargetComboBox.currentRow()
                ],
            )
        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Transfer error")
            msg.setText(f"Error transferring dicoms: \n {e}")
            msg.exec_()

    def result_selected(self, row: int):
        exam = self.exams[self.examListWidget.currentRow()]
        scan = exam.scans[self.scanListWidget.currentRow()]
        if scan.task.results:
            result_data = scan.task.results[row]
            self.viewer.view_scan(result_data.file_path, result_data.type)

    def scan_selected(self, row: int):
        self.resultListWidget.clear()
        exam = self.exams[self.examListWidget.currentRow()]
        scan = exam.scans[row]

        if not scan.task.results:
            for result in ["DICOM", "PLOT", "RAWDATA"]:
                self.resultListWidget.addItem(result)
        else:
            for result in scan.task.results:
                self.resultListWidget.addItem(result.name + " - " + result.type)
        self.resultListWidget.setCurrentRow(0)

    def exam_selected(self, index):
        self.scanListWidget.clear()
        exam = self.exams[index]
        for scan_obj in exam.scans:
            self.scanListWidget.addItem(scan_obj.task.protocol_name)
        self.scanListWidget.setCurrentRow(0)

    def organize_scan_data_from_folders(self) -> List[PatientData]:
        exams: List[ExamData] = []
        for exam_dir in self.archive_path.iterdir():
            if not exam_dir.is_dir():
                continue

            exam_id, scan_num = str(exam_dir.name).split("#")
            scan_task: ScanTask = read_task(exam_dir)
            if not scan_task:
                continue

            patient_name = (
                f"{scan_task.patient.last_name}, {scan_task.patient.first_name}"
            )
            # exam_id = scan_task["exam"]["id"] # should be same as id found in dir_name
            scan_id = scan_task.id

            # create a new patient object if not found
            # patient = next(
            #     (p for p in patients if p.mrn == scan_task.patient.mrn), None
            # )
            # if not patient:
            #     patient = PatientData(
            #         name=patient_name, mrn=scan_task.patient.mrn, exams=[]
            #     )
            #     patients.append(patient)

            # create a new exam object if not found
            exam = next((e for e in exams if e.id == exam_id), None)
            if not exam:
                exam = ExamData(id=exam_id, acc=scan_task.exam.acc, scans=[], patientName=patient_name)
                exams.append(exam)

            dicom_data = np.array([])
            rawdata = np.array([])

            scan = ScanData(
                # id=scan_id,
                # dicom=dicom_data,
                # rawdata=rawdata,
                # metadata=scan_task,
                task=scan_task,
                dir=exam_dir,
            )
            exam.scans.append(scan)
        return exams

    def close_clicked(self):
        self.close()
