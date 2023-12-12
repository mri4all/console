from pathlib import Path

import external.seq.adjustments_acq.config as cfg
from external.seq.adjustments_acq.calibration import rf_max_cal

import common.logger as logger

from sequences import PulseqSequence  # type: ignore
from sequences.common import make_rf_se  # type: ignore
from sequences.common.util import reading_json_parameter, writing_json_parameter

log = logger.get_logger()


class AdjRFAmplitude(PulseqSequence, registry_key=Path(__file__).stem):
    @classmethod
    def get_readable_name(self) -> str:
        return "Adjust RF Amplitude  [untested]"

    def calculate_sequence(self, scan_task) -> bool:
        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"
        log.info("Calculating sequence " + self.get_name())

        make_rf_se.pypulseq_rfse(
            inputs={
                "TE": 20,
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

        # reading configuration data from config.json
        configuration_data = reading_json_parameter()

        est_rf_max, rf_pi2_fraction, data_dict = rf_max_cal(
            seq_file=self.seq_file_path,
            larmor_freq=cfg.LARMOR_FREQ,
            points=20,
            iterations=2,
            zoom_factor=2,
            shim_x=cfg.SHIM_X,
            shim_y=cfg.SHIM_Y,
            shim_z=cfg.SHIM_Z,
            tr_spacing=2,
            force_tr=False,
            first_max=False,
            smooth=True,
            plot=True,
            gui_test=False,
        )

        # updating the Larmor frequency in the config.json file
        configuration_data.rf_parameters.rf_maximum_amplitude_Hze = est_rf_max
        configuration_data.rf_parameters.rf_pi2_fraction = rf_pi2_fraction
        writing_json_parameter(config_data=configuration_data)

        log.info("Done running sequence " + self.get_name())
        return True
