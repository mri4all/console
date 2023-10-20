from pathlib import Path

import external.seq.adjustments_acq.config as cfg
from external.seq.adjustments_acq.calibration import larmor_cal, larmor_step_search
from sequences.common.util import reading_json_parameter, writing_json_parameter

import common.logger as logger

from sequences import PulseqSequence  # type: ignore
from sequences.rf_se import pypulseq_rfse  # type: ignore


log = logger.get_logger()


class AdjFrequency(PulseqSequence, registry_key=Path(__file__).stem):
    @classmethod
    def get_readable_name(self) -> str:
        return "Adjust Frequency"

    def calculate_sequence(self, scan_task) -> bool:
        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"
        log.info("Calculating sequence " + self.get_name())

        pypulseq_rfse(inputs={}, check_timing=True, output_file=self.seq_file_path)

        log.info("Done calculating sequence " + self.get_name())
        self.calculated = True
        return True

    def run_sequence(self, scan_task) -> bool:
        log.info("Running sequence " + self.get_name())

        # Using external packages now: TODO: convert to classes later

        # reading configuration data from config.json
        configuration_data=reading_json_parameter()

        max_snr_freq, data_dict = larmor_step_search(
            seq_file=self.seq_file_path,
            step_search_center=configuration_data.rf_parameters.larmor_frequency_MHz,
            steps=30,
            step_bw_MHz=10e-3,
            plot=True,  # For Debug
            shim_x=cfg.SHIM_X,
            shim_y=cfg.SHIM_Y,
            shim_z=cfg.SHIM_Z,
            delay_s=1,
            gui_test=False,
        )

        opt_max_snr_freq, data_dict = larmor_step_search(
            seq_file=self.seq_file_path,
            step_search_center=max_snr_freq,
            steps=30,
            step_bw_MHz=5e-3,
            plot=True,  # For Debug
            shim_x=cfg.SHIM_X,
            shim_y=cfg.SHIM_Y,
            shim_z=cfg.SHIM_Z,
            delay_s=1,
            gui_test=False,
        )

        larmor_freq, data_dict = larmor_cal(
            seq_file=self.seq_file_path,
            larmor_start=opt_max_snr_freq,
            iterations=10,
            delay_s=1,
            echo_count=1,
            step_size=0.6,
            plot=True,  # For debug
            shim_x=cfg.SHIM_X,
            shim_y=cfg.SHIM_Y,
            shim_z=cfg.SHIM_Z,
            gui_test=False,
        )

        calibrated_larmor_freq, data_dict = larmor_cal(
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
            gui_test=False,
        )

        print("Final Larmor frequency : " + str(calibrated_larmor_freq) + " MHz")

        # updating the Larmor frequency in the config.json file
        configuration_data.rf_parameters.larmor_frequency_MHz = calibrated_larmor_freq
        writing_json_parameter(config_data=configuration_data)

        log.info("Done running sequence " + self.get_name())
        return True
