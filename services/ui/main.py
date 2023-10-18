import sys
import traceback

sys.path.append("/opt/mri4all/console/external/")
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qdarktheme  # type: ignore

import common.logger as logger
import common.runtime as rt
from common.constants import ServiceAction

rt.set_service_name("ui")
log = logger.get_logger()

from common.version import mri4all_version
from services.ui import registration
from services.ui import examination
from services.ui.control import control_services
import services.ui.ui_runtime as ui_runtime
import common.queue as queue


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
    QMenu {
        border: 1px solid rgba(38, 44, 68, 255);
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
    # Make sure that all needed folders are available
    if not queue.check_and_create_folders():
        log.error("Failed to create data folders. Unable to start UI service.")
        return False

    if not queue.clear_folders():
        log.error("Clearing data folders failed. Unable to start UI service.")
        return False

    # TODO: If disk space is low, clear old cases from the archive folder
    control_services(ServiceAction.START)
    # TODO: Check if the acquisition and reconstruction services are running

    ui_runtime.load_config()
    ui_runtime.system_information.name = "dev-system1"
    ui_runtime.system_information.model = "Zeugmatron Z1"
    ui_runtime.system_information.serial_number = "000001"
    ui_runtime.system_information.software_version = (
        mri4all_version.get_version_string()
    )

    return True


def shutdown_system():
    control_services(ServiceAction.STOP)


def run():
    log.info(f"-- MRI4ALL {mri4all_version.get_version_string()} --")
    log.info("UI service started")

    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    ui_runtime.app = QApplication(sys.argv)
    ui_runtime.app.setWindowIcon(
        QIcon(f"{rt.get_console_path()}/services/ui/assets/mri4all_icon.png")
    )
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


def excepthook(exc_type, exc_value, exc_tb):
    # TODO: maybe implement this instead
    # https://timlehr.com/2018/01/python-exception-hooks-with-qt-message-box/
    # This may not work well with exceptions on other threads.
    if issubclass(exc_type, KeyboardInterrupt):
        # ignore keyboard interrupt to support console applications
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        shutdown_system()
        sys.exit()

    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    log.exception(tb)
    tb = "An unexpected error occured:\n{}".format(tb)
    errorbox = QMessageBox()
    errorbox.setText(tb)
    errorbox.exec_()


sys.excepthook = excepthook

if __name__ == "__main__":
    run()
