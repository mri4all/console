from pathlib import Path

from external.seq.adjustments_acq.calibration import shim_cal
import external.seq.adjustments_acq.config as cfg

import common.logger as logger

from sequences import PulseqSequence
from sequences.rf_se import pypulseq_rfse

import configparser


log = logger.get_logger()


class CalShimAmplitude(PulseqSequence, registry_key=Path(__file__).stem):
    @classmethod
    def get_readable_name(self) -> str:
        return "Calibrate B0 shims"

    @classmethod
    def get_description(self) -> str:
        return "Adjust Shim Sequence."

    def calculate_sequence(self) -> bool:
        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"
        log.info("Calculating sequence " + self.get_name())

        pypulseq_rfse(inputs={}, check_timing=True, output_file=self.seq_file_path)

        log.info("Done calculating sequence " + self.get_name())
        self.calculated = True
        return True

    def run_sequence(self) -> bool:
        log.info("Running sequence " + self.get_name())

        shim_cal(larmor_freq=cfg.LARMOR_FREQ,
                channel='x',
                range=0.01,
                shim_points=3,
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
        
        log.info("Done running sequence " + self.get_name())
        return True
