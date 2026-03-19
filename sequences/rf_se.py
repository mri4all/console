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
    param_TE: int = 10
    param_TR: int = 250
    param_NSA: int = 1
    param_ADC_samples: int = 512
    param_ADC_duration: int = 5120
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
            "TE": 10,
            "TR": 250,
            "NSA": 1,
            "ADC_samples": 512,
            "ADC_duration": 5120,
            "debug_plot": True,
            # "TX_Freq": 11.42,  # MHz
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

        make_rf_se.pypulseq_rfse(
            inputs={
                "TE": self.param_TE,
                "TR": self.param_TR,
                "NSA": self.param_NSA,
                "ADC_samples": self.param_ADC_samples,
                "ADC_duration": self.param_ADC_duration,
                "FA1": 90,
                "FA2": 180,
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

        rxd, _ = run_pulseq(
            seq_file=self.seq_file_path,
            rf_center=cfg.LARMOR_FREQ, # scan_task.adjustment.rf.larmor_frequency,
            # rf_center=scan_task.adjustment.rf.larmor_frequency,
            tx_t=1,
            grad_t=self.param_ADC_duration / self. param_ADC_samples,
            tx_warmup=100,
            shim_x=cfg.SHIM_X,
            shim_y=cfg.SHIM_Y,
            shim_z=cfg.SHIM_Z,
            grad_cal=False,
            save_np=False,
            save_mat=False,
            save_msgs=True,
            gui_test=False,
            case_path=self.get_working_folder(),
        )
        log.info("Pulseq ran, plotting")

        self.rxd = rxd
        log.info("Shape of rx data:", rxd.shape)
        # Compute the average
        rxd_rs = np.reshape(rxd, (int(rxd.shape[0]/self.param_NSA), self.param_NSA), order='F')
        # log.info("New shape of rx data:", rxd_rs.shape)
        rxd_avg = (np.average(rxd_rs, axis=1))
        log.info("Done running sequence " + self.get_name())
        log.info("Ran sequence at " + str(cfg.LARMOR_FREQ) + " MHz")
        log.info("Plotting figures")
        
        plt.clf()
        plt.title(f"ADC Signal")
        plt.grid(True, color="#333")
        log.info("Plotting averaged raw signal")
        dt = self.param_ADC_duration / self.param_ADC_samples
        log.info("dt: ", dt)
        log.info(self.param_ADC_duration)
        t = np.arange(0, self.param_ADC_duration, dt).T
        plt.plot(t, np.abs(rxd_avg))
        # plt.plot(np.abs(rxd_avg))
        plt.xlabel('Time [us]')
        plt.ylabel('Signal')
        
        file = open(self.get_working_folder() + "/other/adc.plot", "wb")
        fig = plt.gcf()
        pickle.dump(fig, file)
        file.close()
        result = ResultItem()
        result.name = "ADC"
        result.description = "Acquired ADC signal"
        result.type = "plot"
        result.autoload_viewer = 1
        result.file_path = "other/adc.plot"
        scan_task.results.insert(0, result)

        plt.clf()
        plt.title(f"FFT of Signal")
        recon = np.fft.fftshift(np.fft.ifft(np.fft.fftshift(rxd_avg)))
        plt.grid(True, color="#333")
        # dt is already in us so no need to convert
        df = 1 / (self.param_ADC_duration)
        f =  1e3 * np.arange(-1 / (2 * dt), 1 / (2 * dt), df).T
        log.info("df: ", df)
        log.info("f shape: ", f.shape)
        log.info("recon shape: ", recon.shape)
        plt.plot(f, np.abs(recon))
        plt.xlabel('Frequency [kHz]')    
        plt.ylabel('Signal')
        file = open(self.get_working_folder() + "/other/fft.plot", "wb")
        fig = plt.gcf()
        pickle.dump(fig, file)
        file.close()
        result = ResultItem()
        result.name = "FFT"
        result.description = "FFT of ADC signal"
        result.type = "plot"
        result.autoload_viewer = 2
        result.primary = True
        result.file_path = "other/fft.plot"
        scan_task.results.insert(1, result)

        # # Debug
        # Debug = True
        # if Debug is True:  # todo: debug mode
        #     log.info("Plotting figure now")
        #     # view_traj.view_sig(rxd)

        #     plt.clf()
        #     plt.title("ADC Signal")
        #     plt.grid(True, color="#333")
        #     plt.plot(np.abs(rxd))
        #     # if self.param_debug_plot:
        #     #     plt.show()

        #     file = open(self.get_working_folder() + "/other/rf_se.plot", "wb")
        #     fig = plt.gcf()
        #     pickle.dump(fig, file)
        #     file.close()

        #     result = ResultItem()
        #     result.name = "ADC"
        #     result.description = "Recorded ADC signal"
        #     result.type = "plot"
        #     result.primary = True
        #     result.autoload_viewer = 1
        #     result.file_path = "other/rf_se.plot"
        #     scan_task.results.append(result)

        log.info("Done running sequence " + self.get_name())
        return True
