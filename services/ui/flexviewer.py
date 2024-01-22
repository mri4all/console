from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta

import common.runtime as rt
import common.logger as logger
from services.ui.viewerwidget import ViewerWidget
import services.ui.ui_runtime as ui_runtime


class FlexViewer(QDialog):
    def __init__(self):
        super(FlexViewer, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/flexviewer.ui", self)

        # self.setWindowFlags(Qt.WindowStaysOnTopHint)
        # self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        # self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)

        screen_width, screen_height = ui_runtime.get_screen_size()
        self.resize(int(screen_width * 0.9), int(screen_height * 0.85))
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        viewerLayout = QHBoxLayout(self.flexViewerFrame)
        viewerLayout.setContentsMargins(0, 0, 0, 0)
        self.viewer = ViewerWidget()
        self.viewer.setProperty("id", "flex")
        viewerLayout.addWidget(self.viewer)
        self.flexViewerFrame.setLayout(viewerLayout)

        self.resizeButton.setText(" Maximize")
        self.resizeButton.clicked.connect(self.clickResize)
        self.resizeButton.setIcon(qta.icon("fa5s.expand"))
        self.resizeButton.setIconSize(QSize(24, 24))

        self.closeButton.setText(" Close")
        self.closeButton.clicked.connect(self.close)
        self.closeButton.setIcon(qta.icon("fa5s.check"))
        self.closeButton.setIconSize(QSize(24, 24))

        self.maximized = False

    def closeEvent(self, event):
        ui_runtime.examination_widget.flexViewerButton.setChecked(False)
        event.accept()

    def clickResize(self):
        if self.maximized:
            screen_width, screen_height = ui_runtime.get_screen_size()
            self.resize(int(screen_width * 0.9), int(screen_height * 0.85))
            qr = self.frameGeometry()
            cp = QDesktopWidget().availableGeometry().center()
            qr.moveCenter(cp)
            self.move(qr.topLeft())
            self.resizeButton.setText(" Maximize")
            self.resizeButton.setIcon(qta.icon("fa5s.expand"))
            self.maximized = False
        else:
            screen_width, screen_height = ui_runtime.get_screen_size()
            self.resize(int(screen_width * 1), int(screen_height * 1))
            qr = self.frameGeometry()
            cp = QDesktopWidget().availableGeometry().center()
            qr.moveCenter(cp)
            self.move(qr.topLeft())
            self.resizeButton.setText(" Restore")
            self.resizeButton.setIcon(qta.icon("fa5s.compress"))
            self.maximized = True
        self.closeButton.setFocus()
