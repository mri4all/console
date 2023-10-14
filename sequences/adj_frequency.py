from pathlib import Path

import external.seq.adjustments_acq.config as cfg
from external.seq.adjustments_acq.calibration import larmor_cal, larmor_step_search

import common.logger as logger

from sequences import PulseqSequence
from sequences.rf_se import pypulseq_rfse


log = logger.get_logger()


class AdjFrequency(PulseqSequence, registry_key=Path(__file__).stem):
    @classmethod
    def get_readable_name(self) -> str:
        return "Adjust Frequency"

    def calculate_sequence(self) -> bool:
        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"
        log.info("Calculating sequence " + self.get_name())

        pypulseq_rfse(inputs={}, check_timing=True, output_file=self.seq_file_path)

        log.info("Done calculating sequence " + self.get_name())
        self.calculated = True
        return True

    def run_sequence(self) -> bool:
        log.info("Running sequence " + self.get_name())

        # Using external packages now: TODO: convert to classes later
        larmor_cal(
            seq_file=self.seq_file_path,
            larmor_start=cfg.LARMOR_FREQ,
            iterations=10,
            delay_s=1,
            echo_count=2,
            step_size=0.6,
            plot=False,
            shim_x=cfg.SHIM_X,
            shim_y=cfg.SHIM_Y,
            shim_z=cfg.SHIM_Z,
            gui_test=False,
        )
        larmor_step_search(
            seq_file=self.seq_file_path,
            step_search_center=cfg.LARMOR_FREQ,
            steps=30,
            step_bw_MHz=5e-3,
            plot=False,
            shim_x=cfg.SHIM_X,
            shim_y=cfg.SHIM_Y,
            shim_z=cfg.SHIM_Z,
            delay_s=1,
            gui_test=False,
        )

        log.info("Done running sequence " + self.get_name())
        return True
