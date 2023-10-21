import os

from PyQt5 import uic 

from pathlib import Path

from external.seq.adjustments_acq.calibration import shim_cal_linear
import external.seq.adjustments_acq.config as cfg

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
        return "Calibrate B0 shims"

    @classmethod
    def get_description(self) -> str:
        return "Adjust Shim Sequence."
    
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
        log.info("Running sequence " + self.get_name())
        
        shim_range = 0.1
        
        for shim_iter in range(int(n_iter_linear)):
            
            for channel in axes:
                log.info(f"Updating {channel} linear shim (iter {shim_iter})")
                shim_weight = shim_cal_linear(seq_file=self.seq_file_path,
                        larmor_freq=LARMOR_FREQ,
                        channel=channel,
                        range=shim_range,
                        shim_points=5,
                        points=2,
                        iterations=1,
                        zoom_factor=2,
                        shim_x=cfg.SHIM_X,
                        shim_y=cfg.SHIM_Y,
                        shim_z=cfg.SHIM_Z,
                        tr_spacing=2,
                        force_tr=False,
                        first_max=False,
                        smooth=True,
                        plot=True,
                        gui_test=False)
                
                # write to config file
                if channel == 'x':
                    configuration_data.shim_parameters.shim_x = shim_weight
                elif channel == 'y':
                    configuration_data.shim_parameters.shim_y = shim_weight   
                elif channel == 'z':
                    configuration_data.shim_parameters.shim_z = shim_weight
                writing_json_parameter(config_data=configuration_data)
            
            # decrease the range a bit with each iteration, to a min bound
            if range > 0.01:
                range = range / 2
            else:
                range = range
        
        
        log.info("Done running sequence " + self.get_name())
        return True
