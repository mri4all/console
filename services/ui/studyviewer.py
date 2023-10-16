import json
import numpy as np
from pathlib import Path
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore

from common.version import mri4all_version
import common.runtime as rt
import common.logger as logger
log = logger.get_logger()


def show_viewer():
    w = StudyViewer()
    w.exec_()


class StudyViewer(QDialog):
    patient_info = {"31431":{"name":"Patient A", "exams": [{"id":"ABCD"}]},"43213":{"name":"Patient B", "exams": [{"id":"DEFG"}, {"id":"SDFSDF"}]}}

    def __init__(self):
        super(StudyViewer, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/studyviewer.ui", self)
        self.setWindowTitle("Study Viewer")

        self.patientComboBox.addItems([p["name"] for p in self.patient_info.values()])
        self.patientComboBox.currentIndexChanged.connect(self.patient_selected)

        self.archived_exam_path = Path('/opt/mri4all/data/archive')

        self.archived_exams_data = [self.get_exam_data(i) for i in self.archived_exam_path.glob('*') if i.is_dir()]

        print(self.archived_exams_data)

        self.patient_selected(0)

    def patient_selected(self, index):
        self.examListWidget.clear()
        the_patient = self.patient_info[list(self.patient_info.keys())[index]]
        for exam in the_patient["exams"]:
            self.examListWidget.addItem(exam["id"])
        pass

    
    def get_exam_data(self, path):
        data = {}
        data['dicom'] = np.array([]) # read dicom data from Dicom folder
        data['rawdata'] = np.array([]) # read raw data from rawdata folder
            
        metadata_file = Path(path) / 'scan.json'
        if metadata_file.is_file():
            with open(metadata_file, 'r') as f:
                data['scan_metadata'] = json.load(f)
        else:
            raise FileNotFoundError(f"scan.json not found in : {path}")
        
        return data


    def close_clicked(self):
        self.close()
