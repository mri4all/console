from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore

from common.version import mri4all_version
import common.runtime as rt
import common.logger as logger
log = logger.get_logger()


def show_viewer():
    w = StudyViewer()
    w.exec_()


class StudyViewer(QDialog):
    patient_info = {"31431":{"name":"Patient A", "exams": [{"id":"ABCD"}]},"43213":{"name":"Patient B", "exams": [{"id":"DEFG"}, {"id":"SDFSDF"}]}}

    def __init__(self):
        super(StudyViewer, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/studyviewer.ui", self)
        self.setWindowTitle("Study Viewer")

        self.patientComboBox.addItems([p["name"] for p in self.patient_info.values()])
        self.patientComboBox.currentIndexChanged.connect(self.patient_selected)
        self.patient_selected(0)

    def patient_selected(self, index):
        self.examListWidget.clear()
        the_patient = self.patient_info[list(self.patient_info.keys())[index]]
        for exam in the_patient["exams"]:
            self.examListWidget.addItem(exam["id"])
        pass

    def close_clicked(self):
        self.close()
