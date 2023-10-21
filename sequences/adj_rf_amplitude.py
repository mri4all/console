from pathlib import Path

import external.seq.adjustments_acq.config as cfg
from external.seq.adjustments_acq.calibration import rf_max_cal

import common.logger as logger

from sequences import PulseqSequence  # type: ignore
from sequences.rf_se import pypulseq_rfse  # type: ignore

log = logger.get_logger()


class AdjRFAmplitude(PulseqSequence, registry_key=Path(__file__).stem):
    @classmethod
    def get_readable_name(self) -> str:
        return "Adjust RF Amplitude"

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

        rf_max_cal(
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

        log.info("Done running sequence " + self.get_name())
        return True
