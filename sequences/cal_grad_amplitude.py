from pathlib import Path

from external.seq.adjustments_acq.calibration import grad_max_cal
import external.seq.adjustments_acq.config as cfg

import common.logger as logger

from sequences import PulseqSequence
from sequences.rf_se import pypulseq_rfse


log = logger.get_logger()

#TODO: Untested. 
class CalGradAmplitude(PulseqSequence, registry_key=Path(__file__).stem):
    @classmethod
    def get_readable_name(self) -> str:
        return "Calibrate gradients (with known dimension phantom)"

    def calculate_sequence(self) -> bool:
        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"
        log.info("Calculating sequence " + self.get_name())

        pypulseq_rfse(inputs={}, check_timing=True, output_file=self.seq_file_path)

        log.info("Done calculating sequence " + self.get_name())
        self.calculated = True
        return True

    def run_sequence(self) -> bool:
        log.info("Running sequence " + self.get_name())

        grad_axes = ['x', 'y', 'z']

        for axis in grad_axes:
            print('test')
            log.info(f"Calibrating {axis} axis")
            grad_max_cal(
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
                rf_max=cfg.RF_MAX,
                trap_ramp_duration=50, 
                trap_ramp_pts=5,
                plot=True
            )

        log.info("Done running sequence " + self.get_name())
        return True