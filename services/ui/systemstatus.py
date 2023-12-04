import shutil

from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta  # type: ignore

from common.version import mri4all_version
import common.runtime as rt
import services.ui.ui_runtime as ui_runtime
from services.ui.control import (
    control_service,
    ping,
    run_device_bootsequence,
    run_device_test,
)
from common.constants import *
import common.config as config


def show_systemstatus():
    systemstatus_window = SystemStatusWindow()
    systemstatus_window.exec_()


class SystemStatusWindow(QDialog):
    def __init__(self):
        super(SystemStatusWindow, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/systemstatus.ui", self)
        self.setWindowTitle("System Status")

        # State variables
        self.first_check = True
        self.acq_running = True
        self.recon_running = True
        self.check_is_active = False

        # Connect signals to slots
        self.closeButton.clicked.connect(self.close_clicked)
        self.acqStartButton.clicked.connect(self.acqStartButton_clicked)
        self.reconStartButton.clicked.connect(self.reconStartButton_clicked)
        self.acqKillButton.clicked.connect(self.acqKillButton_clicked)
        self.reconKillButton.clicked.connect(self.reconKillButton_clicked)
        self.pingButton.clicked.connect(self.pingButton_clicked)
        self.deviceTestButton.clicked.connect(self.deviceTestButton_clicked)

        # Define widgets
        self.acqStartButton.setIcon(qta.icon("fa5s.stop"))
        self.acqStartButton.setText(" Stop")
        self.acqKillButton.setIcon(qta.icon("fa5s.times"))
        self.acqKillButton.setText(" Kill")
        self.reconStartButton.setIcon(qta.icon("fa5s.stop"))
        self.reconStartButton.setText(" Stop")
        self.reconKillButton.setIcon(qta.icon("fa5s.times"))
        self.reconKillButton.setText(" Kill")

        self.pingButton.setIcon(qta.icon("fa5s.satellite-dish"))
        self.pingButton.setText(" Ping")
        self.pingLabel.setText("")
        self.pingLabel.setFont(qta.font("fa", 16))

        self.deviceTestButton.setIcon(qta.icon("fa5s.exchange-alt"))
        self.deviceTestButton.setText(" Test")
        self.deviceTestLabel.setText("")
        self.deviceTestLabel.setFont(qta.font("fa", 16))

        self.acquisitionLabel.setText("")
        self.acquisitionLabel.setFont(qta.font("fa", 16))
        self.reconstructionLabel.setText("")
        self.reconstructionLabel.setFont(qta.font("fa", 16))

        self.deviceResetButton.setIcon(qta.icon("fa5s.power-off"))
        self.deviceResetButton.setText(" Reset")
        self.deviceResetButton.setFont(qta.font("fa", 16))
        self.deviceResetLabel.setText("")

        self.softwareLabel.setText(
            f'<span style="color: #E0A526; font-size: 22px;"><b>MRI4ALL {ui_runtime.system_information.model}</b></span><br><br>Serial Number  {ui_runtime.system_information.serial_number}<p>Software Version  {mri4all_version.get_version_string()}</p>'
        )

        diskspace = shutil.disk_usage(mri4all_paths.DATA)
        self.diskspaceBar.setValue(int(diskspace.used / diskspace.total * 100))
        self.diskspaceFreeLabel.setText(
            f"{int(diskspace.free / 1024 / 1024 / 1024)} GB available"
        )
        self.diskspaceFreeLabel.setStyleSheet("color: #424d76;")

        self.deviceTestLabel.setText(
            '<span style="color: #515669; font-size: 24px;"> '
            + chr(0xF059)
            + chr(0xA0)
            + " </span> Not tested"
        )
        self.pingLabel.setText(
            '<span style="color: #515669; font-size: 24px;"> '
            + chr(0xF059)
            + chr(0xA0)
            + " </span> Not tested"
        )

        # Check services status periodically
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_services_status)
        self.timer.start(500)

        # Ping the scanner when opening the dialog
        QTimer.singleShot(10, self.pingButton_clicked)

    def close_clicked(self):
        self.close()

    def acqStartButton_clicked(self) -> None:
        # Update UI based on the new state
        if self.get_acq_service_status():
            control_service(ServiceAction.STOP, Service.ACQ_SERVICE)
        else:
            control_service(ServiceAction.START, Service.ACQ_SERVICE)

    def reconStartButton_clicked(self) -> None:
        # Update UI based on the new state
        if self.get_recon_service_status():
            control_service(ServiceAction.STOP, Service.RECON_SERVICE)
        else:
            control_service(ServiceAction.START, Service.RECON_SERVICE)

    def acqKillButton_clicked(self) -> None:
        control_service(ServiceAction.KILL, Service.ACQ_SERVICE)

    def reconKillButton_clicked(self) -> None:
        control_service(ServiceAction.KILL, Service.RECON_SERVICE)

    def pingButton_clicked(self) -> None:
        if ping(config.get_config().scanner_ip):
            self.pingLabel.setText(
                '<span style="color: #40C1AC; font-size: 24px;"> '
                + chr(0xF058)
                + chr(0xA0)
                + " </span> Responding"
            )
        else:
            self.pingLabel.setText(
                '<span style="color: #E5554F; font-size: 24px;"> '
                + chr(0xF057)
                + chr(0xA0)
                + " </span> Not responding"
            )

    def get_acq_service_status(self) -> bool:
        return control_service(ServiceAction.STATUS, Service.ACQ_SERVICE)

    def get_recon_service_status(self):
        return control_service(ServiceAction.STATUS, Service.RECON_SERVICE)

    def check_services_status(self):
        if self.check_is_active:
            return
        self.check_is_active = True

        current_acq_status = self.get_acq_service_status()
        if current_acq_status != self.acq_running or self.first_check:
            self.acq_running = current_acq_status
            self.update_acq_ui(self.acq_running)

        current_recon_status = self.get_recon_service_status()
        if current_recon_status != self.recon_running or self.first_check:
            self.recon_running = current_recon_status
            self.update_recon_ui(self.recon_running)

        self.first_check = False
        self.check_is_active = False

    def update_acq_ui(self, status):
        if status:
            self.acqStartButton.setText(" Stop")
            self.acqStartButton.setIcon(qta.icon("fa5s.stop"))
            self.acquisitionLabel.setText(
                '<span style="color: #40C1AC; font-size: 24px;"> '
                + chr(0xF058)
                + chr(0xA0)
                + " </span> Running"
            )
        else:
            self.acqStartButton.setText(" Start")
            self.acqStartButton.setIcon(qta.icon("fa5s.play"))
            self.acquisitionLabel.setText(
                '<span style="color: #E5554F; font-size: 24px;"> '
                + chr(0xF057)
                + chr(0xA0)
                + " </span> Not running"
            )

    def update_recon_ui(self, status):
        if status:
            self.reconStartButton.setText(" Stop")
            self.reconStartButton.setIcon(qta.icon("fa5s.stop"))
            self.reconstructionLabel.setText(
                '<span style="color: #40C1AC; font-size: 24px;"> '
                + chr(0xF058)
                + chr(0xA0)
                + " </span> Running"
            )
        else:
            self.reconStartButton.setText(" Start")
            self.reconStartButton.setIcon(qta.icon("fa5s.play"))
            self.reconstructionLabel.setText(
                '<span style="color: #E5554F; font-size: 24px;"> '
                + chr(0xF057)
                + chr(0xA0)
                + " </span> Not running"
            )

    def deviceTestButton_clicked(self):
        test_result = run_device_test()
        if test_result:
            self.deviceTestLabel.setText(
                '<span style="color: #40C1AC; font-size: 24px;"> '
                + chr(0xF058)
                + chr(0xA0)
                + " </span> Success"
            )
        else:
            self.deviceTestLabel.setText(
                '<span style="color: #E5554F; font-size: 24px;"> '
                + chr(0xF057)
                + chr(0xA0)
                + " </span> Failure"
            )
