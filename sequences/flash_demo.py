import os
import time
from pathlib import Path
from PyQt5 import uic

import common.logger as logger

log = logger.get_logger()

import common.task as task
from common.constants import *
from . import PulseqSequence
from common.ipc import Communicator

ipc_comm = Communicator(Communicator.ACQ)


class SequenceFlash(PulseqSequence, registry_key=Path(__file__).stem):
    # Sequence parameters
    param_baseresolution: int = 64
    param_flipangle: int = 15
    param_TE: int = 10
    param_TR: int = 200

    @classmethod
    def get_readable_name(self) -> str:
        return "UI Demo: 2D Flash  [dummy]"

    @classmethod
    def get_description(self) -> str:
        return "Demo sequence that injects fake DICOMs for testing the UI"

    def setup_ui(self, widget) -> bool:
        seq_path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(f"{seq_path}/{self.get_name()}/interface.ui", widget)

        widget.baseresolutionSpinBox.valueChanged.connect(self.update_info)
        widget.flipAngleSpinBox.valueChanged.connect(self.update_info)
        widget.TESpinBox.valueChanged.connect(self.update_info)
        widget.TRSpinBox.valueChanged.connect(self.update_info)

        return True

    def update_info(self):
        duration = int(
            self.main_widget.TRSpinBox.value()
            * self.main_widget.baseresolutionSpinBox.value()
            / 1000
        )
        self.show_ui_info_text(
            f"TA: {duration} sec       Voxel Size: 1.0 x 1.0 x 1.0 mm"
        )

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
        self.update_info()
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
        for i in range(0, 10):
            ipc_comm.send_status(f"Running sequence {i*10}%...")
            time.sleep(1)
            if task.has_task_state(self.get_working_folder(), mri4all_files.STOP):
                log.info("Termination of sequence requested")
                log.info("Stopping sequence")
                return False

        scan_task.processing.recon_mode = "fake_dicoms"
        return True
