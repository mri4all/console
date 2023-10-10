from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta  # type: ignore

import common.runtime as rt
from common.version import mri4all_version
import services.ui.runtime as ui_runtime
import services.ui.about as about
import services.ui.logviewer as logviewer


class RegistrationWindow(QMainWindow):
    def __init__(self):
        super(RegistrationWindow, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/registration.ui", self)
        self.registerButton.setProperty("type", "highlight")
        self.registerButton.setIcon(qta.icon("fa5s.play"))
        self.registerButton.setText(" Start Examination")
        self.registerButton.clicked.connect(self.register_clicked)
        self.phantomButton.setText(" Phantom")
        self.phantomButton.setIcon(qta.icon("fa5s.flask"))
        self.resetButton.setIcon(qta.icon("fa5s.undo-alt"))
        self.resetButton.setText(" Reset")
        self.patientGroupBox.setProperty("type", "highlight")
        self.examGroupBox.setProperty("type", "highlight")

        fmt = self.dobEdit.calendarWidget().weekdayTextFormat(Qt.Sunday)
        fmt.setForeground(QColor("white"))
        self.dobEdit.calendarWidget().setWeekdayTextFormat(Qt.Saturday, fmt)
        self.dobEdit.calendarWidget().setWeekdayTextFormat(Qt.Sunday, fmt)

        self.versionLabel.setText(f"Version {mri4all_version.get_version_string()}")
        self.versionLabel.setProperty("type", "dimmed")

        self.actionShutdown.triggered.connect(self.shutdown_clicked)
        self.actionAbout.triggered.connect(about.show_about)
        self.actionLog_Viewer.triggered.connect(logviewer.show_logviewer)

    def register_clicked(self):
        ui_runtime.register_patient()

    def shutdown_clicked(self):
        ui_runtime.shutdown()
