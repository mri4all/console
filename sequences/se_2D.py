import os
from pathlib import Path
import math
import numpy as np
import matplotlib.pyplot as plt
from PyQt5 import uic

import pypulseq as pp  # type: ignore
import external.seq.adjustments_acq.config as cfg
from external.seq.adjustments_acq.scripts import run_pulseq

from sequences import PulseqSequence
from sequences.common import make_se_2D
from sequences.common import view_traj
import common.logger as logger
from common.types import ResultItem

log = logger.get_logger()


class SequenceSE_2D(PulseqSequence, registry_key=Path(__file__).stem):
    # Sequence parameters
    param_TE: int = 20
    param_TR: int = 3000
    param_NSA: int = 1
    param_FOV: int = 20
    param_Orientation: str = "Axial"
    param_Base_Resolution: int = 96
    param_BW: int = 32000
    param_Trajectory: str = "Catisian"
    param_PE_Ordering: str = "Center_out"
    param_PF: int = 1
    param_view_traj: bool = True

    @classmethod
    def get_readable_name(self) -> str:
        return "2D Spin-Echo  [untested]"

    def setup_ui(self, widget) -> bool:
        seq_path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(f"{seq_path}/{self.get_name()}/interface.ui", widget)
        return True

    def get_parameters(self) -> dict:
        return {
            "TE": self.param_TE,
            "TR": self.param_TR,
            "NSA": self.param_NSA,
            "FOV": self.param_FOV,
            "Orientation": self.param_Orientation,
            "Base_Resolution": self.param_Base_Resolution,
            "BW": self.param_BW,
            "Trajectory": self.param_Trajectory,
            "PE_Ordering": self.param_PE_Ordering,
            "PF": self.param_PF,
            "view_traj": self.param_view_traj,
        }

    @classmethod
    def get_default_parameters(self) -> dict:
        return {
            "TE": 20,
            "TR": 3000,
            "NSA": 1,
            "FOV": 20,
            "Orientation": "Axial",
            "Base_Resolution": 96,
            "BW": 32000,
            "Trajectory": "Cartesian",
            "PE_Ordering": "Center_out",
            "PF": 1,
            "view_traj": True,
        }

    def set_parameters(self, parameters, scan_task) -> bool:
        self.problem_list = []
        try:
            self.param_TE = parameters["TE"]
            self.param_TR = parameters["TR"]
            self.param_NSA = parameters["NSA"]
            self.param_FOV = parameters["FOV"]
            self.param_Orientation = parameters["Orientation"]
            self.param_Base_Resolution = parameters["Base_Resolution"]
            self.param_BW = parameters["BW"]
            self.param_Trajectory = parameters["Trajectory"]
            self.param_PE_Ordering = parameters["PE_Ordering"]
            self.param_PF = parameters["PF"]
            self.param_view_traj = parameters["view_traj"]
        except:
            self.problem_list.append("Invalid parameters provided")
            return False
        return self.validate_parameters(scan_task)

    def write_parameters_to_ui(self, widget) -> bool:
        widget.TESpinBox.setValue(self.param_TE)
        widget.TRSpinBox.setValue(self.param_TR)
        widget.NSA_SpinBox.setValue(self.param_NSA)
        widget.Orientation_ComboBox.setCurrentText(self.param_Orientation)
        widget.FOV_SpinBox.setValue(self.param_FOV)
        widget.Base_Resolution_SpinBox.setValue(self.param_Base_Resolution)
        widget.BW_SpinBox.setValue(self.param_BW)
        widget.Trajectory_ComboBox.setCurrentText(self.param_Trajectory)
        widget.PE_Ordering_ComboBox.setCurrentText(self.param_PE_Ordering)
        widget.PF_SpinBox.setValue(self.param_PF)
        widget.visualize_traj_CheckBox.setCheckState(self.param_view_traj)

        return True

    def read_parameters_from_ui(self, widget, scan_task) -> bool:
        self.problem_list = []
        self.param_TE = widget.TESpinBox.value()
        self.param_TR = widget.TRSpinBox.value()
        self.param_NSA = widget.NSA_SpinBox.value()
        self.param_Orientation = widget.Orientation_ComboBox.currentText()
        self.param_FOV = widget.FOV_SpinBox.value()
        self.param_Base_Resolution = widget.Base_Resolution_SpinBox.value()
        self.param_BW = widget.BW_SpinBox.value()
        self.param_Trajectory = widget.Trajectory_ComboBox.currentText()
        self.param_PE_Ordering = widget.PE_Ordering_ComboBox.currentText()
        self.param_PF = widget.PF_SpinBox.value()
        self.param_view_traj = widget.visualize_traj_CheckBox.isChecked()
        self.validate_parameters(scan_task)
        return self.is_valid()

    def validate_parameters(self, scan_task) -> bool:
        if self.param_TE > self.param_TR:
            self.problem_list.append("TE cannot be longer than TR")
        return self.is_valid()

    def calculate_sequence(self, scan_task) -> bool:
        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"
        log.info("Calculating sequence " + self.get_name())

        # ToDo: if self.Trajectory == "Cartesian": (default)
        make_se_2D.pypulseq_se2D(
            inputs={
                "TE": self.param_TE,
                "TR": self.param_TR,
                "NSA": self.param_NSA,
                "FOV": self.param_FOV,
                "Orientation": self.param_Orientation,
                "Base_Resolution": self.param_Base_Resolution,
                "BW": self.param_BW,
                "Trajectory": self.param_Trajectory,
                "PE_Ordering": self.param_PE_Ordering,
                "PF": self.param_PF,
                "view_traj": self.param_view_traj,
            },
            check_timing=True,
            output_file=self.seq_file_path,
            output_folder=self.get_working_folder(),
        )
        # elif self.Trajectory == "Radial":
        # pypulseq_se2D_radial(
        #    inputs={"TE": self.param_TE, "TR": self.param_TR}, check_timing=True, output_file=self.seq_file_path
        # )

        log.info("Done calculating sequence " + self.get_name())
        self.calculated = True

        if self.param_view_traj is True:
            log.info("Displaying trajectory... " + self.get_name())
            result = ResultItem()
            result.name = "traj plot"
            result.description = "Plot of trajectory in k space of current sequence."
            result.type = "plot"
            result.primary = True
            result.autoload_viewer = 1
            result.file_path = "other/traj.plot"
            scan_task.results.append(result)

        return True

    def run_sequence(self, scan_task) -> bool:
        log.info("Running sequence " + self.get_name())

        rxd, rx_t = run_pulseq(
            seq_file=self.seq_file_path,
            rf_center=cfg.LARMOR_FREQ,
            tx_t=1,
            grad_t=10,
            tx_warmup=100,
            shim_x=0,
            shim_y=0,
            shim_z=0,
            grad_cal=False,
            save_np=False,
            save_mat=False,
            save_msgs=False,
            gui_test=False,
            case_path=self.get_working_folder(),
        )

        log.info("Done running sequence " + self.get_name())

        # test for recon testing
        data = rxd.reshape((70, 70))
        plt.figure()
        plt.subplot(131)
        plt.imshow(np.abs(data))
        plt.title("kspace, abs")
        plt.subplot(132)
        plt.imshow(np.real(data))
        plt.title("real")
        plt.subplot(133)
        plt.imshow(np.imag(data))
        plt.title("imag")
        plt.show()

        img = np.fft.fft2(data)
        plt.figure()
        plt.subplot(131)
        plt.imshow(np.abs(img))
        plt.title("image, abs")
        plt.subplot(132)
        plt.imshow(np.real(img))
        plt.title("real")
        plt.subplot(133)
        plt.imshow(np.imag(img))
        plt.title("imag")
        plt.show()

        # save the raw data file
        self.raw_file_path = self.get_working_folder() + "/rawdata/raw.npy"
        np.save(self.raw_file_path, rxd)

        log.info("Saving rawdata, sequence " + self.get_name())
        return True
