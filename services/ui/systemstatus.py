from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore

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
        # self.versionLabel.setText(
        #     f'<html><head/><body><p><span style="font-weight:600;">MRI4ALL Console</span></p><p>The Open-Source MRI Software</p><p>Version {mri4all_version.get_version_string()}</p></body></html>'
        # )
        self.closeButton.clicked.connect(self.close_clicked)

    def close_clicked(self):
        self.close()
