from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore

import common.runtime as rt
import services.ui.runtime as ui_runtime
import services.ui.about as about
import services.ui.logviewer as logviewer


class ExaminationWindow(QMainWindow):
    def __init__(self):
        super(ExaminationWindow, self).__init__()
        uic.loadUi(f"{rt.get_base_path()}/services/ui/forms/examination.ui", self)
        self.actionClose_Examination.triggered.connect(self.close_examination)
        self.viewer1Frame.setStyleSheet("background-color: #000000;")
        self.viewer2Frame.setStyleSheet("background-color: #000000;")
        self.viewer3Frame.setStyleSheet("background-color: #000000;")
        self.actionShutdown.triggered.connect(self.shutdown_clicked)
        self.actionAbout.triggered.connect(about.show_about)
        self.actionLog_Viewer.triggered.connect(logviewer.show_logviewer)

    def prepare_examination(self):
        self.statusBar().showMessage("Scanner ready", 0)

    def close_examination(self):
        ui_runtime.close_patient()

    def shutdown_clicked(self):
        ui_runtime.shutdown()
