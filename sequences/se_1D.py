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
from sequences import make_se_1D
import common.logger as logger
from sequences.common import view_traj

log = logger.get_logger()


class SequenceRF_SE(PulseqSequence, registry_key=Path(__file__).stem):
    # Sequence parameters
    param_TE: int = 20
    param_TR: int = 3000
    param_NSA: int = 1
    param_FOV: int = 20
    param_Base_Resolution: int = 96
    param_BW: int = 32000
    param_Gradient: str = "y"
    param_debug_plot: bool = True

    @classmethod
    def get_readable_name(self) -> str:
        return "1D Spin-Echo"

    def setup_ui(self, widget) -> bool:
        seq_path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(f"{seq_path}/{self.get_name()}/interface.ui", widget)
        return True

    def get_parameters(self) -> dict:
        return {"TE": self.param_TE, "TR": self.param_TR,
        "NSA": self.param_NSA, 
        "FOV": self.param_FOV,
        "Base_Resolution": self.param_Base_Resolution,
        "BW":self.param_BW,
        "Gradient":self.param_Gradient,
        "debug_plot": self.param_debug_plot}

    @classmethod
    def get_default_parameters(self) -> dict:
        return {"TE": 20, "TR": 3000,
        "NSA": 1, 
        "FOV": 20,
        "Base_Resolution": 250,
        "BW": 32000,
        "Gradient":"y",}

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
        scan_task.processing.recon_mode = "bypass"
        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"
        log.info("Calculating sequence " + self.get_name())

        make_se_1D.pypulseq_1dse(
            inputs={"TE": self.param_TE, "TR": self.param_TR,
            "NSA": self.param_NSA, 
            "FOV": self.param_FOV,
            "Base_Resolution": self.param_Base_Resolution,
            "BW":self.param_BW,
            "Gradient":self.param_Gradient},
            check_timing=True,
            output_file=self.seq_file_path,
        )

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
                shim_x=0,
                shim_y=0,
                shim_z=0,
                grad_cal=False,
                save_np=False,
                save_mat=False,
                save_msgs=False,
                gui_test=False,
            )

        # Debug
        if 1>0: # TODO: set debug mode
            # plt.figure()
            # plt.subplot(121)
            # plt.plot(np.abs(rxd))
            # plt.title("acq signal")
            # plt.subplot(122)
            # recon = np.fft.fft(np.fft.fftshift(rxd))
            # plt.plot(np.abs(recon))
            # plt.title("fft signal")
            # plt.show()

            # view_traj.view_sig(rxd, self.get_working_folder())

            log.info("Plotting figure now")
            plt.style.use("dark_background")
            plt.clf()
            plt.subplot(121)
            plt.title('Acq signal')
            plt.grid(False)
            plt.plot(np.abs(rxd))
            plt.subplot(122)
            recon = np.fft.fft(np.fft.fftshift(rxd))
            plt.plot(np.abs(recon))
            plt.title("FFT signal")
            if self.param_debug_plot:
                plt.show()
            file = open(self.get_working_folder() + "/other/se_1D.plot", 'wb')
            fig = plt.gcf()
            pickle.dump(fig, file)
            file.close()
            result = ResultItem()
            result.name = "demo"
            result.description = "This is just a plot"
            result.type = "plot"
            result.primary = True
            result.autoload_viewer = 1
            result.file_path = 'other/se_1D.plot'
            scan_task.results.append(result)


        log.info("Done running sequence " + self.get_name())

        
        # save the raw data file
        self.raw_file_path = self.get_working_folder() + "/rawdata/raw.npy"
        np.save(self.raw_file_path, rxd)

        log.info("Saving rawdata, sequence " + self.get_name())

        return True

