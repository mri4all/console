from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta  # type: ignore

import common.runtime as rt


def show_logviewer():
    logviewer_window = LogViewerWindow()
    logviewer_window.exec_()


class LogViewerWindow(QDialog):
    def __init__(self):
        super(LogViewerWindow, self).__init__()
        uic.loadUi(f"{rt.get_base_path()}/services/ui/forms/logviewer.ui", self)
        self.closeButton.clicked.connect(self.close_clicked)
        self.refreshButton.setText(" Refresh")
        self.refreshButton.setIcon(qta.icon("fa5s.sync"))
        self.refreshButton.setProperty("type", "highlight")

    def close_clicked(self):
        self.close()
