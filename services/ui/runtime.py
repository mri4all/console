from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
from typing import Tuple

app = None
stacked_widget = None
registration_widget = None
examination_widget = None


def shutdown():
    """Shutdown the MRI4ALL console."""
    global app

    msg = QMessageBox()
    ret = msg.question(
        None,
        "Shutdown Console?",
        "Do you really want to shutdown the console?",
        msg.Yes | msg.No,
    )

    if ret == msg.Yes:
        if app is not None:
            app.quit()
            app = None


def register_patient():
    examination_widget.prepare_examination()
    stacked_widget.setCurrentIndex(1)


def close_patient():
    msg = QMessageBox()
    ret = msg.question(
        None,
        "End Examination?",
        "Do you really want to close the active examination?",
        msg.Yes | msg.No,
    )

    if ret == msg.Yes:
        stacked_widget.setCurrentIndex(0)


def get_screen_size() -> Tuple[int, int]:
    screen = QDesktopWidget().screenGeometry()
    return screen.width(), screen.height()
