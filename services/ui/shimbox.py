from pydantic import BaseModel
import common.runtime as rt
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
import common.logger as logger
from services.ui.viewerwidget import MplCanvas

log = logger.get_logger()
btns = QDialogButtonBox.StandardButton


class currentValues(BaseModel):
    x: float = 0
    y: float = 0
    z: float = 0


class ShimBox(QDialog):
    user_clicked = None
    current_values = currentValues()

    def __init__(self, parent, buttons=btns.Ok):
        super(ShimBox, self).__init__(parent)
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/shimbox.ui", self)
        self.setWindowTitle("Shimming Configuration")

        self.buttons.setStandardButtons(buttons)

        sc = MplCanvas(width=7, height=4)
        self.innerLayout.addWidget(sc)
        self.canvas = sc
        self.buttons.clicked.connect(self.button_clicked)

        self.xBar.valueChanged.connect(self.change_x)
        self.yBar.valueChanged.connect(self.change_y)
        self.zBar.valueChanged.connect(self.change_z)
        self.change_x(0)
        self.change_y(0)
        self.change_z(0)
        self.canvas.axes.plot([], "ro")

    @pyqtSlot(object)
    def new_data(self, data):
        self.innerLayout.removeWidget(self.canvas)
        self.canvas = MplCanvas(width=7, height=4)
        self.innerLayout.addWidget(self.canvas)
        # self.canvas = sc
        # self.canvas.axes.clear()
        self.canvas.axes.plot(data)
        # self.canvas.axes.draw()

    def button_clicked(self, button: QPushButton):
        self.user_clicked = button.text()

    def exec_(self):
        super().exec_()
        return (self.user_clicked or "None").lower()

    def change_x(self, value: int):
        self.current_values.x = value
        self.xLabel.setText(str(value))

    def change_y(self, value: int):
        self.current_values.y = value
        self.yLabel.setText(str(value))

    def change_z(self, value: int):
        self.current_values.z = value
        self.zLabel.setText(str(value))
