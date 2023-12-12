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


class SequenceGRE_1D(PulseqSequence, registry_key=Path(__file__).stem):
    # Sequence parameters
    param_TE: int = 50
    param_TR: int = 250
    param_NSA: int = 1
    param_orientation: str = "Axial"
    param_FOV: int = 200
    param_baseresolution: int = 64
    param_BW: int = 32000
    param_dummy_shots: int = 5

    @classmethod
    def get_readable_name(self) -> str:
        return "1D Gradient Echo"

    @classmethod
    def get_description(self) -> str:
        return "Aquires 1D GRE Projection"

    def setup_ui(self, widget) -> bool:
        seq_path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(f"{seq_path}/{self.get_name()}/interface.ui", widget)
        return True

    def get_parameters(self) -> dict:
        return {
            "TE": self.param_TE,
            "TR": self.param_TR,
            "NSA": self.param_NSA,
            "orientation": self.param_orientation,
            "FOV": self.param_FOV,
            "baseresolution": self.param_baseresolution,
            "BW": self.param_BW,
            "FA": self.param_FA,
        }

    @classmethod
    def get_default_parameters(
        self,
    ) -> dict:
        return {
            "TE": 15,
            "TR": 1000,
            "NSA": 1,
            "orientation": "Axial",
            "FOV": 15,
            "baseresolution": 32,
            "BW": 32000,
            "FA": 20,
        }

    def set_parameters(self, parameters, scan_task) -> bool:
        self.problem_list = []
        try:
            self.param_TE = parameters["TE"]
            self.param_TR = parameters["TR"]
            self.param_NSA = parameters["NSA"]
            self.param_orientation = parameters["orientation"]
            self.param_FOV = parameters["FOV"]
            self.param_baseresolution = parameters["baseresolution"]
            self.param_BW = parameters["BW"]
            self.param_FA = parameters["FA"]
        except:
            self.problem_list.append("Invalid parameters provided")
            return False
        return self.validate_parameters(scan_task)

    def write_parameters_to_ui(self, widget) -> bool:
        widget.TE_SpinBox.setValue(self.param_TE)
        widget.TR_SpinBox.setValue(self.param_TR)
        widget.FA_SpinBox.setValue(self.param_FA)
        widget.NSA_SpinBox.setValue(self.param_NSA)
        widget.Orientation_ComboBox.setCurrentText(self.param_orientation)
        widget.FOV_SpinBox.setValue(self.param_FOV)
        widget.Baseresolution_SpinBox.setValue(self.param_baseresolution)
        widget.BW_SpinBox.setValue(self.param_BW)
        return True

    def read_parameters_from_ui(self, widget, scan_task) -> bool:
        self.problem_list = []
        self.param_TE = widget.TE_SpinBox.value()
        self.param_TR = widget.TR_SpinBox.value()
        self.param_NSA = widget.NSA_SpinBox.value()
        self.param_orientation = widget.Orientation_ComboBox.currentText()
        self.param_FOV = widget.FOV_SpinBox.value()
        self.param_baseresolution = widget.Baseresolution_SpinBox.value()
        self.param_BW = widget.BW_SpinBox.value()
        self.param_FA = widget.FA_SpinBox.value()
        self.validate_parameters(scan_task)
        return self.is_valid()

    def validate_parameters(self, scan_task) -> bool:
        if self.param_TE > self.param_TR:
            self.problem_list.append("TE cannot be longer than TR")
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

        file = open(self.get_working_folder() + "/other/gre_adc.plot", "wb")
        fig = plt.gcf()
        pickle.dump(fig, file)
        file.close()

        result = ResultItem()
        result.name = "ADC"
        result.description = "Recorded ADC signal"
        result.type = "plot"
        result.primary = True
        result.autoload_viewer = 1
        result.file_path = "other/gre_adc.plot"
        scan_task.results.append(result)

        log.info("Done running sequence " + self.get_name())
        return True

    def generate_pulseq(self) -> bool:
        output_file = self.seq_file_path

        alpha1 = self.param_FA
        alpha1_duration = 100e-6

        TR = self.param_TR / 1000
        TE = self.param_TE / 1000
        fovx = self.param_FOV / 1000
        Nx = self.param_baseresolution
        num_averages = self.param_NSA
        orientation = self.param_orientation
        BW = self.param_BW

        adc_dwell = 1 / BW
        adc_duration = Nx * adc_dwell  # 6.4e-3

        ch0 = "x"
        if orientation == "Axial":
            ch0 = "x"
        elif orientation == "Sagittal":
            ch0 = "x"
        elif orientation == "Coronal":
            ch0 = "y"

        n_shots = 1
        dummyshots = 0

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
            delay=100e-6,
            system=system,
            use="excitation",
        )

        # Define other gradients and ADC events
        delta_kx = 1 / fovx
        gx = pp.make_trapezoid(
            channel=ch0, flat_area=Nx * delta_kx, flat_time=adc_duration, system=system
        )
        adc = pp.make_adc(
            num_samples=2 * Nx, duration=gx.flat_time, delay=gx.rise_time, system=system
        )

        gx_pre = pp.make_trapezoid(
            channel=ch0,
            area=gx.area / 2,
            system=system,
        )
        gx_pre.amplitude = gx_pre.amplitude

        gx_spoil = pp.make_trapezoid(channel=ch0, area=2 * Nx * delta_kx, system=system)

        # ======
        # CALCULATE DELAYS
        # ======

        tau1 = (
            math.ceil(
                (
                    TE
                    - 0.5 * pp.calc_duration(rf1)
                    - pp.calc_duration(gx_pre)
                    - 0.5 * pp.calc_duration(gx)
                )
                / seq.grad_raster_time
            )
        ) * seq.grad_raster_time

        delay_TR = (
            math.ceil(
                (
                    TR
                    - 0.5 * pp.calc_duration(rf1)
                    - TE
                    - 0.5 * pp.calc_duration(gx)
                    - pp.calc_duration(gx_spoil)
                )
                / seq.grad_raster_time
            )
        ) * seq.grad_raster_time

        assert np.all(tau1 >= 0)
        assert np.all(delay_TR >= 0)

        # ======
        # CONSTRUCT SEQUENCE
        # ======

        rfspoil_phase = 0
        rfspoil_inc = 0
        rfspoil_incinc = 0

        # Loop over phase encodes and define sequence blocks
        for avg in range(num_averages):
            for i in range(n_shots + dummyshots):
                # rfspoil_inc = rfspoil_inc + rfspoil_incinc
                # rfspoil_phase = rfspoil_phase + rfspoil_inc
                # rfspoil_phase = np.mod(rfspoil_phase, 360.0)
                # rfspoil_inc = np.mod(rfspoil_inc, 360.0)
                # print(f"{i} = {rfspoil_phase}")

                if i < dummyshots:
                    is_dummyshot = True
                else:
                    is_dummyshot = False

                rf1.phase_offset = rfspoil_phase / 180 * math.pi
                seq.add_block(rf1)
                seq.add_block(pp.make_delay(150e-6))
                seq.add_block(adc)

                # seq.add_block(gx_pre)
                # seq.add_block(pp.make_delay(tau1))

                # if is_dummyshot:
                #     seq.add_block(gx)
                # else:
                #     adc.phase_offset = rfspoil_phase / 180 * math.pi
                #     seq.add_block(gx, adc)

                # seq.add_block(gx_spoil)
                # seq.add_block(pp.make_delay(delay_TR))

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
