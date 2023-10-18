import json
from pathlib import Path
from typing import Optional
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
import common.logger as logger

log = logger.get_logger()


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        plt.style.use("dark_background")
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class ViewerWidget(QWidget):
    # layout: QBoxLayout
    widget: Optional[QWidget] = None

    def __init__(self):
        super(ViewerWidget, self).__init__()
        self.setLayout(QVBoxLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

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

    def clear_view(self):
        if self.widget:
            self.layout().removeWidget(self.widget)
            self.widget.deleteLater()
            self.widget = None

    def view_scan(self, file_path: str):
        self.clear_view()
        dcm_path = Path(file_path) / "dicom"
        other_path = Path(file_path) / "other"
        if list(dcm_path.glob("**/*.dcm")):
            self.visualize_dcm_files(str(dcm_path))
            return True
        elif others := list(other_path.glob("*.json")):
            self.plot_array(json.loads(others[0].read_text()))
            return False

    def visualize_dcm_files(self, input_path="/vagrant/classDcm"):
        lstFilesDCM = [str(p) for p in Path(input_path).glob("**/*.dcm")]
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

        text = pg.LabelItem("Patient ID", color=(255, 255, 255), bold=True, size="18px")
        text.setPos(-30, -10)
        widget.addItem(text)

        # Another option to display text
        # label = QLabel("Patient ID")
        # label.move(0, 0)
        # label.setStyleSheet("background-color: #000;")
        # self.layout.addWidget(label)

        self.layout().addWidget(widget)
        self.widget = widget

    def plot_array(self, array=None):
        sc = MplCanvas(self)
        if array is None:
            array = np.random.normal(size=10)
        sc.axes.plot(array)
        self.layout().addWidget(sc)
        self.widget = sc
