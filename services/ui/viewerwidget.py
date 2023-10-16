from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta  # type: ignore

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import pyqtgraph as pg
import pydicom
import numpy as np
import os


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        plt.style.use("dark_background")
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class ViewerWidget(QWidget):
    def __init__(self):
        super(ViewerWidget, self).__init__()

    series_name = ""

    def set_series_name(self, name: str):
        self.series_name = name
        self.update()

    def configure(self):
        if self.property("id") == "1":
            self.layout = QVBoxLayout(self)
            self.layout.setContentsMargins(0, 0, 0, 0)
            self.visualize_dcm_files()

        # if self.property("id") == "3":
        #     sc = MplCanvas(self, width=5, height=4, dpi=100)
        #     sc.axes.plot([0, 1, 2, 3, 4], [10, 1, 20, 3, 40])
        #     layout = QVBoxLayout(self)
        #     layout.setContentsMargins(0, 0, 0, 0)
        #     layout.addWidget(sc)

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

        # Dummy code
        if self.series_name:
            width = self.frameGeometry().width()
            height = self.frameGeometry().height()

            if width >= height:
                image_size = height
            else:
                image_size = width
            offset_x = int((width - image_size) / 2)

            dummy_image = QPixmap("/opt/mri4all/console/services/ui/assets/dummy_scan.jpg")
            painter.drawPixmap(offset_x, 0, image_size, image_size, dummy_image)
            painter.drawText(8, 8 + 28, "Scan " + self.series_name)

        painter.end()

    def visualize_dcm_files(self):
        input_path = "/vagrant/classDcm"
        lstFilesDCM = []  # create an empty list
        for dirName, subdirList, fileList in sorted(os.walk(input_path)):
            for filename in fileList:
                if ".dcm" in filename.lower():
                    lstFilesDCM.append(os.path.join(dirName,filename))

        lstFilesDCM.sort()
        ds = pydicom.dcmread(lstFilesDCM[0])

        ConstPixelDims = (len(lstFilesDCM), int(ds.Rows), int(ds.Columns))

        ArrayDicom = np.zeros(ConstPixelDims, dtype=ds.pixel_array.dtype)

        for filenameDCM in lstFilesDCM:
            ds = pydicom.dcmread(filenameDCM)
            ArrayDicom[lstFilesDCM.index(filenameDCM), :, :] = ds.pixel_array

        pg.setConfigOptions(imageAxisOrder='row-major')
        self.layout.addWidget(pg.image(ArrayDicom))