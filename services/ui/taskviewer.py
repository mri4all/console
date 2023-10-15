from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta  # type: ignore

import common.runtime as rt
import common.logger as logger
from common.constants import *
import services.ui.ui_runtime as ui_runtime

log = logger.get_logger()


def show_taskviewer(task_folder: str):
    taskviewer_window = TaskViewerWindow()
    taskviewer_window.load_taskfile(task_folder)
    taskviewer_window.exec_()


class TaskViewerWindow(QDialog):
    def __init__(self):
        super(TaskViewerWindow, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/taskviewer.ui", self)

        screen_width, screen_height = ui_runtime.get_screen_size()
        self.resize(int(screen_width * 0.8), int(screen_height * 0.8))
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.closeButton.setProperty("type", "highlight")
        self.closeButton.clicked.connect(self.close_clicked)
        self.closeButton.setFocus()
        self.scantaskEdit.setStyleSheet("color: rgba(255, 255, 255, 220);")
        self.fileLocationEdit.setStyleSheet("color: rgba(255, 255, 255, 220);")

        log_font = QFont("Monospace")
        log_font.setStyleHint(QFont.TypeWriter)
        self.scantaskEdit.setFont(log_font)

    def close_clicked(self):
        self.close()

    def load_taskfile(self, folder):
        task_filename = f"{folder}/" + mri4all_files.TASK
        file_content = ""
        try:
            with open(task_filename, "r") as file:
                for line in file.readlines():
                    file_content += line
        except:
            log.error(f"Unable to load task file {task_filename}")
            file_content = "- Unable to load scan task definition -"

        self.scantaskEdit.setPlainText(file_content)
        self.fileLocationEdit.setText(task_filename)
