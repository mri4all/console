from pathlib import Path

import external.seq.adjustments_acq.config as cfg
from external.seq.adjustments_acq.calibration import larmor_step_search, load_plot_in_ui
from sequences.common.util import reading_json_parameter, writing_json_parameter

import common.logger as logger

from sequences import PulseqSequence  # type: ignore
from sequences.common import make_rf_se  # type: ignore


log = logger.get_logger()


class AdjFrequency(PulseqSequence, registry_key=Path(__file__).stem):
    @classmethod
    def get_readable_name(self) -> str:
        return "Prescan Frequency  [untested]"

    def calculate_sequence(self, scan_task) -> bool:
        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"
        log.info("Calculating sequence " + self.get_name())

        make_rf_se.pypulseq_rfse(
            inputs={
                "TE": 70,
                "TR": 250,
                "NSA": 1,
                "ADC_samples": 4096,
                "ADC_duration": 6400,
                "FA1": 90,
                "FA2": 180,
            },
            check_timing=True,
            output_file=self.seq_file_path,
        )

        log.info("Done calculating sequence " + self.get_name())
        self.calculated = True
        return True

    def run_sequence(self, scan_task) -> bool:
        log.info("Running sequence " + self.get_name())

        # Using external packages now: TODO: convert to classes later

        # reading configuration data from config.json
        configuration_data = reading_json_parameter()

        working_folder = self.get_working_folder()

        max_freq, data_dict, fig = larmor_step_search(
            seq_file=self.seq_file_path,
            step_search_center=configuration_data.rf_parameters.larmor_frequency_MHz,
            steps=2,
            step_bw_MHz=5e-3,
            plot=True,  # For Debug
            shim_x=cfg.SHIM_X,
            shim_y=cfg.SHIM_Y,
            shim_z=cfg.SHIM_Z,
            delay_s=1,
            gui_test=False,
        )

        plot_result = load_plot_in_ui(
            working_folder=working_folder, file_name="plot_result", fig=fig
        )
        scan_task.results.append(plot_result)

        print("Final Larmor frequency : " + str(max_freq) + " MHz")

        # updating the Larmor frequency in the config.json file
        configuration_data.rf_parameters.larmor_frequency_MHz = max_freq
        writing_json_parameter(config_data=configuration_data)

        log.info("Done running sequence " + self.get_name())
        return True
