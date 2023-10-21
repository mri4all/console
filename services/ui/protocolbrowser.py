from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta

import common.runtime as rt
import common.logger as logger
import services.ui.ui_runtime as ui_runtime

log = logger.get_logger()


def show_protocol_browser():
    protocol_browser_window = ProtocolBrowser()
    protocol_browser_window.exec_()


class ProtocolBrowser(QDialog):
    def __init__(self):
        super(ProtocolBrowser, self).__init__()
        uic.loadUi(
            f"{rt.get_console_path()}/services/ui/forms/protocolbrowser.ui", self
        )

        screen_width, screen_height = ui_runtime.get_screen_size()
        self.resize(int(800), int(screen_height * 0.8))
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.closeButton.setText(" Close")
        self.closeButton.setToolTip("Close browser")
        self.closeButton.setIcon(qta.icon("fa5s.times"))
        self.closeButton.setIconSize(QSize(24, 24))
        self.closeButton.clicked.connect(self.close)

        self.insertButton.setText(" Insert")
        self.insertButton.setToolTip("Insert protocol to queue")
        self.insertButton.setIcon(qta.icon("fa5s.plus"))
        self.insertButton.setIconSize(QSize(24, 24))

        self.renameButton.setText(" Rename")
        self.renameButton.setToolTip("Rename selected protocol")
        self.renameButton.setIcon(qta.icon("fa5s.pen"))
        self.renameButton.setIconSize(QSize(24, 24))

        self.deleteButton.setText(" Delete")
        self.deleteButton.setToolTip("Delete selected protocol")
        self.deleteButton.setIcon(qta.icon("fa5s.trash"))
        self.deleteButton.setIconSize(QSize(24, 24))
        # self.closeButton.clicked.connect(self.close_clicked)

    def close_clicked(self):
        self.close()
