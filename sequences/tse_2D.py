import os
from pathlib import Path
import math
import numpy as np
from PyQt5 import uic
import pypulseq as pp  # type: ignore
import external.seq.adjustments_acq.config as cfg
from external.seq.adjustments_acq.scripts import run_pulseq
from sequences.common.make_tse_2D import pypulseq_tse2D, pypulseq_tse2D_radial
from sequences import PulseqSequence
import common.logger as logger
from sequences.common import view_traj
from sequences.common.post_acq_process import post_acq_do

log = logger.get_logger()


class SequenceTSE_2D(PulseqSequence, registry_key=Path(__file__).stem):
    # Sequence parameters
    param_TE: int = 70
    param_TR: int = 250

    @classmethod
    def get_readable_name(self) -> str:
        return "2D Turbo Spin-Echo  [untested]"

    def setup_ui(self, widget) -> bool:
        seq_path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(f"{seq_path}/{self.get_name()}/interface.ui", widget)
        return True

    def get_parameters(self) -> dict:
        return {"TE": self.param_TE, "TR": self.param_TR}

    @classmethod
    def get_default_parameters(
        self,
    ) -> dict:
        return {"TE": 70, "TR": 250}

    def set_parameters(self, parameters, scan_task) -> bool:
        self.problem_list = []
        try:
            self.param_TE = parameters["TE"]
            self.param_TR = parameters["TR"]
        except:
            self.problem_list.append("Invalid parameters provided")
            return False
        return self.validate_parameters(scan_task)

    def write_parameters_to_ui(self, widget) -> bool:
        widget.TESpinBox.setValue(self.param_TE)
        widget.TRSpinBox.setValue(self.param_TR)
        return True

    def read_parameters_from_ui(self, widget, scan_task) -> bool:
        self.problem_list = []
        self.param_TE = widget.TESpinBox.value()
        self.param_TR = widget.TRSpinBox.value()
        self.validate_parameters(scan_task)
        return self.is_valid()

    def validate_parameters(self, scan_task) -> bool:
        if self.param_TE > self.param_TR:
            self.problem_list.append("TE cannot be longer than TR")
        log.info("Validated acquisition parameters")
        return self.is_valid()

    def calculate_sequence(self, scan_task) -> bool:
        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"
        log.info("Calculating sequence " + self.get_name())

        # ToDo: if self.trajectory == "Cartesian": # (default)
        pypulseq_tse2D(
            inputs={"TE": self.param_TE, "TR": self.param_TR},
            check_timing=True,
            output_file=self.seq_file_path,
        )
        # elif self.trajectory == "Radial":
        # pypulseq_tse2D_radial(
        #    inputs={"TE": self.param_TE, "TR": self.param_TR}, check_timing=True, output_file=self.seq_file_path
        # )

        log.info("Done calculating sequence " + self.get_name())
        self.calculated = True
        return True

    def run_sequence(self, scan_task) -> bool:
        log.info("Running sequence " + self.get_name())

        rxd, rx_t = run_pulseq(
            seq_file=self.seq_file_path,
            rf_center=cfg.LARMOR_FREQ,
            tx_t=1,
            grad_t=10,
            tx_warmup=100,
            shim_x=0,
            shim_y=0,
            shim_z=0,
            grad_cal=False,
            save_np=True,
            save_mat=False,
            save_msgs=False,
            gui_test=False,
            case_path=self.get_working_folder(),
        )

        log.info("Done running sequence " + self.get_name())

        log.info("Completing post-acquisition processes for" + self.get_name())
        # TODO: Build this sequence info object over all other places to build the JSON for recon
        seq_info = {
            "raw_file_path": self.get_working_folder() + "/rawdata/raw.npy",
            "traj_file_path": self.get_working_folder() + "/data/traj.npy",
        }
        post_acq_do(seq_info)
        log.info("Sequence completed" + self.get_name())

        return True
