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
from services.ui import taskviewer
from common.constants import *

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
    resultListWidget: QListWidget
    patients: List[PatientData]
    dicomTargetComboBox: QComboBox
    selected_scan: Optional[ScanData]

    loaded_path = ""
    load_scan_path = ""
    load_result_type = ""
    load_scan_task = ""
    loadTimer = QTimer()

    def __init__(self):
        super(StudyViewer, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/studyviewer.ui", self)

        screen_width, screen_height = ui_runtime.get_screen_size()
        self.resize(int(screen_width * 0.9), int(screen_height * 0.85))
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.setWindowTitle("Exam Viewer")

        self.archive_path = Path(rt.get_base_path()) / "data/archive"
        self.exams = self.organize_scan_data_from_folders()

        if not self.exams:
            return

        self.examListWidget.addItems(
            [e.patientName + "   (acc " + e.acc.upper() + ")" for e in self.exams]
        )

        self.dicomTargetComboBox.addItems(
            [t.name for t in ui_runtime.get_config().dicom_targets]
        )
        self.sendDicomsButton.clicked.connect(self.dicoms_send)

        viewerLayout = QHBoxLayout(self.viewerFrame)
        viewerLayout.setContentsMargins(0, 0, 0, 0)
        self.viewer = ViewerWidget()
        self.viewer.setStyleSheet("border: 1px solid #E0A526;")
        viewerLayout.addWidget(self.viewer)
        self.viewerFrame.setLayout(viewerLayout)

        self.closeButton.clicked.connect(self.close_clicked)
        self.closeButton.setProperty("type", "highlight")
        self.closeButton.setIcon(qta.icon("fa5s.check"))
        self.closeButton.setIconSize(QSize(20, 20))
        self.closeButton.setText(" Close")

        self.selectAllPushButton.clicked.connect(self.select_all_clicked)
        self.selectNonePushButton.clicked.connect(self.select_none_clicked)
        self.definitionPushButton.clicked.connect(self.show_definition)

        label_style = "font-weight: bold; color: #E0A526; font-size: 20px; margin-left: 0px; padding-left: 0px;"
        self.scansLabel.setStyleSheet(label_style)
        self.examsLabel.setStyleSheet(label_style)
        self.resultsLabel.setStyleSheet(label_style)
        self.dicomSendLabel.setStyleSheet(label_style)
        self.viewerLabel.setStyleSheet(label_style)

        self.definitionPushButton.setIcon(qta.icon("fa5s.binoculars"))
        self.definitionPushButton.setText(" Show definition")
        self.definitionPushButton.setIconSize(QSize(20, 20))

        self.exportPushButton.setIcon(qta.icon("fa5s.save"))
        self.exportPushButton.setText(" Export")
        self.exportPushButton.setIconSize(QSize(20, 20))

        self.sendDicomsButton.setIcon(qta.icon("fa5s.paper-plane"))
        self.sendDicomsButton.setText(" Send")
        self.sendDicomsButton.setIconSize(QSize(20, 20))

        self.setStyleSheet(
            """
            QListView::item
            {
                padding: 8px;
            }
            QListView::item:selected
            {
                background-color: #E0A526;  
            }
            QListView::item:hover
            {
                background-color: rgba(224, 165, 38, 120);
            }
            """
        )
        self.loadTimer = QTimer(self)
        self.loadTimer.setInterval(100)
        self.loadTimer.timeout.connect(self.trigger_load_scan)

        self.examListWidget.currentRowChanged.connect(self.exam_selected)
        self.scanListWidget.currentRowChanged.connect(self.scan_selected)
        self.resultListWidget.currentRowChanged.connect(self.result_selected)
        self.examListWidget.setCurrentRow(0)

    def trigger_load_scan(self):
        self.loadTimer.stop()
        self.viewer.view_scan(
            self.load_scan_path, self.load_result_type, self.load_scan_task
        )

    def dicoms_send(self):
        # TODO: Add mechanism for sending DICOMs in background task
        checked_scans_numbers = []
        for i in range(self.scanListWidget.count()):
            item = self.scanListWidget.item(i)
            if item.checkState():
                checked_scans_numbers.append(i)

        if not checked_scans_numbers:
            return

        exam = self.exams[self.examListWidget.currentRow()]
        for scan_number in checked_scans_numbers:
            checked_scan = exam.scans[scan_number]
            try:
                dicomexport.send_dicoms(
                    checked_scan.dir / "dicom",
                    ui_runtime.get_config().dicom_targets[
                        self.dicomTargetComboBox.currentIndex()
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
            scan_path = str(scan.dir) + "/" + result_data.file_path
            if self.loaded_path != scan_path:
                self.load_scan_path = scan_path
                self.load_result_type = result_data.type
                self.load_scan_task = scan.task
                if not self.loadTimer.isActive():
                    self.loadTimer.start()

    def scan_selected(self, row: int):
        self.resultListWidget.clear()
        exam = self.exams[self.examListWidget.currentRow()]
        scan = exam.scans[row]

        if not scan.task.results:
            for result in ["DICOM", "PLOT", "RAWDATA"]:
                self.resultListWidget.addItem(result)
        else:
            for result in scan.task.results:
                self.resultListWidget.addItem(result.name + "  (" + result.type + ")")
        self.resultListWidget.setCurrentRow(0)

    def exam_selected(self, index: int):
        self.scanListWidget.clear()
        exam = self.exams[index]
        for scan_obj in exam.scans:
            item = QListWidgetItem(scan_obj.task.protocol_name)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.scanListWidget.addItem(item)
        self.scanListWidget.setCurrentRow(0)

    def organize_scan_data_from_folders(self) -> List[ExamData]:
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

            # create a new exam object if not found
            exam = next((e for e in exams if e.id == exam_id), None)
            if not exam:
                exam = ExamData(
                    id=exam_id,
                    acc=scan_task.exam.acc,
                    scans=[],
                    patientName=patient_name,
                )
                exams.append(exam)

            scan = ScanData(
                task=scan_task,
                dir=exam_dir,
            )
            exam.scans.append(scan)
        return exams

    def close_clicked(self):
        self.close()

    def select_all_clicked(self):
        for i in range(self.scanListWidget.count()):
            item = self.scanListWidget.item(i)
            item.setCheckState(Qt.CheckState.Checked)

    def select_none_clicked(self):
        for i in range(self.scanListWidget.count()):
            item = self.scanListWidget.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)

    def show_definition(self):
        exam = self.exams[self.examListWidget.currentRow()]
        scan = exam.scans[self.scanListWidget.currentRow()]
        taskviewer.show_taskviewer(scan.dir)
