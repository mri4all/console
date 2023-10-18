from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
from common.constants import ViewerMode
import qtawesome as qta  # type: ignore

import pyqtgraph as pg
import pydicom
import numpy as np
import os

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
    layout: QBoxLayout
    image_widget = None

    def __init__(self):
        super(ViewerWidget, self).__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

    series_name = ""

    def set_series_name(self, name: str):
        self.series_name = name
        self.update()

    def view_data(self, file_path: str, viewerMode: ViewerMode):
        # TODO- use file_path to pick values from the specified folder.
        if viewerMode == ViewerMode.DICOM:
            self.visualize_dcm_files()
        elif viewerMode == ViewerMode.PLOT:
            self.plot_array()

    def visualize_dcm_files(self, input_path="/vagrant/classDcm"):
        lstFilesDCM = []  # create an empty list
        for dirName, subdirList, fileList in sorted(os.walk(input_path)):
            for filename in fileList:
                if ".dcm" in filename.lower():
                    lstFilesDCM.append(os.path.join(dirName, filename))

        lstFilesDCM.sort()
        if len(lstFilesDCM) < 1:
            return
        ds = pydicom.dcmread(lstFilesDCM[0])

        ConstPixelDims = (len(lstFilesDCM), int(ds.Rows), int(ds.Columns))

        ArrayDicom = np.zeros(ConstPixelDims, dtype=ds.pixel_array.dtype)

        for filenameDCM in lstFilesDCM:
            ds = pydicom.dcmread(filenameDCM)
            ArrayDicom[lstFilesDCM.index(filenameDCM), :, :] = ds.pixel_array

        pg.setConfigOptions(imageAxisOrder="row-major")
        widget = pg.image(ArrayDicom)
        widget.ui.histogram.hide()
        widget.ui.roiBtn.hide()
        widget.ui.menuBtn.hide()
        if self.image_widget:
            self.layout.removeWidget(self.image_widget)
        self.layout.addWidget(widget)
        self.image_widget = widget

    def plot_array(self):
        sc = MplCanvas(self)
        y = np.random.normal(size=10)
        sc.axes.plot(y)
        self.layout.addWidget(sc)
