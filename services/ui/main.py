import sys
import os

from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qdarktheme  # type: ignore
import qtawesome as qta  # type: ignore

import common.logger as logger
import common.runtime as rt

rt.set_service_name("ui")
log = logger.get_logger()

from common.version import mri4all_version
from services.ui import registration
from services.ui import examination
import services.ui.runtime as ui_runtime


class DemoWindow(QMainWindow):
    def __init__(self):
        super(DemoWindow, self).__init__()
        uic.loadUi(f"{rt.get_base_path()}/services/ui/forms/demo.ui", self)
        self.setWindowTitle("MRI4ALL")
        fa5_icon = qta.icon("fa5s.play")
        self.pushButton.setIcon(fa5_icon)
        self.pushButton.setProperty("type", "highlight")
        self.pushButton.clicked.connect(self.button_clicked)
        self.label.setText('This is something with a <a href="https://www.google.com">link</a>.')
        self.actionShutdown.triggered.connect(self.shutdown_clicked)

    def button_clicked(self):
        msg = QMessageBox()
        msg.setText("This is a message box This is a message box This is a message box This is a message box")
        msg.setInformativeText("This is additional information")
        msg.setDetailedText("This is additional information")
        msg.setWindowTitle("MessageBox demo")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setWindowIcon(QIcon(f"{rt.get_base_path()}/services/ui/assets/mri4all_icon.png"))
        msg.exec_()

    def shutdown_clicked(self):
        ui_runtime.shutdown()


def set_MRI4ALL_style(app):
    # Define custom styles for individual widgets
    qss = """
    QPushButton {
        color: #FFFFFF;
        background-color: #FFFFFF;    
    }
    QPushButton:hover {
        color: #FFFFFF;
        background-color: #E0A526;    
    }    
    QPushButton[type = "highlight"] {
        color: #FFFFFF;
        background-color: rgba(224, 165, 38, 120); 
    }  
    QPushButton[type = "highlight"]:hover, QPushButton[type = "highlight"]:focus {
        color: #FFFFFF;
        background-color: #E0A526;    
    }  
    QGroupBox::title {
        background-color: transparent;
        color: #E0A526;    
    }  
    QGroupBox[type = "highlight"] {
        font-size: 20px;
    }              
    QCalendarWidget QAbstractItemView
    {
        background-color: #262C44;
    }    
    QLabel[type = "dimmed"] {
        color: #424d76;
    }      
    """

    qdarktheme.setup_theme(
        corner_shape="sharp",
        custom_colors={
            "primary": "#E0A526",
            "background": "#040919",
            "border": "#FFFFFF22",
            "input.background": "#00000022",
            "statusBar.background": "#040919",
            "foreground": "#FFFFFF",
            "primary>button.hoverBackground": "#E0A52645",
            "tableSectionHeader.background": "#262C44",
            "linkVisited": "#E0A526",
        },
        additional_qss=qss,
    )


def run():
    log.info(f"-- MRI4ALL {mri4all_version.get_version_string()} --")
    log.info("UI service started")

    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    ui_runtime.app = QApplication(sys.argv)
    ui_runtime.app.setWindowIcon(QIcon(f"{rt.get_base_path()}/services/ui/assets/mri4all_icon.png"))
    set_MRI4ALL_style(ui_runtime.app)

    ui_runtime.stacked_widget = QStackedWidget()
    ui_runtime.stacked_widget.setWindowTitle("MRI4ALL")
    ui_runtime.registration_widget = registration.RegistrationWindow()
    ui_runtime.stacked_widget.addWidget(ui_runtime.registration_widget)
    ui_runtime.examination_widget = examination.ExaminationWindow()
    ui_runtime.stacked_widget.addWidget(ui_runtime.examination_widget)
    ui_runtime.stacked_widget.showFullScreen()

    return_value = ui_runtime.app.exec_()

    log.info("UI service terminated")
    log.info("-------------")
    sys.exit(return_value)


if __name__ == "__main__":
    run()
