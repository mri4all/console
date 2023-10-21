from pathlib import Path

from external.seq.adjustments_acq.calibration import grad_max_cal
import external.seq.adjustments_acq.config as cfg

import common.logger as logger

from sequences import PulseqSequence  # type: ignore
from sequences.rf_se import pypulseq_rfse  # type: ignore
from sequences.common.util import reading_json_parameter, writing_json_parameter

import configparser

log = logger.get_logger()


# TODO: Untested.
class CalGradAmplitude(PulseqSequence, registry_key=Path(__file__).stem):
    @classmethod
    def get_readable_name(self) -> str:
        return "Calibrate Gradients"

    @classmethod
    def get_description(self) -> str:
        return "Service sequence to calibrate the gradients using a phantom with known dimensions."

    def calculate_sequence(self, scan_task) -> bool:
        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"
        log.info("Calculating sequence " + self.get_name())

        pypulseq_rfse(inputs={"TE":70, "TR":250, "NSA":1, "ADC_samples": 4096, \
                              "ADC_duration": 6400}, check_timing=True, output_file=self.seq_file_path)

        log.info("Done calculating sequence " + self.get_name())
        self.calculated = True
        return True

    def run_sequence(self, scan_task) -> bool:
        log.info("Running sequence " + self.get_name())

        # reading configuration data from config.json
        configuration_data=reading_json_parameter()

        grad_axes = ["x", "y", "z"]
        iter = 20
        for iterations in range(iter):
            for axis in grad_axes:
                print("test")
                log.info(f"Calibrating {axis} axis")
                grad_max = grad_max_cal(
                    channel=axis,
                    phantom_width=10,
                    larmor_freq=cfg.LARMOR_FREQ,
                    calibration_power=0.8,
                    trs=3,
                    tr_spacing=2e6,
                    echo_duration=5000,
                    readout_duration=500,
                    rx_period=25 / 3,
                    RF_PI2_DURATION=50,
                    rf_max=RF_MAX,
                    trap_ramp_duration=50,
                    trap_ramp_pts=5,
                    plot=True,
                )

        # updating the Larmor frequency in the config.json file
        configuration_data.rf_parameters.rf_maximum_amplitude_Hze = grad_max
        writing_json_parameter(config_data=configuration_data)

        log.info("Done running sequence " + self.get_name())
        return True
