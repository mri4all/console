import glob
import sip  # type: ignore
import pickle
from pathlib import Path
from typing import Literal, Optional
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore

import pyqtgraph as pg  # type: ignore
import pydicom
import numpy as np
from PyQt5 import QtGui

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import common.logger as logger
from common.types import ResultTypes, ScanTask, TimeSeriesResult

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

    def clear_view(self):
        if self.widget:
            widget_to_delete = self.widget
            self.layout().removeWidget(self.widget)
            sip.delete(widget_to_delete)
            self.widget = None
            self.viewed_scan_task = None

    def set_empty_viewer(self):
        self.widget = QWidget()
        self.widget.setStyleSheet("background-color: #000;")
        self.layout().addWidget(self.widget)

    def view_data(self, file_path: str, viewer_mode: ResultTypes, task) -> bool:
        """
        Used to load results into the viewer for the inline widgets
        """
        self.clear_view()
        if viewer_mode == "dicom":
            self.load_dicoms(file_path, task)
            return True
        elif viewer_mode == "plot":
            self.load_pickled_plot(file_path, task)
            # self.load_plot()
            return True
        else:
            self.set_empty_viewer()
            return False

    def view_scan(
        self,
        file_path: str,
        type: Literal["dicom", "plot", "raw"],
        task: Optional[ScanTask],
    ) -> bool:
        """
        Used to load results into the viewer from the study viewer
        """
        # TODO: Harmonize with function view_data!
        self.clear_view()
        if type == "dicom":
            self.load_dicoms(file_path, task)
            return True
        elif type == "plot":
            self.load_pickled_plot(file_path, task)
            return True
        elif type == "other":
            self.load_pickled_plot(file_path, task)
            return True
        else:
            self.set_empty_viewer()
            return False

    def load_dicoms(self, input_path, task: Optional[ScanTask] = None):
        if not input_path:
            self.set_empty_viewer()
            return

        lstFilesDCM = None
        if isinstance(input_path, list):
            lstFilesDCM = input_path
        else:
            path = Path(input_path)
            if not path.is_file():
                lstFilesDCM = [str(name) for name in glob.glob(input_path + "*.dcm")]
            else:
                lstFilesDCM = [input_path]
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
        self.widget.timeLine.setPen(color=(200, 200, 200), width=8)
        self.widget.timeLine.setHoverPen(color=(255, 255, 255), width=8)

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

    def load_plot(self, result: Optional[TimeSeriesResult] = None):
        sc = MplCanvas(self)
        if result is None:
            result = TimeSeriesResult(data=np.random.normal(size=10).tolist())

        result.show(sc.axes)
        self.layout().addWidget(sc)
        self.widget = sc

    def load_pickled_plot(self, input_path, task: Optional[ScanTask] = None):
        if not input_path:
            self.set_empty_viewer()
            return

        pickled_file_path = Path(input_path)

        if not pickled_file_path.is_file():
            log.error("File not found: " + str(pickled_file_path))
            return

        # TODO: Add error handling!
        self.widget = QWidget()
        self.widget.setLayout(QVBoxLayout(self.widget))
        self.widget.layout().setContentsMargins(0, 0, 0, 0)
        self.widget.layout().setSpacing(0)

        plt.style.use("dark_background")
        with open(pickled_file_path, "rb") as pickle_file:
            fig = pickle.load(pickle_file)

        figCanvas = FigureCanvasQTAgg(fig)
        fig.tight_layout()
        # fig.set_figheight(8)
        # fig.set_figwidth(5)

        toolbar = NavigationToolbar2QT(figCanvas, self)
        toolbar.setStyleSheet(
            "QToolBar::separator { background-color: #0C1123; } QFrame, QFrame:hover { border: 0px solid #000; }  QToolBar { background-color: #000; } QToolButton { background-color: #262C44; } QToolButton:checked { background-color: #FFF; }  QToolButton:disabled { background-color: #000; } QToolButton:hover { background-color: #E0A526; }"
        )
        unwanted_buttons = ["Back", "Forward"]
        for x in toolbar.actions():
            if x.text() in unwanted_buttons:
                toolbar.removeAction(x)

        self.widget.layout().addWidget(figCanvas)
        self.widget.layout().addWidget(toolbar)
        self.layout().addWidget(self.widget)
