import os
from pathlib import Path
import math
import numpy as np
import matplotlib.pyplot as plt
from PyQt5 import uic

import pypulseq as pp  # type: ignore
import external.seq.adjustments_acq.config as cfg
from external.seq.adjustments_acq.scripts import run_pulseq

from sequences import PulseqSequence
from sequences import make_se_2D
from sequences.common import view_traj
import common.logger as logger

log = logger.get_logger()


class SequenceSE_2D(PulseqSequence, registry_key=Path(__file__).stem):
    # Sequence parameters
    param_TE: int = 70
    param_TR: int = 250
    param_NSA: int = 1
    param_FOV: int = 140
    param_Orientation: str = "Axial"
    param_Base_Resolution: int = 70
    param_BW: int = 32e3
    param_Trajectory: str = "Catisian"
    param_PE_Ordering: str = "Center_out"
    param_PF: int = 1 
    

    @classmethod
    def get_readable_name(self) -> str:
        return "2D Spin-Echo"

    def setup_ui(self, widget) -> bool:
        seq_path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(f"{seq_path}/{self.get_name()}/interface.ui", widget)
        return True

    def get_parameters(self) -> dict:
        return {"TE": self.param_TE, 
        "TR": self.param_TR, 
        "NSA": self.param_NSA, 
        "FOV": self.param_FOV,
        "Orientation":self.param_Orientation,
        "Base_Resolution": self.param_Base_Resolution,
        "BW":self.param_BW,
        "Trajectory":self.param_Trajectory,
        "PE_Ordering":self.param_PE_Ordering,
        "PF": self.param_PF}

    @classmethod
    def get_default_parameters(self) -> dict:
        return {"TE": 70, "TR": 250,
                "NSA": 1, 
                "FOV": 140,
                "Orientation":"Axial",
                "Base_Resolution": 70,
                "BW":20,
                "Trajectory":"Cartesian",
                "PE_Ordering":"Center_out",
                "PF": 1
                }

    def set_parameters(self, parameters, scan_task) -> bool:
        self.problem_list = []
        try:
            self.param_TE = parameters["TE"]
            self.param_TR = parameters["TR"]
            self.param_NSA = parameters["NSA"]
            self.param_FOV = parameters["FOV"]
            self.param_Orientation = parameters["Orientation"]
            self.param_Base_Resolution = parameters["Base_Resolution"]
            self.param_BW = parameters["BW"]
            self.param_Trajectory = parameters["Trajectory"]
            self.param_PE_Ordering = parameters["PE_Ordering"]
            self.param_PF = parameters["PF"]
        except:
            self.problem_list.append("Invalid parameters provided")
            return False
        return self.validate_parameters(scan_task)

    def write_parameters_to_ui(self, widget) -> bool:
        widget.TESpinBox.setValue(self.param_TE)
        widget.TRSpinBox.setValue(self.param_TR)
        widget.NSA_SpinBox.setValue(self.param_NSA)
        widget.Orientation_ComboBox.setCurrentText(self.param_Orientation)
        widget.FOV_SpinBox.setValue(self.param_FOV)
        widget.Base_Resolution_SpinBox.setValue(self.param_Base_Resolution)
        widget.BW_SpinBox.setValue(self.param_BW)
        widget.Trajectory_ComboBox.setCurrentText(self.param_Trajectory)
        widget.PE_Ordering_ComboBox.setCurrentText(self.param_PE_Ordering)
        widget.PF_SpinBox.setValue(self.param_PF)

        return True

    def read_parameters_from_ui(self, widget, scan_task) -> bool:
        self.problem_list = []
        self.param_TE = widget.TESpinBox.value()
        self.param_TR = widget.TRSpinBox.value()
        self.param_NSA = widget.NSA_SpinBox.value()
        self.param_Orientation = widget.Orientation_ComboBox.currentText()
        self.param_FOV = widget.FOV_SpinBox.value()
        self.param_Base_Resolution = widget.Base_Resolution_SpinBox.value()
        self.param_BW = widget.BW_SpinBox.value()
        self.param_Trajectory = widget.Trajectory_ComboBox.currentText()
        self.param_PE_Ordering = widget.PE_Ordering_ComboBox.currentText()
        self.param_PF = widget.PF_SpinBox.value()
        self.validate_parameters(scan_task)
        return self.is_valid()

    def validate_parameters(self, scan_task) -> bool:
        if self.param_TE > self.param_TR:
            self.problem_list.append("TE cannot be longer than TR")
        return self.is_valid()

    def calculate_sequence(self, scan_task) -> bool:
        self.seq_file_path = self.get_working_folder() + "/seq/acq0.seq"
        log.info("Calculating sequence " + self.get_name())

        # ToDo: if self.Trajectory == "Cartesian": (default)
        make_se_2D.pypulseq_se2D(
            inputs={"TE": self.param_TE, "TR": self.param_TR, 
                    "NSA": self.param_NSA, 
                    "FOV": self.param_FOV,
                    "Orientation":self.param_Orientation,
                    "Base_Resolution": self.param_Base_Resolution,
                    "BW":self.param_BW,
                    "Trajectory":self.param_Trajectory,
                    "PE_Ordering":self.param_PE_Ordering,
                    "PF": self.param_PF},
            check_timing=True,
            output_file=self.seq_file_path,
        )
        # elif self.Trajectory == "Radial":
        # pypulseq_se2D_radial(
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
            save_np=False,
            save_mat=False,
            save_msgs=False,
            gui_test=False,
        )

        log.info("Done running sequence " + self.get_name())

        # test for recon testing
        data = rxd.reshape((70, 70))
        plt.figure()
        plt.subplot(131)
        plt.imshow(np.abs(data))
        plt.title("kspace, abs")
        plt.subplot(132)
        plt.imshow(np.real(data))
        plt.title("real")
        plt.subplot(133)
        plt.imshow(np.imag(data))
        plt.title("imag")
        plt.show()

        img = np.fft.fft2(data)
        plt.figure()
        plt.subplot(131)
        plt.imshow(np.abs(img))
        plt.title("image, abs")
        plt.subplot(132)
        plt.imshow(np.real(img))
        plt.title("real")
        plt.subplot(133)
        plt.imshow(np.imag(img))
        plt.title("imag")
        plt.show()

        return True


def pypulseq_se2D(
    inputs=None, check_timing=True, output_file="", visualize=True
) -> bool:
    if not output_file:
        log.error("No output file specified")
        return False

    # ======
    # DEFAULTS FROM CONFIG FILE              TODO: MOVE DEFAULTS TO UI
    # ======
    LARMOR_FREQ = cfg.LARMOR_FREQ
    RF_MAX = cfg.RF_MAX
    RF_PI2_FRACTION = cfg.RF_PI2_FRACTION

    fov = 140e-3  # Define FOV and resolution
    Nx = 70
    Ny = Nx
    alpha1 = 90  # flip angle
    alpha1_duration = 100e-6  # pulse duration
    alpha2 = 180  # refocusing flip angle
    alpha2_duration = 100e-6  # pulse duration
    num_averages = 1
    BW = 32e3
    adc_dwell = 1 / BW
    adc_duration = Nx * adc_dwell  # 6.4e-3
    prephaser_duration = 3e-3  # TODO: Need to define this behind the scenes and optimze

    TR = inputs["TR"] / 1000
    TE = inputs["TE"] / 1000
    num_averages = inputs['NSA']
    Orientation = inputs['Orientation']
    fov = inputs['FOV']
    base_resolution = inputs['Base_Resolution']
    BW = inputs['BW']
    Trajectory = inputs['Trajectory']
    PE_Ordering = inputs['PE_Ordering']
    PF = inputs['PF']

    # ======
    # INITIATE SEQUENCE
    # ======

    seq = pp.Sequence()

    # ======
    # SET SYSTEM CONFIG TODO --> ?
    # ======

    system = pp.Opts(
        max_grad=12,
        grad_unit="mT/m",
        max_slew=25,
        slew_unit="T/m/s",
        rf_ringdown_time=20e-6,
        rf_dead_time=100e-6,
        rf_raster_time=1e-6,
        adc_dead_time=20e-6,
    )

    # ======
    # CREATE EVENTS
    # ======
    # Create non-selective RF pulses for excitation and refocusing
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

    # Define other gradients and ADC events
    delta_k = 1 / fov
    gx = pp.make_trapezoid(
        channel="x", flat_area=Nx * delta_k, flat_time=adc_duration, system=system
    )
    adc = pp.make_adc(
        num_samples=Nx, duration=gx.flat_time, delay=gx.rise_time, system=system
    )
    gx_pre = pp.make_trapezoid(
        channel="x", area=gx.area / 2, duration=prephaser_duration, system=system
    )

    phase_areas = -(np.arange(Ny) - Ny / 2) * delta_k

    # Gradient spoiling -TODO: Need to see if this is really required based on data
    gx_spoil = pp.make_trapezoid(channel="x", area=2 * Nx * delta_k, system=system)

    # ======
    # CALCULATE DELAYS
    # ======
    tau1 = (
        math.ceil(
            (
                TE / 2
                - 0.5 * (pp.calc_duration(rf1) + pp.calc_duration(rf2))
                - pp.calc_duration(gx_pre)
            )
            / seq.grad_raster_time
        )
    ) * seq.grad_raster_time

    tau2 = (
        math.ceil(
            (TE / 2 - 0.5 * (pp.calc_duration(rf2)) - pp.calc_duration(gx_pre))
            / seq.grad_raster_time
        )
    ) * seq.grad_raster_time

    delay_TR = (
        math.ceil(
            (
                TR
                - TE
                - pp.calc_duration(gx_pre)
                - np.max(pp.calc_duration(gx_spoil, gx_pre))
            )
            / seq.grad_raster_time
        )
    ) * seq.grad_raster_time
    assert np.all(tau1 >= 0)
    assert np.all(tau2 >= 0)
    assert np.all(delay_TR >= pp.calc_duration(gx_spoil))

    # ======
    # CONSTRUCT SEQUENCE
    # ======
    # Loop over phase encodes and define sequence blocks
    for avg in range(num_averages):
        for i in range(Ny):
            # rf1.phase_offset = rf_phase / 180 * np.pi  # TODO: Include later
            # adc.phase_offset = rf_phase / 180 * np.pi
            # rf_inc = divmod(rf_inc + rf_spoiling_inc, 360.0)[1]
            # rf_phase = divmod(rf_phase + rf_inc, 360.0)[1]
            seq.add_block(rf1)
            gy_pre = pp.make_trapezoid(
                channel="y",
                area=phase_areas[i],
                duration=pp.calc_duration(gx_pre),
                system=system,
            )
            seq.add_block(gx_pre, gy_pre)
            seq.add_block(pp.make_delay(tau1))
            seq.add_block(rf2)
            seq.add_block(pp.make_delay(tau2))
            seq.add_block(gx, adc)
            gy_pre.amplitude = -gy_pre.amplitude
            seq.add_block(gx_spoil, gy_pre)  # TODO: Figure if we need spoiling
            seq.add_block(pp.make_delay(delay_TR))

    # Check whether the timing of the sequence is correct
    if check_timing:
        ok, error_report = seq.check_timing()
        if ok:
            log.info("Timing check passed successfully")
        else:
            log.info("Timing check failed. Error listing follows:")
            [print(e) for e in error_report]

    # Visualize Trajectory and other things
    if visualize:
        [k_traj_adc, k_traj, t_excitation, t_refocusing, t_adc] = seq.calculate_kspace(spoil_val=2 * Nx * delta_k)
        log.info("Completed calculating trajectory")
        log.info("Generating plots...")
        view_traj.view_traj_2d(k_traj_adc, k_traj)

    # Save sequence
    log.debug(output_file)
    try:
        seq.write(output_file)
        log.debug("Seq file stored")
    except:
        log.error("Could not write sequence file")
        return False

    return True


# implement 2D radial Trajectory (Ruoxun Zi)
def pypulseq_se2D_radial(inputs=None, check_timing=True, output_file="") -> bool:
    if not output_file:
        log.error("No output file specified")
        return False

    # ======
    # DEFAULTS FROM CONFIG FILE              TODO: MOVE DEFAULTS TO UI
    # ======
    LARMOR_FREQ = cfg.LARMOR_FREQ
    RF_MAX = cfg.RF_MAX
    RF_PI2_FRACTION = cfg.RF_PI2_FRACTION

    fov = 140e-3  # Define FOV and resolution
    Nx = 70
    Ny = Nx
    Nspokes = math.ceil(Nx * math.pi / 2)
    alpha1 = 90  # flip angle
    alpha1_duration = 100e-6  # pulse duration
    alpha2 = 180  # refocusing flip angle
    alpha2_duration = 100e-6  # pulse duration
    num_averages = 1
    BW = 20e3
    adc_dwell = 1 / BW
    adc_duration = Nx * adc_dwell  # 6.4e-3
    prephaser_duration = 3e-3  # TODO: Need to define this behind the scenes and optimze

    TR = inputs["TR"] / 1000
    TE = inputs["TE"] / 1000
    spoke_inc = "golden_angle"  # TODO: get from UI: GA or linear increment over 180

    # ======
    # INITIATE SEQUENCE
    # ======

    seq = pp.Sequence()

    # ======
    # SET SYSTEM CONFIG TODO --> ?
    # ======

    system = pp.Opts(
        max_grad=12,
        grad_unit="mT/m",
        max_slew=25,
        slew_unit="T/m/s",
        rf_ringdown_time=20e-6,
        rf_dead_time=100e-6,
        rf_raster_time=1e-6,
        adc_dead_time=20e-6,
    )

    # ======
    # CREATE EVENTS
    # ======
    # Create non-selective RF pulses for excitation and refocusing
    rf1 = pp.make_block_pulse(
        flip_angle=alpha1 * math.pi / 180,
        duration=alpha1_duration,
        delay=100e-6,
        system=system,
    )
    rf2 = pp.make_block_pulse(
        flip_angle=alpha2 * math.pi / 180,
        duration=alpha2_duration,
        delay=100e-6,
        phase_offset=math.pi / 2,
        system=system,
    )

    # Define other gradients and ADC events
    delta_k = 1 / fov  # frequency-oversampling is not implemented
    gx = pp.make_trapezoid(
        channel="x", flat_area=Nx * delta_k, flat_time=adc_duration, system=system
    )
    gy = pp.make_trapezoid(
        channel="y", flat_area=Nx * delta_k, flat_time=adc_duration, system=system
    )
    adc = pp.make_adc(
        num_samples=Nx, duration=gx.flat_time, delay=gx.rise_time, system=system
    )
    gx_pre = pp.make_trapezoid(
        channel="x", area=gx.area / 2, duration=prephaser_duration, system=system
    )
    gy_pre = pp.make_trapezoid(
        channel="y", area=gy.area / 2, duration=prephaser_duration, system=system
    )

    amp_pre_max = gx_pre.amplitude
    amp_enc_max = gx.amplitude

    # Gradient spoiling -TODO: Need to see if this is really required based on data
    gx_spoil = pp.make_trapezoid(channel="x", area=2 * Nx * delta_k, system=system)
    gy_spoil = pp.make_trapezoid(channel="y", area=2 * Nx * delta_k, system=system)

    # ======
    # CALCULATE DELAYS
    # ======
    tau1 = (
        math.ceil(
            (
                TE / 2
                - 0.5 * (pp.calc_duration(rf1) + pp.calc_duration(rf2))
                - pp.calc_duration(gx_pre)
            )
            / seq.grad_raster_time
        )
    ) * seq.grad_raster_time

    tau2 = (
        math.ceil(
            (TE / 2 - 0.5 * (pp.calc_duration(rf2)) - pp.calc_duration(gx_pre))
            / seq.grad_raster_time
        )
    ) * seq.grad_raster_time

    delay_TR = (
        math.ceil(
            (
                TR
                - TE
                - pp.calc_duration(gx_pre)
                - np.max(pp.calc_duration(gx_spoil, gx_pre))
            )
            / seq.grad_raster_time
        )
    ) * seq.grad_raster_time
    assert np.all(tau1 >= 0)
    assert np.all(tau2 >= 0)
    assert np.all(delay_TR >= pp.calc_duration(gx_spoil))

    # ======
    # CONSTRUCT SEQUENCE
    # ======
    # Loop over phase encodes and define sequence blocks
    for avg in range(num_averages):
        for i in range(Nspokes):
            # rf1.phase_offset = rf_phase / 180 * np.pi  # TODO: Include later
            # adc.phase_offset = rf_phase / 180 * np.pi
            # rf_inc = divmod(rf_inc + rf_spoiling_inc, 360.0)[1]
            # rf_phase = divmod(rf_phase + rf_inc, 360.0)[1]
            seq.add_block(rf1)
            if spoke_inc == "linear_increment":
                phi = i * (math.pi / Nspokes)
            elif spoke_inc == "golden_angle":
                phi = i * (111.246117975 / 180 * math.pi)
            gx_pre.amplitude = amp_pre_max * math.sin(phi)
            gy_pre.amplitude = amp_pre_max * math.cos(phi)
            seq.add_block(gx_pre, gy_pre)
            seq.add_block(pp.make_delay(tau1))
            seq.add_block(rf2)
            seq.add_block(pp.make_delay(tau2))
            gx.amplitude = amp_enc_max * math.sin(phi)
            gy.amplitude = amp_enc_max * math.cos(phi)
            seq.add_block(gx, gy, adc)
            seq.add_block(gx_spoil, gy_spoil)  # TODO: Figure if we need spoiling
            seq.add_block(pp.make_delay(delay_TR))
        seq.plot(time_range=[0, 3 * TR])

    # Check whether the timing of the sequence is correct
    if check_timing:
        ok, error_report = seq.check_timing()
        if ok:
            log.info("Timing check passed successfully")
        else:
            log.info("Timing check failed. Error listing follows:")
            [print(e) for e in error_report]

    log.debug(output_file)
    try:
        seq.write(output_file)
        log.debug("Seq file stored")
    except:
        log.error("Could not write sequence file")
        return False

    return True
