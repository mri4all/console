import os
from pathlib import Path
import math

from PyQt5 import uic
import numpy as np
import pickle

import pypulseq as pp  # type: ignore

from external.seq.adjustments_acq.scripts import run_pulseq

# from external.seq.adjustments_acq.util import reading_json_parameter
import external.seq.adjustments_acq.config as cfg
import matplotlib.pyplot as plt
from sequences import PulseqSequence
from external.seq.adjustments_acq.calibration import run_sequence_test
from common.types import ResultItem

import common.logger as logger

log = logger.get_logger()


class SequenceRFTSE(PulseqSequence, registry_key=Path(__file__).stem):
    # Sequence parameters
    param_TE: int = 10
    param_ETL: int = 8

    @classmethod
    def get_readable_name(self) -> str:
        return "RF Turbo Spin-Echo"

    def setup_ui(self, widget) -> bool:
        seq_path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(f"{seq_path}/{self.get_name()}/interface.ui", widget)
        return True

    def get_parameters(self) -> dict:
        return {
            "TE": self.param_TE,
            "ETL": self.param_ETL,
        }

    @classmethod
    def get_default_parameters(self) -> dict:
        return {
            "TE": 10,
            "ETL": 8,
        }

    def set_parameters(self, parameters, scan_task) -> bool:
        self.problem_list = []
        try:
            self.param_TE = parameters["TE"]
            self.param_ETL = parameters["ETL"]
        except:
            self.problem_list.append("Invalid parameters provided")
            return False
        return self.validate_parameters(scan_task)

    def write_parameters_to_ui(self, widget) -> bool:
        widget.TESpinBox.setValue(self.param_TE)
        widget.ETLSpinBox.setValue(self.param_ETL)
        return True

    def read_parameters_from_ui(self, widget, scan_task) -> bool:
        self.problem_list = []
        self.param_TE = widget.TESpinBox.value()
        self.param_ETL = widget.ETLSpinBox.value()
        self.validate_parameters(scan_task)
        return self.is_valid()

    def validate_parameters(self, scan_task) -> bool:
        return self.is_valid()

    def calculate_sequence(self, scan_task) -> bool:
        log.info("Calculating sequence " + self.get_name())

        scan_task.processing.recon_mode = "bypass"
        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"

        pypulseq_rftse(
            inputs={
                "TE": self.param_TE,
                "ETL": self.param_ETL,
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

        # reading configuration data from config.json
        # configuration_data=reading_json_parameter(file_name='config.json')

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
            save_msgs=False,
            gui_test=False,
            case_path=self.get_working_folder(),
        )
        scan_task.adjustment.rf.larmor_frequency = cfg.LARMOR_FREQ

        plt.clf()
        plt.title("ADC Signal")
        plt.grid(True, color="#333")
        plt.plot(np.abs(rxd))
        # if self.param_debug_plot:
        #     plt.show()

        file = open(self.get_working_folder() + "/other/rf_tse.plot", "wb")
        fig = plt.gcf()
        pickle.dump(fig, file)
        file.close()

        result = ResultItem()
        result.name = "ADC"
        result.description = "Recorded ADC signal"
        result.type = "plot"
        result.primary = True
        result.autoload_viewer = 1
        result.file_path = "other/rf_tse.plot"
        scan_task.results.append(result)

        log.info("Done running sequence " + self.get_name())
        return True


def pypulseq_rftse(inputs=None, check_timing=True, output_file="") -> bool:
    LARMOR_FREQ = cfg.LARMOR_FREQ
    RF_MAX = cfg.RF_MAX
    RF_PI2_FRACTION = cfg.RF_PI2_FRACTION
    alpha1 = cfg.DBG_FA_EXC  # flip angle
    alpha1_duration = 80e-6  # pulse duration
    alpha2 = cfg.DBG_FA_REF  # refocusing flip angle
    alpha2_duration = 80e-6  # pulse duration
    TE = inputs["TE"] / 1000  # TE = 54e-3
    # TODO: Debug -- increase TR to always have enough space
    TR = 2000e-3 + TE * inputs["ETL"]
    num_averages = 1
    adc_num_samples = 4096
    adc_duration = 6.4e-3
    ETL = inputs["ETL"]

    # ======
    # INITIATE SEQUENCE
    # ======

    seq = pp.Sequence()

    # ======
    # SET SYSTEM CONFIG TODO --> ?
    # ======

    system = pp.Opts(
        # max_grad=28,
        # grad_unit="mT/m",
        # max_slew=150,
        # slew_unit="T/m/s",
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
    rf2 = pp.make_block_pulse(
        flip_angle=alpha2 * math.pi / 180,
        duration=alpha2_duration,
        delay=100e-6,
        phase_offset=math.pi / 2,
        system=system,
        use="refocusing",
    )

    # ======
    # CALCULATE DELAYS
    # ======
    tau1 = TE / 2 - 0.5 * (pp.calc_duration(rf1) + pp.calc_duration(rf2))
    tau2 = TE / 2 - 0.5 * (pp.calc_duration(rf2) + adc_duration)
    print(tau2)
    delay_TR = TR - (ETL * TE) - (0.5 * (TE + adc_duration))
    assert np.all(tau1 >= 0)
    assert np.all(delay_TR > 0)

    # Define ADC events
    adc = pp.make_adc(
        num_samples=adc_num_samples, delay=tau2, duration=adc_duration, system=system
    )

    # ======
    # ======
    # CONSTRUCT SEQUENCE
    # ======
    # Loop over phase encodes and define sequence blocks
    for avg in range(num_averages):
        seq.add_block(rf1)
        seq.add_block(pp.make_delay(tau1))
        for echo_num in range(ETL):
            seq.add_block(rf2)
            seq.add_block(adc)  # Has a delay of tau2 in built
            seq.add_block(pp.make_delay(tau2))  # Delay before next refocusing pulse
        seq.add_block(pp.make_delay(delay_TR))

    # Check whether the timing of the sequence is correct
    if check_timing:
        ok, error_report = seq.check_timing()
        if ok:
            log.info("Timing check passed successfully")
        else:
            log.info("Timing check failed. Error listing follows:")
            [print(e) for e in error_report]

    try:
        seq.write(output_file)
        print(
            output_file
        )  # Remove this later: for locally testing if not connected to Redpitaya
        log.debug("Seq file stored")
    except:
        log.error("Could not write sequence file")
        return False

    return True
