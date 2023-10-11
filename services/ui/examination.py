from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta  # type: ignore

import common.runtime as rt
import services.ui.runtime as ui_runtime
import services.ui.about as about
import services.ui.logviewer as logviewer
import services.ui.configuration as configuration
import services.ui.systemstatus as systemstatus


class ExaminationWindow(QMainWindow):
    def __init__(self):
        super(ExaminationWindow, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/examination.ui", self)
        self.actionClose_Examination.triggered.connect(self.close_examination)
        self.viewer1Frame.setStyleSheet("background-color: #000000;")
        self.viewer2Frame.setStyleSheet("background-color: #000000;")
        self.viewer3Frame.setStyleSheet("background-color: #000000;")
        self.actionShutdown.triggered.connect(self.shutdown_clicked)
        self.actionAbout.triggered.connect(about.show_about)
        self.actionLog_Viewer.triggered.connect(logviewer.show_logviewer)
        self.actionConfiguration.triggered.connect(configuration.show_configuration)
        self.actionSystem_Status.triggered.connect(systemstatus.show_systemstatus)

        self.protocolBrowserButton.setText("")
        self.protocolBrowserButton.setIcon(qta.icon("fa5s.list"))
        self.protocolBrowserButton.setIconSize(QSize(32, 32))
        self.settingsButton.setText("")
        self.settingsButton.setIcon(qta.icon("fa5s.x-ray"))
        self.settingsButton.setIconSize(QSize(32, 32))
        self.closePatientButton.setText("")
        self.closePatientButton.setIcon(qta.icon("fa5s.sign-out-alt"))
        self.closePatientButton.setIconSize(QSize(32, 32))
        self.closePatientButton.clicked.connect(self.close_examination)

        self.startScanButton.setText("")
        self.startScanButton.setIcon(qta.icon("fa5s.play"))
        self.startScanButton.setIconSize(QSize(32, 32))

        self.queueWidget.setStyleSheet("background-color: #262C44;")

        self.update_size()

    def prepare_examination(self):
        self.statusBar().showMessage("Scanner ready", 0)

    def close_examination(self):
        ui_runtime.close_patient()

    def shutdown_clicked(self):
        ui_runtime.shutdown()

    def update_size(self):
        screen_width, screen_height = ui_runtime.get_screen_size()

        self.inlineViewerFrame.setMaximumHeight(int(screen_height * 0.5))
        self.inlineViewerFrame.setMinimumHeight(int(screen_height * 0.5))

        self.seqQueueFrame.setMaximumWidth(int(screen_width * 0.25))
        self.seqQueueFrame.setMaximumWidth(int(screen_width * 0.25))
