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
from sequences.common import make_se_1D
import common.logger as logger
from sequences.common import view_traj

log = logger.get_logger()


class SequenceRF_SE(PulseqSequence, registry_key=Path(__file__).stem):
    # Sequence parameters
    param_TE: int = 10
    param_TR: int = 3000
    param_NSA: int = 1
    param_FOV: int = 64
    param_Base_Resolution: int = 64
    param_BW: int = 16000
    param_Gradient: str = "x"
    param_debug_plot: bool = True

    @classmethod
    def get_readable_name(self) -> str:
        return "1D Spin-Echo"

    @classmethod
    def get_description(self) -> str:
        return "Spin-Echo sequence with gradient encoding in a pre-selected direction (projection)"

    def setup_ui(self, widget) -> bool:
        seq_path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(f"{seq_path}/{self.get_name()}/interface.ui", widget)
        return True

    def get_parameters(self) -> dict:
        return {
            "TE": self.param_TE,
            "TR": self.param_TR,
            "NSA": self.param_NSA,
            "FOV": self.param_FOV,
            "Base_Resolution": self.param_Base_Resolution,
            "BW": self.param_BW,
            "Gradient": self.param_Gradient,
            "debug_plot": self.param_debug_plot,
        }

    @classmethod
    def get_default_parameters(self) -> dict:
        return {
            "TE": 5,
            "TR": 1000,
            "NSA": 1,
            "FOV": 64,
            "Base_Resolution": 64,
            "BW": 16000,
            "Gradient": "x",
        }

    def set_parameters(self, parameters, scan_task) -> bool:
        self.problem_list = []
        try:
            self.param_TE = parameters["TE"]
            self.param_TR = parameters["TR"]
            self.param_NSA = parameters["NSA"]
            self.param_FOV = parameters["FOV"]
            self.param_Base_Resolution = parameters["Base_Resolution"]
            self.param_BW = parameters["BW"]
            self.param_Gradient = parameters["Gradient"]
            self.param_debug_plot = parameters["debug_plot"]
        except:
            self.problem_list.append("Invalid parameters provided")
            return False
        return self.validate_parameters(scan_task)

    def write_parameters_to_ui(self, widget) -> bool:
        widget.TESpinBox.setValue(self.param_TE)
        widget.TRSpinBox.setValue(self.param_TR)
        widget.NSA_SpinBox.setValue(self.param_NSA)
        widget.FOV_SpinBox.setValue(self.param_FOV)
        widget.Base_Resolution_SpinBox.setValue(self.param_Base_Resolution)
        widget.BW_SpinBox.setValue(self.param_BW)
        widget.Gradient_ComboBox.setCurrentText(self.param_Gradient)
        return True

    def read_parameters_from_ui(self, widget, scan_task) -> bool:
        self.problem_list = []
        self.param_TE = widget.TESpinBox.value()
        self.param_TR = widget.TRSpinBox.value()
        self.param_NSA = widget.NSA_SpinBox.value()
        self.param_FOV = widget.FOV_SpinBox.value()
        self.param_Base_Resolution = widget.Base_Resolution_SpinBox.value()
        self.param_BW = widget.BW_SpinBox.value()
        self.param_Gradient = widget.Gradient_ComboBox.currentText()
        self.validate_parameters(scan_task)
        return self.is_valid()

    def validate_parameters(self, scan_task) -> bool:
        if self.param_TE > self.param_TR:
            self.problem_list.append("TE cannot be longer than TR")
        return self.is_valid()

    def calculate_sequence(self, scan_task)-> bool:
        log.info("Calculating sequence " + self.get_name())
        scan_task.processing.recon_mode = "bypass"
        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"

        plt.clf()
        plt.title("Sequence")
        channel = self.param_Gradient
        if channel == "x":
            max_grad = cfg.GX_MAX
        elif channel == "y":
            max_grad = cfg.GY_MAX
        elif channel == "z":
            max_grad = cfg.GZ_MAX
        
        # seq = pp.Sequence()
        self.system = pp.Opts(
            max_grad=max_grad,  
            grad_unit="Hz/m", # 
            max_slew=1000,
            slew_unit="T/m/s",
            #rf_ringdown_time=100e-6,
            rf_ringdown_time=20e-6,
            rf_dead_time=100e-6,
            rf_raster_time=1e-6,
            #adc_dead_time=10e-6,
            adc_dead_time=20e-6,
            grad_raster_time = 1/self.param_BW,
            B0=0.27,
            )
        log.info("Using system config: ", self.system)
        make_se_1D.pypulseq_1dse(
            inputs={
                "TE": self.param_TE,
                "TR": self.param_TR,
                "NSA": self.param_NSA,
                "FOV": self.param_FOV,
                "Base_Resolution": self.param_Base_Resolution,
                "BW": self.param_BW,
                "Gradient": self.param_Gradient,
                "system": self.system,
            },
            check_timing=True,
            output_file=self.seq_file_path,
        )
        
        file = open(self.get_working_folder() + "/other/seq1.plot", "wb")
        fig = plt.figure(1)
        pickle.dump(fig, file)
        file.close()
        result = ResultItem()
        result.name = "SEQ1"
        result.description = "Sequence diagram RF/ADC"
        result.type = "plot"
        result.file_path = "other/seq1.plot"
        scan_task.results.append(result)

        file = open(self.get_working_folder() + "/other/seq2.plot", "wb")
        fig = plt.figure(2)
        pickle.dump(fig, file)
        file.close()
        result = ResultItem()
        result.name = "SEQ2"
        result.description = "Sequence diagram Grad"
        result.type = "plot"
        result.file_path = "other/seq2.plot"
        scan_task.results.append(result)

        log.info("Done calculating sequence " + self.get_name())
        self.calculated = True
        return True

    def run_sequence(self, scan_task) -> bool:
        log.info("Running sequence " + self.get_name())
        rxd, _ = run_pulseq(
        seq_file=self.seq_file_path,
        rf_center=cfg.LARMOR_FREQ, #scan_task.adjustment.rf.larmor_frequency,
        tx_t=1,
        grad_t=np.round(self.system.grad_raster_time * 1e6, decimals=0), # us
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
        system = self.system
        )
    # Compute the average
        rxd_rs = np.reshape(rxd, (int(rxd.shape[0]/self.param_NSA), self.param_NSA), order='F')
        log.info("New shape of rx data:", rxd_rs.shape)
        rxd_avg = (np.average(rxd_rs, axis=1))
        filtering = False
        if filtering is True:
            rxd_avg = np.convolve(rxd_avg, np.ones(5)/5, mode='same')

        log.info("Done running sequence " + self.get_name())
        log.info("Plotting figures")
        
        plt.clf()
        plt.title(f"ADC Signal - Grad_{self.param_Gradient}")
        plt.grid(True, color="#333")
        log.info("Plotting averaged raw signal")
        dt = 1e6 / self.param_BW
        log.info("dt: ", dt)
        
        t = np.arange(0, self.param_Base_Resolution * dt * 2, dt).T # oversampling by factor 2
        plt.plot(t, np.abs(rxd_avg))
        plt.xlabel('Time (us)')
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
        plt.title(f"FFT of Signal - Grad_{self.param_Gradient}")
        recon = np.fft.fftshift(np.fft.ifft(np.fft.fftshift(rxd_avg)))
        plt.grid(True, color="#333")
        kmax_half = -self.param_Base_Resolution / self.param_FOV / 2
        k_array = np.linspace(-kmax_half, kmax_half, self.param_Base_Resolution)

        r = np.linspace(-self.param_FOV/2, self.param_FOV/2, self.param_Base_Resolution * 2)
        plt.plot(r, np.abs(recon))
        plt.xlabel("Position (mm)")
        plt.ylabel("Projection")
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

        # Save the raw data file
        log.info("Saving rawdata, sequence " + self.get_name())
        self.raw_file_path = self.get_working_folder() + "/rawdata/raw.npy"
        np.save(self.raw_file_path, rxd)

        return True
