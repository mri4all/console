from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta  # type: ignore

import common.runtime as rt
import common.logger as logger
import services.ui.ui_runtime as ui_runtime

log = logger.get_logger()


def show_logviewer():
    logviewer_window = LogViewerWindow()
    logviewer_window.exec_()


class LogViewerWindow(QDialog):
    def __init__(self):
        super(LogViewerWindow, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/logviewer.ui", self)

        screen_width, screen_height = ui_runtime.get_screen_size()
        self.resize(int(screen_width * 0.8), int(screen_height * 0.8))
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.closeButton.setProperty("type", "highlight")
        self.closeButton.clicked.connect(self.close_clicked)
        self.closeButton.setFocus()
        self.refreshButton.setText("")
        self.refreshButton.setIcon(qta.icon("fa5s.sync"))
        self.refreshButton.setIconSize(QSize(24, 24))
        self.refreshButton.clicked.connect(self.update_log)
        self.logEdit.setStyleSheet("color: rgba(255, 255, 255, 220);")
        self.logfileBox.currentIndexChanged.connect(self.update_log)

        log_font = QFont("Monospace")
        log_font.setStyleHint(QFont.TypeWriter)
        self.logEdit.setFont(log_font)

        QTimer.singleShot(10, self.update_log)

    def close_clicked(self):
        self.close()

    def update_log(self):
        selected_log = "acq"
        if self.logfileBox.currentText() == "Reconstruction Service":
            selected_log = "recon"
        if self.logfileBox.currentText() == "UI Service":
            selected_log = "ui"

        log_filename = f"{rt.get_base_path()}/logs/{selected_log}.log"
        log_content = []

        try:
            with open(log_filename, "r") as file:
                for line in file.readlines():
                    log_line = line
                    if "| ERR |" in line:
                        log_line = f"<span style='color: #E5554F;'>{line}</span>"
                    if "| WRN |" in line:
                        log_line = f"<span style='color: #E0A526;'>{line}</span>"
                    if "| DBG |" in line:
                        log_line = f"<span style='color: #489FDF;'>{line}</span>"

                    log_content.append(log_line)
        except:
            log.exception("Unable to load log")
            log_content = "- Unable to load log -"

        self.logEdit.setHtml("<br>".join(log_content))
        self.logEdit.verticalScrollBar().setValue(
            self.logEdit.verticalScrollBar().maximum()
        )
