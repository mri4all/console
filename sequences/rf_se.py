import os
from pathlib import Path
import math
import numpy as np
import matplotlib.pyplot as plt
import pickle

from common.types import ResultItem
from PyQt5 import uic

import pypulseq as pp  # type: ignore
import external.seq.adjustments_acq.config as cfg
from external.seq.adjustments_acq.scripts import run_pulseq

from sequences import PulseqSequence
from sequences.common import make_rf_se
import common.logger as logger

log = logger.get_logger()


class SequenceRF_SE(PulseqSequence, registry_key=Path(__file__).stem):
    # Sequence parameters
    param_TE: int = 70
    param_TR: int = 250
    param_NSA: int = 1
    param_ADC_samples: int = 4096
    param_ADC_duration: int = 6400
    param_debug_plot: bool = True

    @classmethod
    def get_readable_name(self) -> str:
        return "RF Spin-Echo"

    @classmethod
    def get_description(self) -> str:
        return "Acquisition of a single spin-echo without switching any gradients"

    def setup_ui(self, widget) -> bool:
        seq_path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(f"{seq_path}/{self.get_name()}/interface.ui", widget)
        return True

    def get_parameters(self) -> dict:
        return {
            "TE": self.param_TE,
            "TR": self.param_TR,
            "NSA": self.param_NSA,
            "ADC_samples": self.param_ADC_samples,
            "ADC_duration": self.param_ADC_duration,
            "debug_plot": self.param_debug_plot,
        }

    @classmethod
    def get_default_parameters(self) -> dict:
        return {
            "TE": 20,
            "TR": 250,
            "NSA": 1,
            "ADC_samples": 4096,
            "ADC_duration": 6400,
            "debug_plot": True,
        }

    def set_parameters(self, parameters, scan_task) -> bool:
        self.problem_list = []
        try:
            self.param_TE = parameters["TE"]
            self.param_TR = parameters["TR"]
            self.param_NSA = parameters["NSA"]
            self.param_ADC_samples = parameters["ADC_samples"]
            self.param_ADC_duration = parameters["ADC_duration"]
            self.param_debug_plot = parameters["debug_plot"]
        except:
            self.problem_list.append("Invalid parameters provided")
            return False
        return self.validate_parameters(scan_task)

    def write_parameters_to_ui(self, widget) -> bool:
        widget.TESpinBox.setValue(self.param_TE)
        widget.TRSpinBox.setValue(self.param_TR)
        widget.NSA_SpinBox.setValue(self.param_NSA)
        widget.ADC_samples_SpinBox.setValue(self.param_ADC_samples)
        widget.ADC_duration_SpinBox.setValue(self.param_ADC_duration)
        return True

    def read_parameters_from_ui(self, widget, scan_task) -> bool:
        self.problem_list = []
        self.param_TE = widget.TESpinBox.value()
        self.param_TR = widget.TRSpinBox.value()
        self.param_NSA = widget.NSA_SpinBox.value()
        self.param_ADC_samples = widget.ADC_samples_SpinBox.value()
        self.param_ADC_duration = widget.ADC_duration_SpinBox.value()
        self.validate_parameters(scan_task)
        return self.is_valid()

    def validate_parameters(self, scan_task) -> bool:
        if self.param_TE > self.param_TR:
            self.problem_list.append("TE cannot be longer than TR")
        return self.is_valid()

    def calculate_sequence(self, scan_task) -> bool:
        scan_task.processing.recon_mode = "bypass"

        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"
        log.info("Calculating sequence " + self.get_name())

        fa_exc = cfg.DBG_FA_EXC
        fa_ref = cfg.DBG_FA_REF
        if "FA1" in scan_task.other:
            fa_exc = int(scan_task.other["FA1"])
        if "FA2" in scan_task.other:
            fa_ref = int(scan_task.other["FA2"])

        make_rf_se.pypulseq_rfse(
            inputs={
                "TE": self.param_TE,
                "TR": self.param_TR,
                "NSA": self.param_NSA,
                "ADC_samples": self.param_ADC_samples,
                "ADC_duration": self.param_ADC_duration,
                "FA1": fa_exc,
                "FA2": fa_ref,
            },
            check_timing=True,
            output_file=self.seq_file_path,
        )

        log.info("Done calculating sequence " + self.get_name())
        self.calculated = True
        return True

    def run_sequence(self, scan_task) -> bool:
        log.info("Running sequence " + self.get_name())

        # run_sequence_test("prescan_frequency")

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
            save_np=False,
            save_mat=False,
            save_msgs=True,
            gui_test=False,
            case_path=self.get_working_folder(),
        )
        scan_task.adjustment.rf.larmor_frequency = cfg.LARMOR_FREQ

        log.info("Pulseq ran, plotting")

        self.rxd = rxd

        # Debug
        Debug = True
        if Debug is True:  # todo: debug mode
            log.info("Plotting figure now")
            # view_traj.view_sig(rxd)

            plt.clf()
            plt.title("ADC Signal")
            plt.grid(True, color="#333")
            plt.plot(np.abs(rxd))
            # if self.param_debug_plot:
            #     plt.show()

            file = open(self.get_working_folder() + "/other/rf_se.plot", "wb")
            fig = plt.gcf()
            pickle.dump(fig, file)
            file.close()

            result = ResultItem()
            result.name = "ADC"
            result.description = "Recorded ADC signal"
            result.type = "plot"
            result.primary = True
            result.autoload_viewer = 1
            result.file_path = "other/rf_se.plot"
            scan_task.results.append(result)

        log.info("Done running sequence " + self.get_name())
        return True
