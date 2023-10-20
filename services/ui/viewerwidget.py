import json
import glob
import sip  # type: ignore
from pathlib import Path
from typing import Optional
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta  # type: ignore

import pyqtgraph as pg  # type: ignore
import pydicom
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import common.logger as logger
from common.types import ResultTypes, ScanTask

log = logger.get_logger()


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        plt.style.use("dark_background")
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class StaticTextItem(pg.TextItem):
    """
    Stays where you put it and ignores viewport translation/zoom.
    """

    def updateTransform(self, force=False):
        if not self.isVisible():
            return

        p = self.parentItem()
        if p is None:
            pt = QtGui.QTransform()
        else:
            pt = p.sceneTransform()

        if not force and pt == self._lastTransform:
            return
        self.setTransform(pt.inverted()[0])
        self._lastTransform = pt
        self.updateTextPos()


class ViewerWidget(QWidget):
    # layout: QBoxLayout
    widget: Optional[QWidget] = None
    viewed_scan_task: Optional[ScanTask] = None

    def __init__(self):
        super(ViewerWidget, self).__init__()
        self.setLayout(QVBoxLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.set_empty_viewer()

    def view_data(self, file_path: str, viewer_mode: ResultTypes, task):
        self.clear_view()
        if viewer_mode == "dicom":
            self.load_dicoms(file_path, task)
        elif viewer_mode == "plot":
            self.load_plot()
        else:
            self.set_empty_viewer()

    def clear_view(self):
        if self.widget:
            widget_to_delete = self.widget
            self.layout().removeWidget(self.widget)
            sip.delete(widget_to_delete)
            self.widget = None
            self.viewed_scan_task = None

    def view_scan(self, file_path: Path, task: Optional[ScanTask] = None):
        self.clear_view()
        dcm_path = file_path / "dicom"
        other_path = file_path / "other"
        if list(dcm_path.glob("**/*.dcm")):
            self.load_dicoms(str(dcm_path), task)
            return True
        elif others := list(other_path.glob("*.json")):
            self.load_plot(json.loads(others[0].read_text()))
            return False

    def load_dicoms(self, input_path, task: Optional[ScanTask] = None):
        if not input_path:
            self.set_empty_viewer()
            return

        lstFilesDCM = [str(name) for name in glob.glob(input_path + "*.dcm")]
        lstFilesDCM.sort()
        if len(lstFilesDCM) < 1:
            self.set_empty_viewer()
            return

        ds = pydicom.dcmread(lstFilesDCM[0])
        ConstPixelDims = (len(lstFilesDCM), int(ds.Rows), int(ds.Columns))
        ArrayDicom = np.zeros(ConstPixelDims, dtype=ds.pixel_array.dtype)
        for filenameDCM in lstFilesDCM:
            ds = pydicom.dcmread(filenameDCM)
            ArrayDicom[lstFilesDCM.index(filenameDCM), :, :] = ds.pixel_array

        pg.setConfigOptions(imageAxisOrder="row-major")

        self.widget = pg.ImageView()
        self.widget.setImage(ArrayDicom)

        # viewer_widget.ui.histogram.hide()
        self.widget.ui.roiBtn.hide()
        self.widget.ui.menuBtn.hide()
        self.widget.autoRange()

        if task:
            text = StaticTextItem(
                html=f"""<span style='font-size: 16px; color: #999;'>
                    {task.patient.last_name}, {task.patient.first_name}<br/>
                    {task.patient.mrn}<br/>
                    {task.protocol_name}<br/>
                    Scan {task.scan_number}<br/>                    
                    </span><br/>""",
                anchor=(0, 0),
            )
            text.setPos(0, 0)  # todo: this only works with 0,0 position
            self.widget.addItem(text)

        self.layout().addWidget(self.widget)

    def load_plot(self, array=None):
        sc = MplCanvas(self)
        if array is None:
            array = np.random.normal(size=10)
        sc.axes.plot(array)
        self.layout().addWidget(sc)
        self.widget = sc

    def set_empty_viewer(self):
        self.widget = QWidget()
        self.widget.setStyleSheet("background-color: #000;")
        self.layout().addWidget(self.widget)
