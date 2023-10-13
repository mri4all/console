import os
from pathlib import Path
import math

from PyQt5 import uic

import pypulseq as pp
import numpy as np

from sequences import PulseqSequence
from external.seq.adjustments_acq.scripts import run_pulseq
import external.seq.adjustments_acq.config as cfg

import common.logger as logger

log = logger.get_logger()


class SequenceRFTSE(PulseqSequence, registry_key=Path(__file__).stem):
    @classmethod
    def get_readable_name(self) -> str:
        return "Radio Frequency Turbo Spin Echo"

    def setup_ui(self, widget) -> bool:
        """
        Returns the user inteface of the sequence.
        """
        seq_path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(f"{seq_path}/{self.get_name()}/interface.ui", widget)
        return True

    def pypulseq_rftse(self, ui_inputs=None, check_timing=True) -> bool:
        if len(ui_inputs) == 0:
            # ======
            # DEFAULTS              TODO: MOVE DEFAULTS TO UI
            # ======
            LARMOR_FREQ = cfg.LARMOR_FREQ
            RF_MAX = cfg.RF_MAX
            RF_PI2_FRACTION = cfg.RF_PI2_FRACTION
            alpha1 = 90  # flip angle
            alpha1_duration = 100e-6  # pulse duration
            alpha2 = 180  # refocusing flip angle
            alpha2_duration = 100e-6  # pulse duration
            TE = 54e-3
            TR = 2000e-3
            num_averages = 1
            adc_num_samples = 4096
            adc_duration = 6.4e-3
            ETL = 8
        else:
            LARMOR_FREQ = ui_inputs["LARMOR_FREQ"]
            RF_MAX = ui_inputs["RF_MAX"]
            RF_PI2_FRACTION = ui_inputs["RF_PI2_FRACTION"]
            TR = ui_inputs["TR"]
            TE = ui_inputs["TE"]

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
            flip_angle=alpha1 * math.pi / 180, duration=alpha1_duration, delay=100e-6, system=system
        )
        rf2 = pp.make_block_pulse(
            flip_angle=alpha2 * math.pi / 180,
            duration=alpha2_duration,
            delay=100e-6,
            phase_offset=math.pi / 2,
            system=system,
        )

        # ======
        # CALCULATE DELAYS
        # ======
        tau1 = TE / 2 - 0.5 * (pp.calc_duration(rf1) + pp.calc_duration(rf2))
        tau2 = TE / 2 - 0.5 * (pp.calc_duration(rf2) + adc_duration)
        print(tau2)
        delay_TR = TR - (ETL * TE) - (0.5 * TE)
        assert np.all(tau1 >= 0)
        assert np.all(delay_TR > 0)

        # Define ADC events
        adc = pp.make_adc(num_samples=adc_num_samples, delay=tau2, duration=adc_duration, system=system)

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
                seq.add_block(pp.make_delay(tau2))
            seq.add_block(pp.make_delay(delay_TR))

        # Check whether the timing of the sequence is correct
        if check_timing:
            ok, error_report = seq.check_timing()
            if ok:
                log.info("Timing check passed successfully")
            else:
                log.info("Timing check failed. Error listing follows:")
                [print(e) for e in error_report]

        # seq.write('rfse.seq')
        seq_file_path = self.store_seq_file(file_name="rftse.seq", seq=seq)
        log.info("Seq file stored")
        return seq_file_path

    def run(self) -> bool:
        log.info("Starting to build sequence Radio Frequency Turbo Spin Echo")
        seq_file_path = self.pypulseq_rftse(ui_inputs={}, check_timing=True)  # Change when UI is ready
        rxd, rx_t = run_pulseq(
            seq_file=seq_file_path,
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
        )
        log.info("Completed executing sequence: RFTSE")
        return True


if __name__ == "__main__":
    test_instance = SequenceRFTSE()
    test_instance.run()
