from typing import List, Optional
import os
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
import common.config as config

log = logger.get_logger()


def show_viewer():
    w = StudyViewer()
    w.exec_()


class ScanData(BaseModel):
    task: ScanTask
    dir: Path


class ExamData(BaseModel):
    id: str
    acc: str
    scans: list[ScanData]
    patientName: str
    examTime: str


class PatientData(BaseModel):
    name: str
    mrn: str
    exams: list[ExamData]


class StudyViewer(QDialog):
    scanListWidget: QListWidget
    resultListWidget: QListWidget
    patients: List[PatientData]
    dicomTargetComboBox: QComboBox
    selected_scan: Optional[ScanData]

    # Caching and timer for preventing loading multiple studies
    # when updating the list widgets
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

        self.setWindowTitle("Study Viewer")

        self.exams = self.organize_scan_data_from_folders(Path(mri4all_paths.DATA_COMPLETE))
        self.exams += self.organize_scan_data_from_folders(Path(mri4all_paths.DATA_ARCHIVE))

        if not self.exams:
            return

        self.examTableWidget.setColumnHidden(0, True)
        self.examTableWidget.horizontalHeader().setStretchLastSection(True)
        self.examTableWidget.verticalHeader().setDefaultSectionSize(36)

        # for e in self.exams:
        for idx, e in enumerate(self.exams):
            rowPosition = self.examTableWidget.rowCount()
            self.examTableWidget.insertRow(rowPosition)

            self.examTableWidget.setItem(rowPosition, 0, QTableWidgetItem(str(idx)))
            self.examTableWidget.setItem(rowPosition, 1, QTableWidgetItem(e.patientName))
            item = QTableWidgetItem(e.acc.upper())
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.examTableWidget.setItem(rowPosition, 2, item)

            item = QTableWidgetItem(e.examTime)
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.examTableWidget.setItem(rowPosition, 3, item)

        self.examTableWidget.sortItems(3, Qt.DescendingOrder)

        self.dicomTargetComboBox.addItems([t.name for t in config.get_config().dicom_targets])
        self.sendDicomsButton.clicked.connect(self.dicoms_send)

        viewerLayout = QHBoxLayout(self.viewerFrame)
        viewerLayout.setContentsMargins(0, 0, 0, 0)
        self.viewer = ViewerWidget()
        self.viewerFrame.setStyleSheet("QFrame#viewerFrame { border: 1px solid #262C44; }")
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
        self.cloneScanButton.clicked.connect(self.clone_scan_clicked)

        if not ui_runtime.is_exam_active():
            self.cloneScanButton.setEnabled(False)
            self.loadToViewerButton.setEnabled(False)

        label_style = "font-weight: bold; color: #E0A526; font-size: 20px; margin-left: 0px; padding-left: 0px;"
        self.scansLabel.setStyleSheet(label_style)
        self.examsLabel.setStyleSheet(label_style)
        self.resultsLabel.setStyleSheet(label_style)
        self.dicomSendLabel.setStyleSheet(label_style)
        self.viewerLabel.setStyleSheet(label_style)

        self.definitionPushButton.setIcon(qta.icon("fa5s.binoculars"))
        self.definitionPushButton.setText(" Definition")
        self.definitionPushButton.setIconSize(QSize(20, 20))

        self.exportPushButton.setIcon(qta.icon("fa5s.save"))
        self.exportPushButton.setText(" Export")
        self.exportPushButton.setIconSize(QSize(20, 20))

        self.loadToViewerButton.setText(" View in")
        self.loadToViewerButton.setIcon(qta.icon("fa5s.image"))
        self.loadToViewerButton.setIconSize(QSize(20, 20))

        self.cloneScanButton.setText(" Clone")
        self.cloneScanButton.setIcon(qta.icon("fa5s.clone"))
        self.cloneScanButton.setIconSize(QSize(20, 20))

        loadToViewerMenu = QMenu()
        loadToViewerMenu.addAction("Viewer 1", self.loadtoviewer1_clicked)
        loadToViewerMenu.addAction("Viewer 2", self.loadtoviewer2_clicked)
        loadToViewerMenu.addAction("Viewer 3", self.loadtoviewer3_clicked)
        loadToViewerMenu.addAction("Flex Viewer", self.loadtoflexviewer_clicked)
        self.loadToViewerButton.setMenu(loadToViewerMenu)
        self.loadToViewerButton.setStyleSheet(
            """QPushButton::menu-indicator {
                                                image: none;
                                                subcontrol-position: right top;
                                                subcontrol-origin: padding;
                                                width: 0px;
                                            }                                        
            """
        )

        self.sendDicomsButton.setIcon(qta.icon("fa5s.paper-plane"))
        self.sendDicomsButton.setText(" Send")
        self.sendDicomsButton.setIconSize(QSize(20, 20))

        self.setStyleSheet(
            """
            QListView, QTableView {
                background-color: #0C1123;
            }
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
            QTableView::item:selected
            {
                background-color: #E0A526;  
            }
            QTableView::item:hover
            {
                background-color: rgba(224, 165, 38, 120);
            }    
            QTableView QHeaderView::section {	    
                color: #FFFFFF;
                padding: 6px;
            }            
            """
        )
        self.loadTimer = QTimer(self)
        self.loadTimer.setInterval(100)
        self.loadTimer.timeout.connect(self.trigger_load_scan)

        self.examTableWidget.currentItemChanged.connect(self.exam_selected)
        self.scanListWidget.currentRowChanged.connect(self.scan_selected)
        self.resultListWidget.currentRowChanged.connect(self.result_selected)
        self.examTableWidget.setCurrentCell(0, 0)

        QTimer.singleShot(1, self.update_control_size)

    def update_control_size(self):
        table_width = self.examTableWidget.width()
        self.examTableWidget.horizontalHeader().resizeSection(1, int(table_width * 0.5))
        self.examTableWidget.horizontalHeader().resizeSection(2, int(table_width * 0.2))

    def get_selected_exam_index(self):
        index = self.examTableWidget.currentRow()
        if index < 0:
            return 0
        return int(self.examTableWidget.item(index, 0).text())

    def trigger_load_scan(self):
        self.loadTimer.stop()
        self.viewer.view_data(self.load_scan_path, self.load_result_type, self.load_scan_task)

    def dicoms_send(self):
        # TODO: Add mechanism for sending DICOMs in background task
        checked_scans_numbers = []
        for i in range(self.scanListWidget.count()):
            item = self.scanListWidget.item(i)
            if item.checkState():
                checked_scans_numbers.append(i)

        if not checked_scans_numbers:
            return

        exam = self.exams[self.get_selected_exam_index()]
        for scan_number in checked_scans_numbers:
            checked_scan = exam.scans[scan_number]
            try:
                dicomexport.send_dicoms(
                    checked_scan.dir / "dicom",
                    config.get_config().dicom_targets[self.dicomTargetComboBox.currentIndex()],
                )
            except Exception as e:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("Transfer error")
                msg.setText(f"Error transferring dicoms: \n {e}")
                msg.exec_()

    def result_selected(self, row: int):
        exam_index = self.get_selected_exam_index()
        exam = self.exams[exam_index]
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
        exam_index = self.get_selected_exam_index()
        exam = self.exams[exam_index]
        scan = exam.scans[row]

        if not scan.task.results:
            self.viewer.clear_view()
        else:
            for result in scan.task.results:
                self.resultListWidget.addItem(result.name + "  (" + result.type.upper() + ")")
        self.resultListWidget.setCurrentRow(0)

    def exam_selected(self):
        index = self.get_selected_exam_index()
        if index < 0:
            return

        self.scanListWidget.clear()
        exam = self.exams[index]
        for scan_obj in exam.scans:
            failed_notice = ""
            if scan_obj.task.journal.failed_at:
                failed_notice = "  [failed]"
            item = QListWidgetItem(f"{scan_obj.task.scan_number}:  " + scan_obj.task.protocol_name + failed_notice)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.scanListWidget.addItem(item)
        self.scanListWidget.setCurrentRow(0)

    def organize_scan_data_from_folders(self, folder: Path) -> List[ExamData]:
        exams: List[ExamData] = []

        # Sort by creation time
        folders = sorted(folder.iterdir(), key=os.path.getmtime, reverse=True)
        for exam_dir in folders:
            if not exam_dir.is_dir():
                continue

            exam_id, scan_num = str(exam_dir.name).split("#")
            scan_task: ScanTask = read_task(exam_dir)
            if not scan_task:
                continue

            patient_name = f"{scan_task.patient.last_name}, {scan_task.patient.first_name}"

            # create a new exam object if not found
            exam = next((e for e in exams if e.id == exam_id), None)
            if not exam:
                exam_date, exam_time = scan_task.exam.registration_time.split("T")
                exam_time = exam_time.split(".")[0]
                exam = ExamData(
                    id=exam_id,
                    acc=scan_task.exam.acc,
                    scans=[],
                    patientName=patient_name,
                    examTime=exam_date + "  " + exam_time,
                )
                exams.append(exam)

            scan = ScanData(
                task=scan_task,
                dir=exam_dir,
            )
            exam.scans.append(scan)

        # After all folders have been searched, order the scans within each exam chronologically
        for items in exams:
            items.scans = sorted(items.scans, key=lambda x: x.task.scan_number)

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
        exam = self.exams[self.get_selected_exam_index()]
        scan = exam.scans[self.scanListWidget.currentRow()]
        taskviewer.show_taskviewer(scan.dir)

    def loadtoviewer1_clicked(self):
        self.loadtoviewer(1)

    def loadtoviewer2_clicked(self):
        self.loadtoviewer(2)

    def loadtoviewer3_clicked(self):
        self.loadtoviewer(3)

    def loadtoflexviewer_clicked(self):
        self.loadtoviewer(4)

    def loadtoviewer(self, viewer_id):
        exam = self.exams[self.get_selected_exam_index()]
        scan = exam.scans[self.scanListWidget.currentRow()]

        if scan.task.results:
            row = self.resultListWidget.currentRow()
            result_data = scan.task.results[row]
            scan_path = str(scan.dir) + "/" + result_data.file_path

            if viewer_id == 1:
                ui_runtime.examination_widget.viewer1.view_data(scan_path, result_data.type, scan.task)
            if viewer_id == 2:
                ui_runtime.examination_widget.viewer2.view_data(scan_path, result_data.type, scan.task)
            if viewer_id == 3:
                ui_runtime.examination_widget.viewer3.view_data(scan_path, result_data.type, scan.task)
            if viewer_id == 4:
                ui_runtime.examination_widget.flexViewer.view_data(scan_path, result_data.type, scan.task)

    def clone_scan_clicked(self):
        exam = self.exams[self.get_selected_exam_index()]
        scan = exam.scans[self.scanListWidget.currentRow()]
        if not ui_runtime.duplicate_sequence_dir(scan.dir):
            # TODO: Error handling
            pass
