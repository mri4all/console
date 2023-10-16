from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore
import qtawesome as qta  # type: ignore

import pyqtgraph as pg
import pydicom
import numpy as np
import os


class ViewerWidget(QWidget):
    def __init__(self):
        super(ViewerWidget, self).__init__()

    series_name = ""

    def set_series_name(self, name: str):
        self.series_name = name
        self.update()

    def configure(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.visualize_dcm_files()

        # if self.property("id") == "3":
        #     sc = MplCanvas(self, width=5, height=4, dpi=100)
        #     sc.axes.plot([0, 1, 2, 3, 4], [10, 1, 20, 3, 40])
        #     layout = QVBoxLayout(self)
        #     layout.setContentsMargins(0, 0, 0, 0)
        #     layout.addWidget(sc)

    def visualize_dcm_files(self):
        input_path = "/vagrant/classDcm"
        lstFilesDCM = []  # create an empty list
        for dirName, subdirList, fileList in sorted(os.walk(input_path)):
            for filename in fileList:
                if ".dcm" in filename.lower():
                    lstFilesDCM.append(os.path.join(dirName,filename))

        lstFilesDCM.sort()
        if len(lstFilesDCM) < 1:
            return
        ds = pydicom.dcmread(lstFilesDCM[0])

        ConstPixelDims = (len(lstFilesDCM), int(ds.Rows), int(ds.Columns))

        ArrayDicom = np.zeros(ConstPixelDims, dtype=ds.pixel_array.dtype)

        for filenameDCM in lstFilesDCM:
            ds = pydicom.dcmread(filenameDCM)
            ArrayDicom[lstFilesDCM.index(filenameDCM), :, :] = ds.pixel_array

        pg.setConfigOptions(imageAxisOrder='row-major')
        self.layout.addWidget(pg.image(ArrayDicom))