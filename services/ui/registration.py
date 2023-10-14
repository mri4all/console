from random import random

from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta  # type: ignore

import common.runtime as rt
from common.version import mri4all_version
from common.helper import generate_uid
import services.ui.ui_runtime as ui_runtime
import services.ui.about as about
import services.ui.logviewer as logviewer
import services.ui.systemstatus as systemstatus


class RegistrationWindow(QMainWindow):
    def __init__(self):
        super(RegistrationWindow, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/registration.ui", self)
        self.registerButton.setProperty("type", "highlight")
        self.registerButton.setIcon(qta.icon("fa5s.check"))
        self.registerButton.setIconSize(QSize(20, 20))
        self.registerButton.setText(" Start Exam")
        self.registerButton.clicked.connect(self.register_clicked)
        self.phantomButton.setText(" Phantom")
        self.phantomButton.setIcon(qta.icon("fa5s.flask"))
        self.phantomButton.setIconSize(QSize(20, 20))
        self.phantomButton.clicked.connect(self.generate_phantom_data)
        self.resetButton.setIcon(qta.icon("fa5s.undo-alt"))
        self.resetButton.setIconSize(QSize(20, 20))
        self.resetButton.setText(" Reset")
        self.resetButton.clicked.connect(self.clear_form)
        self.patientGroupBox.setProperty("type", "highlight")
        self.examGroupBox.setProperty("type", "highlight")

        self.powerButton.setText("")
        self.powerButton.setProperty("type", "dimmed")
        self.powerButton.setIcon(qta.icon("fa5s.power-off", color="#424d76"))
        self.powerButton.setIconSize(QSize(32, 32))
        self.powerButton.clicked.connect(self.shutdown_clicked)

        fmt = self.dobEdit.calendarWidget().weekdayTextFormat(Qt.Sunday)
        fmt.setForeground(QColor("white"))
        self.dobEdit.calendarWidget().setWeekdayTextFormat(Qt.Saturday, fmt)
        self.dobEdit.calendarWidget().setWeekdayTextFormat(Qt.Sunday, fmt)

        self.versionLabel.setText(f"Version {mri4all_version.get_version_string()}")
        self.versionLabel.setProperty("type", "dimmed")

        self.actionShutdown.triggered.connect(self.shutdown_clicked)
        self.actionAbout.triggered.connect(about.show_about)
        self.actionLog_Viewer.triggered.connect(logviewer.show_logviewer)
        self.actionSystem_Status.triggered.connect(systemstatus.show_systemstatus)

        self.mrnEdit.installEventFilter(self)

    def eventFilter(self, source, event):
        if source == self.mrnEdit and event.type() == QEvent.MouseButtonPress:
            self.mrnEdit.setFocus(Qt.MouseFocusReason)
            self.mrnEdit.setCursorPosition(0)
            return True
        return super().eventFilter(source, event)

    def clear_form(self):
        self.lastnameEdit.setText("")
        self.firstnameEdit.setText("")
        self.mrnEdit.setText("")
        self.dobEdit.setDate(QDate(2000, 1, 1))
        self.lastnameEdit.setFocus()
        self.weightSpinBox.setValue(0)
        self.heightSpinBox.setValue(0)
        self.genderComboBox.setCurrentIndex(0)
        self.accEdit.setText("")
        self.patientPositionComboBox.setCurrentIndex(0)
        self.validationLabel.setText("")

    def generate_phantom_data(self):
        self.lastnameEdit.setText("Phantom")
        self.firstnameEdit.setText(str(round(random() * 9999)))
        self.mrnEdit.setText(generate_uid()[:8])
        self.accEdit.setText(generate_uid()[:8])
        self.dobEdit.setDate(QDate(2023, 10, 16))
        self.registerButton.setFocus()
        self.genderComboBox.setCurrentIndex(2)
        self.patientPositionComboBox.setCurrentIndex(0)
        self.weightSpinBox.setValue(20)
        self.heightSpinBox.setValue(100)
        self.validationLabel.setText("")

    def register_clicked(self):
        error = ""
        if self.lastnameEdit.text() == "" or self.firstnameEdit.text() == "":
            error = "Invalid patient name"

        if not error and self.mrnEdit.text() == "":
            error = "Medical record number (MRN) missing"

        if error:
            self.validationLabel.setText('<b><span style="color: #E5554F;">Error: </span>' + chr(0xA0) + f"{error}</b>")
        else:
            ui_runtime.patient_information.first_name = self.firstnameEdit.text()
            ui_runtime.patient_information.last_name = self.lastnameEdit.text()
            ui_runtime.patient_information.mrn = self.mrnEdit.text()
            ui_runtime.register_patient()

    def shutdown_clicked(self):
        ui_runtime.shutdown()
