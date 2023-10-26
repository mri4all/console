import common.runtime as rt
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
import common.logger as logger

log = logger.get_logger()
btns = QDialogButtonBox.StandardButton


class CustomMessageBox(QDialog):
    user_clicked = None

    def __init__(self, parent, widget, buttons=btns.Ok | btns.Abort | btns.Retry):
        super(CustomMessageBox, self).__init__(parent)
        uic.loadUi(
            f"{rt.get_console_path()}/services/ui/forms/custommessagebox.ui", self
        )
        self.setWindowTitle("Configuration")

        self.buttons.setStandardButtons(buttons)
        self.innerLayout.addWidget(widget)

        self.buttons.clicked.connect(self.button_clicked)

    def button_clicked(self, button: QPushButton):
        self.user_clicked = button.text()

    def exec_(self):
        super().exec_()
        return (self.user_clicked or "None").lower()
