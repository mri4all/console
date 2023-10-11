from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta  # type: ignore

from common.version import mri4all_version
import common.runtime as rt


def show_systemstatus():
    systemstatus_window = SystemStatusWindow()
    systemstatus_window.exec_()


class SystemStatusWindow(QDialog):
    def __init__(self):
        super(SystemStatusWindow, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/systemstatus.ui", self)
        self.setWindowTitle("System Status")
        self.closeButton.clicked.connect(self.close_clicked)
        self.acqStartButton.setIcon(qta.icon("fa5s.stop"))
        self.acqStartButton.setText(" Stop")
        self.acqKillButton.setIcon(qta.icon("fa5s.times"))
        self.acqKillButton.setText(" Kill")
        self.reconStartButton.setIcon(qta.icon("fa5s.play"))
        self.reconStartButton.setText(" Start")
        self.reconKillButton.setIcon(qta.icon("fa5s.times"))
        self.reconKillButton.setText(" Kill")

        self.pingButton.setIcon(qta.icon("fa5s.satellite-dish"))
        self.pingButton.setText(" Ping")
        self.pingLabel.setText(
            '<span style="color: #40C1AC; font-size: 20px;"> ' + chr(0xF058) + chr(0xA0) + " </span> Responding"
        )
        self.pingLabel.setFont(qta.font("fa", 16))

        self.acquisitionLabel.setText(
            '<span style="color: #40C1AC; font-size: 20px;"> ' + chr(0xF058) + chr(0xA0) + " </span> Running"
        )
        self.acquisitionLabel.setFont(qta.font("fa", 16))
        self.reconstructionLabel.setText(
            '<span style="color: #E5554F; font-size: 20px;"> ' + chr(0xF057) + chr(0xA0) + " </span> Not running"
        )
        self.reconstructionLabel.setFont(qta.font("fa", 16))

        self.softwareLabel.setText(
            f'<span style="color: #E0A526; font-size: 20px;"><b>MRI4ALL H-1 Scanner</b></span><br><br>Serial Number  00001<p>Software Version  {mri4all_version.get_version_string()}</p>'
        )

    def close_clicked(self):
        self.close()
