import os
from pathlib import Path
import datetime
import math
import numpy as np
from PyQt5 import uic

import matplotlib.pyplot as plt
import pickle

import pypulseq as pp  # type: ignore
import external.seq.adjustments_acq.config as cfg
from external.seq.adjustments_acq.scripts import run_pulseq
from sequences.common.get_trajectory import choose_pe_order
from sequences import PulseqSequence
from sequences.common import make_tse_3D
import common.logger as logger
from common.types import ResultItem
import common.helper as helper

log = logger.get_logger()

from common.ipc import Communicator

ipc_comm = Communicator(Communicator.ACQ)


class SequenceFID(PulseqSequence, registry_key=Path(__file__).stem):
    # Sequence parameters
    param_FA: int = 90
    param_ADC_samples: int = 4096
    param_ADC_duration: int = 6400

    @classmethod
    def get_readable_name(self) -> str:
        return "FID"

    @classmethod
    def get_description(self) -> str:
        return "Aquires the FID"

    def setup_ui(self, widget) -> bool:
        seq_path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(f"{seq_path}/{self.get_name()}/interface.ui", widget)
        return True

    def get_parameters(self) -> dict:
        return {
            "FA": self.param_FA,
            "ADC_samples": self.param_ADC_samples,
            "ADC_duration": self.param_ADC_duration,
        }

    @classmethod
    def get_default_parameters(
        self,
    ) -> dict:
        return {
            "FA": 90,
            "ADC_samples": 4096,
            "ADC_duration": 6400,
        }

    def set_parameters(self, parameters, scan_task) -> bool:
        self.problem_list = []
        try:
            self.param_FA = parameters["FA"]
            self.param_ADC_samples = parameters["ADC_samples"]
            self.param_ADC_duration = parameters["ADC_duration"]
        except:
            self.problem_list.append("Invalid parameters provided")
            return False
        return self.validate_parameters(scan_task)

    def write_parameters_to_ui(self, widget) -> bool:
        widget.FA_SpinBox.setValue(self.param_FA)
        widget.ADC_samples_SpinBox.setValue(self.param_ADC_samples)
        widget.ADC_duration_SpinBox.setValue(self.param_ADC_duration)
        return True

    def read_parameters_from_ui(self, widget, scan_task) -> bool:
        self.problem_list = []
        self.param_FA = widget.FA_SpinBox.value()
        self.param_ADC_samples = widget.ADC_samples_SpinBox.value()
        self.param_ADC_duration = widget.ADC_duration_SpinBox.value()
        self.validate_parameters(scan_task)
        return self.is_valid()

    def validate_parameters(self, scan_task) -> bool:
        return self.is_valid()

    def calculate_sequence(self, scan_task) -> bool:
        log.info("Calculating sequence " + self.get_name())
        ipc_comm.send_status(f"Calculating sequence...")

        scan_task.processing.recon_mode = "bypass"
        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"

        if not self.generate_pulseq():
            log.error("Unable to calculate sequence " + self.get_name())
            return False

        log.info("Done calculating sequence " + self.get_name())
        return True

    def run_sequence(self, scan_task) -> bool:
        log.info("Running sequence " + self.get_name())
        ipc_comm.send_status(f"Preparing scan...")

        rxd, rx_t = run_pulseq(
            seq_file=self.seq_file_path,
            rf_center=cfg.LARMOR_FREQ,
            tx_t=1,
            grad_t=10,
            tx_warmup=100,
            shim_x=0.0,
            shim_y=0.0,
            shim_z=0.0,
            grad_cal=False,
            save_np=True,
            save_mat=False,
            save_msgs=False,
            gui_test=False,
            case_path=self.get_working_folder(),
            raw_filename="raw",
        )

        log.info("Plotting results...")
        plt.clf()
        plt.title("ADC Signal")
        plt.grid(True, color="#333")
        plt.plot(np.abs(rxd))

        file = open(self.get_working_folder() + "/other/fid.plot", "wb")
        fig = plt.gcf()
        pickle.dump(fig, file)
        file.close()

        result = ResultItem()
        result.name = "ADC"
        result.description = "Recorded ADC signal"
        result.type = "plot"
        result.primary = True
        result.autoload_viewer = 1
        result.file_path = "other/fid.plot"
        scan_task.results.append(result)

        log.info("Done running sequence " + self.get_name())
        return True

    def generate_pulseq(self) -> bool:
        output_file = self.seq_file_path

        alpha1 = self.param_FA
        alpha1_duration = 200e-6

        adc_num_samples = self.param_ADC_samples
        adc_duration = self.param_ADC_duration / 1e6  # us to s

        # ======
        # INITIATE SEQUENCE
        # ======

        seq = pp.Sequence()

        # ======
        # SET SYSTEM CONFIG TODO --> ?
        # ======
        system = pp.Opts(
            max_grad=100,
            grad_unit="mT/m",
            max_slew=4000,
            slew_unit="T/m/s",
            rf_ringdown_time=20e-6,
            rf_dead_time=100e-6,
            rf_raster_time=1e-6,
            adc_dead_time=20e-6,
        )

        # ======
        # CREATE EVENTS
        # ======

        rf1 = pp.make_block_pulse(
            flip_angle=alpha1 * math.pi / 180,
            duration=alpha1_duration,
            delay=0e-6,
            system=system,
            use="excitation",
        )

        adc = pp.make_adc(
            num_samples=adc_num_samples, duration=adc_duration, delay=0, system=system
        )

        # ======
        # CONSTRUCT SEQUENCE
        # ======

        # Loop over phase encodes and define sequence blocks
        seq.add_block(rf1)
        seq.add_block(pp.make_delay(150e-6))
        seq.add_block(adc)

        # Check whether the timing of the sequence is correct
        ok, error_report = seq.check_timing()
        if ok:
            log.info("Timing check passed successfully")
        else:
            log.info("Timing check failed. Error listing follows:")
            [print(e) for e in error_report]

        try:
            seq.write(output_file)
            log.debug("Seq file stored")
        except:
            log.error("Could not write sequence file")
            return False

        return True
