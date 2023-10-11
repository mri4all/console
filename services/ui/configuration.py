from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore

from common.version import mri4all_version
import common.runtime as rt


def show_configuration():
    configuration_window = ConfigurationWindow()
    configuration_window.exec_()


class ConfigurationWindow(QDialog):
    def __init__(self):
        super(ConfigurationWindow, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/configuration.ui", self)
        self.setWindowTitle("Console Configuration")
        self.saveButton.clicked.connect(self.cancel_clicked)
        self.cancelButton.clicked.connect(self.save_clicked)

    def cancel_clicked(self):
        self.close()

    def save_clicked(self):
        self.close()
