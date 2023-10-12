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
import services.ui.ui_runtime as ui_runtime


def set_MRI4ALL_style(app):
    # Define custom styles for individual widgets
    qss = """
    QWidget {
        font-size: 16px;
    }
    QPushButton {
        color: #FFFFFF;
        background-color: #FFFFFF;    
    }
    QPushButton:hover {
        color: #FFFFFF;
        background-color: #E0A526;    
    }    
    QPushButton:focus {
        color: #FFFFFF;
    }   
    QPushButton:default {
        color: #FFFFFF;
    }      
    QPushButton[type = "highlight"], QPushButton[type = "highlight"]:focus {
        color: #FFFFFF;
        background-color: rgba(224, 165, 38, 120); 
    }  
    QPushButton[type = "highlight"]:hover {
        color: #FFFFFF;
        background-color: #E0A526;    
    }  
    QPushButton[type = "dimmed"], QPushButton[type = "dimmed"]:focus {
        color: #FFFFFF;
    }  
    QPushButton[type = "dimmed"]:hover {
        background-color: rgba(66, 77, 118, 80); 
    }      
    QPushButton[type = "toolbar"], QPushButton[type = "toolbar"]:focus {
        background-color: rgba(255, 255, 255, 10); 
    }  
    QPushButton[type = "toolbar"]:hover {
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


def prepare_system() -> bool:
    # TODO: Make sure that all needed folders are available
    # TODO: Start the acquisition and reconstruction services
    # TODO: Check if the acquisition and reconstruction services are running
    return False


def shutdown_system():
    # TODO: Stop the acquisition and reconstruction services
    return True


def run():
    log.info(f"-- MRI4ALL {mri4all_version.get_version_string()} --")
    log.info("UI service started")

    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    ui_runtime.app = QApplication(sys.argv)
    ui_runtime.app.setWindowIcon(QIcon(f"{rt.get_console_path()}/services/ui/assets/mri4all_icon.png"))
    set_MRI4ALL_style(ui_runtime.app)

    if not prepare_system():
        log.error("Failed to prepare system. Unable to start UI service.")
        msg = QMessageBox()
        msg.critical(
            None,
            "Error during startup",
            "A major error occurred during preparation of the system. The scanner software cannot be started. Review the log files for details.",
        )
        sys.exit(1)

    ui_runtime.stacked_widget = QStackedWidget()
    ui_runtime.stacked_widget.setWindowTitle("MRI4ALL")
    ui_runtime.registration_widget = registration.RegistrationWindow()
    ui_runtime.stacked_widget.addWidget(ui_runtime.registration_widget)
    ui_runtime.examination_widget = examination.ExaminationWindow()
    ui_runtime.stacked_widget.addWidget(ui_runtime.examination_widget)
    ui_runtime.stacked_widget.setCurrentIndex(0)
    ui_runtime.stacked_widget.show()
    ui_runtime.stacked_widget.showFullScreen()

    return_value = ui_runtime.app.exec_()

    shutdown_system()

    log.info("UI service terminated")
    log.info("-------------")
    sys.exit(return_value)


if __name__ == "__main__":
    run()
