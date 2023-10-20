import os
import time
from pathlib import Path
from PyQt5 import uic

from . import PulseqSequence


class SequenceFlash(PulseqSequence, registry_key=Path(__file__).stem):
    # Sequence parameters
    param_baseresolution: int = 64
    param_flipangle: int = 15
    param_TE: int = 10
    param_TR: int = 200

    @classmethod
    def get_readable_name(self) -> str:
        return "UI Demo: 2D Flash"

    @classmethod
    def get_description(self) -> str:
        return "Demo sequence that injects fake DICOMs for testing the UI"

    def setup_ui(self, widget) -> bool:
        seq_path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(f"{seq_path}/{self.get_name()}/interface.ui", widget)
        return True

    def get_parameters(self) -> dict:
        return {
            "baseresolution": self.param_baseresolution,
            "flipangle": self.param_flipangle,
            "TE": self.param_TE,
            "TR": self.param_TR,
        }

    @classmethod
    def get_default_parameters(self) -> dict:
        return {"baseresolution": 64, "flipangle": 10, "TE": 10, "TR": 200}

    def set_parameters(self, parameters, scan_task) -> bool:
        self.problem_list = []
        try:
            self.param_baseresolution = parameters["baseresolution"]
            self.param_flipangle = parameters["flipangle"]
            self.param_TE = parameters["TE"]
            self.param_TR = parameters["TR"]
        except:
            self.problem_list.append("Invalid parameters provided")
            return False
        return self.validate_parameters(scan_task)

    def write_parameters_to_ui(self, widget) -> bool:
        widget.baseresolutionSpinBox.setValue(self.param_baseresolution)
        widget.flipAngleSpinBox.setValue(self.param_flipangle)
        widget.TESpinBox.setValue(self.param_TE)
        widget.TRSpinBox.setValue(self.param_TR)
        return True

    def read_parameters_from_ui(self, widget, scan_task) -> bool:
        self.problem_list = []
        self.param_baseresolution = widget.baseresolutionSpinBox.value()
        self.param_flipangle = widget.flipAngleSpinBox.value()
        self.param_TE = widget.TESpinBox.value()
        self.param_TR = widget.TRSpinBox.value()
        self.validate_parameters(scan_task)
        return self.is_valid()

    def validate_parameters(self, scan_task) -> bool:
        if self.param_TE > self.param_TR:
            self.problem_list.append("TE cannot be longer than TR")
        return self.is_valid()

    def run_sequence(self, scan_task) -> bool:
        time.sleep(2)
        scan_task.processing.recon_mode = "fake_dicoms"
        return True
