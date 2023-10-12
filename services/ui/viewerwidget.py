from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta  # type: ignore

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        plt.style.use("dark_background")
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class ViewerWidget(QWidget):
    def __init__(self):
        super(ViewerWidget, self).__init__()

    def configure(self):
        if self.property("id") == "3":
            sc = MplCanvas(self, width=5, height=4, dpi=100)
            sc.axes.plot([0, 1, 2, 3, 4], [10, 1, 20, 3, 40])
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(sc)

    def paintEvent(self, e):
        painter = QPainter(self)
        brush = QBrush()
        brush.setColor(QColor("black"))
        brush.setStyle(Qt.SolidPattern)
        rect = QRect(0, 0, painter.device().width(), painter.device().height())
        painter.fillRect(rect, brush)

        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QColor("#999"))
        painter.drawText(8, 8 + 10, "Viewer " + self.property("id"))
        painter.end()
