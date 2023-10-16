from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore

from common.version import mri4all_version
import common.runtime as rt


def show_viewer():
    w = StudyViewer()
    w.exec_()


class StudyViewer(QDialog):
    def __init__(self):
        super(StudyViewer, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/studyviewer.ui", self)
        self.setWindowTitle("Study Viewer")
        # self.closeButton.clicked.connect(self.close_clicked)

    def close_clicked(self):
        self.close()
