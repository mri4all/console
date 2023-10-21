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
from sequences import make_rf_se
import common.logger as logger

log = logger.get_logger()


class SequenceRF_SE(PulseqSequence, registry_key=Path(__file__).stem):
    # Sequence parameters
    param_TE: int = 70
    param_TR: int = 250
    param_NSA: int = 1
    param_ADC_samples: int = 4096
    param_ADC_duration: int = 6400


    @classmethod
    def get_readable_name(self) -> str:
        return "RF Spin-Echo"

    def setup_ui(self, widget) -> bool:
        seq_path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(f"{seq_path}/{self.get_name()}/interface.ui", widget)
        return True

    def get_parameters(self) -> dict:
        return {"TE": self.param_TE, "TR": self.param_TR, "NSA": self.param_NSA, "ADC_samples": self.param_ADC_samples, "ADC_duration": self.param_ADC_duration} # , 

    @classmethod
    def get_default_parameters(
        self
    ) -> dict:
        return {"TE": 70, "TR": 250, "NSA": 1, "ADC_samples": 4096, "ADC_duration": 6400}


    def set_parameters(self, parameters, scan_task) -> bool:
        self.problem_list = []
        try:
            self.param_TE = parameters["TE"]
            self.param_TR = parameters["TR"]
            self.param_NSA = parameters["NSA"]
            self.param_ADC_samples = parameters["ADC_samples"]
            self.param_ADC_duration = parameters["ADC_duration"]
        except:
            self.problem_list.append("Invalid parameters provided")
            return False
        return self.validate_parameters(scan_task)

    def write_parameters_to_ui(self, widget) -> bool:
        widget.TESpinBox.setValue(self.param_TE)
        widget.TRSpinBox.setValue(self.param_TR)
        widget.NSA_SpinBox.setValue(self.param_NSA)
        widget.ADC_samples_SpinBox.setValue(self.param_ADC_samples)
        widget.ADC_duration_SpinBox.setValue(self.param_ADC_duration)
        
        return True

    def read_parameters_from_ui(self, widget, scan_task) -> bool:
        self.problem_list = []
        self.param_TE = widget.TESpinBox.value()
        self.param_TR = widget.TRSpinBox.value()
        self.param_NSA = widget.NSA_SpinBox.value()
        self.param_ADC_samples = widget.ADC_samples_SpinBox.value()
        self.param_ADC_duration = widget.ADC_duration_SpinBox.value()
        self.validate_parameters(scan_task)
        return self.is_valid()

    def validate_parameters(self, scan_task) -> bool:
        if self.param_TE > self.param_TR:
            self.problem_list.append("TE cannot be longer than TR")
        return self.is_valid()

    def calculate_sequence(self, scan_task) -> bool:
        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"
        log.info("Calculating sequence " + self.get_name())

        make_rf_se.pypulseq_rfse(
            inputs={"TE": self.param_TE, "TR": self.param_TR, "NSA": self.param_NSA, 
            "ADC_samples":self.param_ADC_samples, "ADC_duration":self.param_ADC_duration}, check_timing=True, output_file=self.seq_file_path
        ) # 

        log.info("Done calculating sequence " + self.get_name())
        self.calculated = True
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
        )

        # Debug 
        plt.figure()
        plt.plot(np.abs(rxd))
        plt.show()

        log.info("Done running sequence " + self.get_name())
        return True