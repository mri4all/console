import os
from pathlib import Path
from PyQt5 import uic
import math
import sys
sys.path.insert(0, '.')
import os
from sequences import SequenceBase
import pypulseq as pp
from external.seq.adjustments_acq.scripts import run_pulseq
import external.seq.adjustments_acq.config as cfg
import numpy as np
import uuid 
import common.logger as logger
from sequences.rfse import SequenceRFSE
from external.seq.adjustments_acq.calibration import larmor_cal, larmor_step_search
log = logger.get_logger()


class AdjFrequency(SequenceBase, registry_key=Path(__file__).stem):
    @classmethod
    def get_readable_name(self) -> str:
        return "Radio Frequency Spin Echo"

    def setup_ui(self, widget) -> bool:
        """
        Returns the user inteface of the sequence.
        """
        seq_path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(f"{seq_path}/{self.get_name()}/interface.ui", widget)
        return True

    def run() -> bool:
        log.info('Starting to find Larmor frequency in coarse and fine modes')
        ui_inputs = SequenceBase.read_parameters_from_ui('AdjFrequency')
        seq_file_path = SequenceRFSE.pypulseq_rfse(ui_inputs={}, check_timing=True)  # Change when UI is ready
        # Using external packages now: TODO: convert to classes later
        larmor_cal(seq_file=seq_file_path,larmor_start=cfg.LARMOR_FREQ, iterations=10, delay_s=1, echo_count=2,
               step_size=0.6, plot=False, shim_x=cfg.SHIM_X, shim_y=cfg.SHIM_Y, shim_z=cfg.SHIM_Z, gui_test=False)
        larmor_step_search(seq_file=seq_file_path, step_search_center=cfg.LARMOR_FREQ, steps=30, step_bw_MHz=5e-3, plot=False,
                       shim_x=cfg.SHIM_X, shim_y=cfg.SHIM_Y, shim_z=cfg.SHIM_Z, delay_s=1, gui_test=False)
        log.info("Completed executing adjustment: Larmor Frequency")
        return True
        
if __name__ == "__main__":
    AdjFrequency.run()