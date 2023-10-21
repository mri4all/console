from pathlib import Path

import external.seq.adjustments_acq.config as cfg
from external.seq.adjustments_acq.calibration import larmor_cal, larmor_step_search
from sequences.common.util import reading_json_parameter, writing_json_parameter
from sequences.common.pydanticConfig import Config

import common.logger as logger
from PyQt5 import uic
import os

from sequences import PulseqSequence  # type: ignore
from sequences import make_rf_se  # type: ignore


log = logger.get_logger()

class AdjFrequency(PulseqSequence, registry_key=Path(__file__).stem):
    # Sequence parameters
    param_TE: int = 70
    param_TR: int = 250
    param_NSA: int = 1
    param_ADC_samples: int = 4096
    param_ADC_duration: int = 6400


    @classmethod
    def get_readable_name(self) -> str:
        return "Adjust Frequency with maximum"

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

        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"
        log.info("Calculating sequence " + self.get_name())

        make_rf_se.pypulseq_rfse(
            inputs={"TE": self.param_TE, "TR": self.param_TR, "NSA": self.param_NSA, 
            "ADC_samples":self.param_ADC_samples, "ADC_duration":self.param_ADC_duration}, check_timing=True, output_file=self.seq_file_path
        ) 
        # make_rf_se.pypulseq_rfse(inputs={"TE":70, "TR":250, "NSA":1, "ADC_samples": 4096, \
        #                       "ADC_duration": 6400}, check_timing=True, output_file=self.seq_file_path)

        log.info("Done calculating sequence " + self.get_name())
        self.calculated = True
        return True

    def run_sequence(self, scan_task) -> bool:
        log.info("Running sequence " + self.get_name())

        # Using external packages now: TODO: convert to classes later

        # reading configuration data from config.json
        configuration_data=reading_json_parameter()

        working_folder = self.get_working_folder()

        max_freq, max_snr_freq, data_dict, plot_result_signal1, plot_result_noise1 = larmor_step_search(
            seq_file=self.seq_file_path,
            step_search_center=configuration_data.rf_parameters.larmor_frequency_MHz,
            steps=30,
            step_bw_MHz=10e-3,
            plot=True,  # For Debug
            shim_x=cfg.SHIM_X,
            shim_y=cfg.SHIM_Y,
            shim_z=cfg.SHIM_Z,
            working_folder=working_folder,
            delay_s=1,
            gui_test=False,
        )
        
        scan_task.results.append(plot_result_signal1)
        scan_task.results.append(plot_result_noise1)

        opt_max_freq, opt_max_snr_freq, data_dict, plot_result_signal2, plot_result_noise2 = larmor_step_search(
            seq_file=self.seq_file_path,
            step_search_center=max_freq,
            steps=30,
            step_bw_MHz=5e-3,
            plot=True,  # For Debug
            shim_x=cfg.SHIM_X,
            shim_y=cfg.SHIM_Y,
            shim_z=cfg.SHIM_Z,
            working_folder=working_folder,
            delay_s=1,
            gui_test=False,
        )

        scan_task.results.append(plot_result_signal2)
        scan_task.results.append(plot_result_noise2)

        larmor_freq, data_dict, plot_result1 = larmor_cal(
            seq_file=self.seq_file_path,
            larmor_start=opt_max_freq,
            iterations=10,
            delay_s=1,
            echo_count=1,
            step_size=0.6,
            plot=True,  # For debug
            shim_x=cfg.SHIM_X,
            shim_y=cfg.SHIM_Y,
            shim_z=cfg.SHIM_Z,
            working_folder=working_folder,
            gui_test=False,
        )

        scan_task.results.append(plot_result1)

        calibrated_larmor_freq, data_dict, plot_result2 = larmor_cal(
            seq_file=self.seq_file_path,
            larmor_start=larmor_freq,
            iterations=10,
            delay_s=1,
            echo_count=1,
            step_size=0.2,
            plot=True,  # For debug
            shim_x=cfg.SHIM_X,
            shim_y=cfg.SHIM_Y,
            shim_z=cfg.SHIM_Z,
            working_folder=working_folder,
            gui_test=False,
        )

        scan_task.results.append(plot_result2)

        print("Final Larmor frequency using maximum: " + str(calibrated_larmor_freq) + " MHz")

        # updating the Larmor frequency in the config.json file
        configuration_data.rf_parameters.larmor_frequency_MHz = calibrated_larmor_freq
        writing_json_parameter(config_data=configuration_data)

        log.info("Done running sequence " + self.get_name())
        return True
