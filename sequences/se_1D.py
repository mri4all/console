import os
from pathlib import Path
import math
import numpy as np
import matplotlib.pyplot as plt
import pickle

from common.types import ResultItem
from PyQt5 import uic

import pypulseq as pp  # type: ignore
import external.seq.adjustments_acq.config as cfg
from external.seq.adjustments_acq.scripts import run_pulseq

from sequences import PulseqSequence
from sequences.common import make_se_1D
import common.logger as logger
from sequences.common import view_traj

log = logger.get_logger()


class SequenceRF_SE(PulseqSequence, registry_key=Path(__file__).stem):
    # Sequence parameters
    param_TE: int = 50
    param_TR: int = 3000
    param_NSA: int = 1
    param_FOV: int = 20
    param_Base_Resolution: int = 96
    param_BW: int = 32000
    param_Gradient: str = "x"
    param_debug_plot: bool = True

    @classmethod
    def get_readable_name(self) -> str:
        return "1D Spin-Echo"

    @classmethod
    def get_description(self) -> str:
        return "Spin-Echo sequence with gradient encoding in a pre-selected direction (projection)"

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
            "Base_Resolution": self.param_Base_Resolution,
            "BW": self.param_BW,
            "Gradient": self.param_Gradient,
            "debug_plot": self.param_debug_plot,
        }

    @classmethod
    def get_default_parameters(self) -> dict:
        return {
            "TE": 50,
            "TR": 1000,
            "NSA": 1,
            "FOV": 15,
            "Base_Resolution": 256,
            "BW": 32000,
            "Gradient": "x",
        }

    def set_parameters(self, parameters, scan_task) -> bool:
        self.problem_list = []
        try:
            self.param_TE = parameters["TE"]
            self.param_TR = parameters["TR"]
            self.param_NSA = parameters["NSA"]
            self.param_FOV = parameters["FOV"]
            self.param_Base_Resolution = parameters["Base_Resolution"]
            self.param_BW = parameters["BW"]
            self.param_Gradient = parameters["Gradient"]
            self.param_debug_plot = parameters["debug_plot"]
        except:
            self.problem_list.append("Invalid parameters provided")
            return False
        return self.validate_parameters(scan_task)

    def write_parameters_to_ui(self, widget) -> bool:
        widget.TESpinBox.setValue(self.param_TE)
        widget.TRSpinBox.setValue(self.param_TR)
        widget.NSA_SpinBox.setValue(self.param_NSA)
        widget.FOV_SpinBox.setValue(self.param_FOV)
        widget.Base_Resolution_SpinBox.setValue(self.param_Base_Resolution)
        widget.BW_SpinBox.setValue(self.param_BW)
        widget.Gradient_ComboBox.setCurrentText(self.param_Gradient)
        return True

    def read_parameters_from_ui(self, widget, scan_task) -> bool:
        self.problem_list = []
        self.param_TE = widget.TESpinBox.value()
        self.param_TR = widget.TRSpinBox.value()
        self.param_NSA = widget.NSA_SpinBox.value()
        self.param_FOV = widget.FOV_SpinBox.value()
        self.param_Base_Resolution = widget.Base_Resolution_SpinBox.value()
        self.param_BW = widget.BW_SpinBox.value()
        self.param_Gradient = widget.Gradient_ComboBox.currentText()
        self.validate_parameters(scan_task)
        return self.is_valid()

    def validate_parameters(self, scan_task) -> bool:
        if self.param_TE > self.param_TR:
            self.problem_list.append("TE cannot be longer than TR")
        return self.is_valid()

    def calculate_sequence(self, scan_task) -> bool:
        log.info("Calculating sequence " + self.get_name())
        scan_task.processing.recon_mode = "bypass"
        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"

        plt.clf()
        plt.title("Sequence")

        make_se_1D.pypulseq_1dse(
            inputs={
                "TE": self.param_TE,
                "TR": self.param_TR,
                "NSA": self.param_NSA,
                "FOV": self.param_FOV,
                "Base_Resolution": self.param_Base_Resolution,
                "BW": self.param_BW,
                "Gradient": self.param_Gradient,
            },
            check_timing=True,
            output_file=self.seq_file_path,
        )

        file = open(self.get_working_folder() + "/other/seq1.plot", "wb")
        fig = plt.figure(1)
        pickle.dump(fig, file)
        file.close()
        result = ResultItem()
        result.name = "SEQ1"
        result.description = "Sequence diagram RF/ADC"
        result.type = "plot"
        result.file_path = "other/seq1.plot"
        scan_task.results.append(result)

        file = open(self.get_working_folder() + "/other/seq2.plot", "wb")
        fig = plt.figure(2)
        pickle.dump(fig, file)
        file.close()
        result = ResultItem()
        result.name = "SEQ2"
        result.description = "Sequence diagram Grad"
        result.type = "plot"
        result.file_path = "other/seq2.plot"
        scan_task.results.append(result)

        log.info("Done calculating sequence " + self.get_name())
        self.calculated = True
        return True

    def run_sequence(self, scan_task) -> bool:
        log.info("Running sequence " + self.get_name())
        iterations = 1
        for iter in range(iterations):
            rxd, rx_t = run_pulseq(
                seq_file=self.seq_file_path,
                rf_center=cfg.LARMOR_FREQ,
                tx_t=1,
                grad_t=10,
                tx_warmup=100,
                shim_x=-0.0,
                shim_y=-0.0,
                shim_z=-0.0,
                grad_cal=False,
                save_np=False,
                save_mat=False,
                save_msgs=True,
                gui_test=False,
                case_path=self.get_working_folder(),
            )

        log.info("Done running sequence " + self.get_name())

        log.info("Plotting figures")
        plt.clf()
        plt.title(f"ADC Signal - Grad_{self.param_Gradient}")
        plt.grid(True, color="#333")
        plt.plot(np.abs(rxd))
        file = open(self.get_working_folder() + "/other/adc.plot", "wb")
        fig = plt.gcf()
        pickle.dump(fig, file)
        file.close()
        result = ResultItem()
        result.name = "ADC"
        result.description = "Acquired ADC signal"
        result.type = "plot"
        result.autoload_viewer = 1
        result.file_path = "other/adc.plot"
        scan_task.results.insert(0, result)

        plt.clf()
        plt.title(f"FFT of Signal - Grad_{self.param_Gradient}")
        recon = np.fft.fftshift(np.fft.ifft(np.fft.fftshift(rxd)))
        plt.grid(True, color="#333")
        plt.plot(np.abs(recon))
        file = open(self.get_working_folder() + "/other/fft.plot", "wb")
        fig = plt.gcf()
        pickle.dump(fig, file)
        file.close()
        result = ResultItem()
        result.name = "FFT"
        result.description = "FFT of ADC signal"
        result.type = "plot"
        result.autoload_viewer = 2
        result.primary = True
        result.file_path = "other/fft.plot"
        scan_task.results.insert(1, result)

        # Save the raw data file
        log.info("Saving rawdata, sequence " + self.get_name())
        self.raw_file_path = self.get_working_folder() + "/rawdata/raw.npy"
        np.save(self.raw_file_path, rxd)

        return True
