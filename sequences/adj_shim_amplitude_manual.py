import os

from PyQt5 import uic 

from pathlib import Path

from external.seq.adjustments_acq.calibration import shim_cal_linear
import external.seq.adjustments_acq.config as cfg
from common.ipc.ipc import *

import common.logger as logger

from sequences import PulseqSequence
from sequences import make_rf_se

import configparser
from sequences.common.util import reading_json_parameter, writing_json_parameter

# Extracting configuration
configuration_data=reading_json_parameter()
LARMOR_FREQ = configuration_data.rf_parameters.larmor_frequency_MHz

log = logger.get_logger()


class CalShimAmplitude(PulseqSequence, registry_key=Path(__file__).stem):
    @classmethod
    def get_readable_name(self) -> str:
        return "Manually set B0 shims"

    @classmethod
    def get_description(self) -> str:
        return "Adjust Shim Sequence manually."
    
    def setup_ui(self, widget) -> bool:
        seq_path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(f"{seq_path}/{self.get_name()}/interface.ui", widget)
        return True

    def get_parameters(self) -> dict:
        return {"TE": self.param_TE, "TR": self.param_TR, "NSA": self.param_NSA, "ADC_samples": self.param_ADC_samples, "ADC_duration": self.param_ADC_duration, "N_ITER":self.param_N_ITER} # , 

    @classmethod
    def get_default_parameters(
        self
    ) -> dict:
        return {"TE": 70, "TR": 250, "NSA": 1, "ADC_samples": 4096, "ADC_duration": 6400, "N_ITER": 1}

    def set_parameters(self, parameters, scan_task) -> bool:
        self.problem_list = []
        try:
            self.param_TE = parameters["TE"]
            self.param_TR = parameters["TR"]
            self.param_NSA = parameters["NSA"]
            self.param_ADC_samples = parameters["ADC_samples"]
            self.param_ADC_duration = parameters["ADC_duration"]
            self.param_N_ITER = parameters["N_ITER"]
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
        widget.N_ITER_SpinBox.setValue(self.param_N_ITER)
        
        return True

    def read_parameters_from_ui(self, widget, scan_task) -> bool:
        self.problem_list = []
        self.param_TE = widget.TESpinBox.value()
        self.param_TR = widget.TRSpinBox.value()
        self.param_NSA = widget.NSA_SpinBox.value()
        self.param_ADC_samples = widget.ADC_samples_SpinBox.value()
        self.param_ADC_duration = widget.ADC_duration_SpinBox.value()
        self.param_N_ITER = widget.N_ITER_SpinBox.value()
        self.validate_parameters(scan_task)
        return self.is_valid()

    def validate_parameters(self, scan_task) -> bool:
        if self.param_TE > self.param_TR:
            self.problem_list.append("TE cannot be longer than TR")
        if self.param_N_ITER < 1:
            self.problem_list.append("Cannot have less than 1 iteration")
        return self.is_valid()


    def calculate_sequence(self, scan_task) -> bool:
        scan_task.processing.recon_mode = "bypass"

        self.seq_file_path = self.get_working_folder() + "/seq/shim.seq"
        log.info("Calculating sequence " + self.get_name())
        make_rf_se.pypulseq_rfse(inputs={"TE":70, "TR":250, "NSA":1, "ADC_samples": 4096, \
                              "ADC_duration": 6400}, check_timing=True, output_file=self.seq_file_path)

        log.info("Done calculating sequence " + self.get_name())
        self.calculated = True
        return True

    def run_sequence(self, scan_task) -> bool:
        
        # calculate the linear shim 
        axes = ['x', 'y', 'z']
        log.info("Running manual shimming")
    
        k = Communicator(Communicator.RECON)

        result = k.do_shim(new_user_values, new_signal)
        
        log.info("Manual shimming finished")
        return True
