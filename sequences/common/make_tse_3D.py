import math
import numpy as np

import pypulseq as pp  # type: ignore
import external.seq.adjustments_acq.config as cfg
from sequences.common.get_trajectory import choose_pe_order
import common.logger as logger
from sequences.common import view_traj

log = logger.get_logger()


def pypulseq_tse3D(
    inputs=None, check_timing=True, output_file="", pe_order_file="", output_folder=""
) -> bool:
    if not output_file:
        log.error("No output file specified")
        return False
    if not pe_order_file:
        log.error("No PE order file specified")
        return False

    # ======
    # DEFAULTS FROM CONFIG FILE              TODO: MOVE DEFAULTS TO UI
    # ======
    LARMOR_FREQ = cfg.LARMOR_FREQ
    RF_MAX = cfg.RF_MAX
    RF_PI2_FRACTION = cfg.RF_PI2_FRACTION

    # fovx = 140e-3  # Define FOV and resolution
    # fovy = 140e-3
    # cfovz = 140e-3
    # Nx = 70  # Targeting a resolution of 2 x 2 x 5mm3
    # Ny = 70
    # Nz = 28
    calib = 0.9

    alpha1 = calib * 90  # flip angle
    alpha1_duration = 120e-6  # pulse duration
    alpha2 = calib * 180  # refocusing flip angle
    alpha2_duration = 120e-6  # pulse duration

    prephaser_duration = 3e-3  # TODO: Need to define this behind the scenes and optimze

    TR = inputs["TR"] / 1000
    TE = inputs["TE"] / 1000
    ETL = inputs["ETL"]
    fovx = inputs["FOV"] / 1000
    fovy = inputs["FOV"] / 1000
    # DEBUG! TODO: Expose FOV in Z on UI
    fovz = inputs["FOV"] / 1000 / 2
    Nx = inputs["Base_Resolution"]
    Ny = inputs["Base_Resolution"]
    Nz = inputs["Slices"]
    dim0 = Ny
    dim1 = Nz  # TODO: remove redundancy and bind it closer to UI - next step
    num_averages = inputs["NSA"]
    orientation = inputs["Orientation"]
    visualize = inputs["view_traj"]

    BW = inputs["BW"]  # 20e3
    adc_dwell = 1 / BW
    adc_duration = Nx * adc_dwell  # 6.4e-3

    traj = inputs["Ordering"]
    # traj = "linear_up"  # TODO: add linear, hybrid trajectory

    # TODO: coordinate the orientation
    ch0 = "x"
    ch1 = "y"
    ch2 = "z"
    if orientation == "Axial":
        ch0 = "x"
        ch1 = "y"
        ch2 = "z"
        # ch0 = "y"
        # ch1 = "x"
        # ch2 = "z"
    elif orientation == "Sagittal":
        ch0 = "x"
        ch1 = "z"
        ch2 = "y"
    elif orientation == "Coronal":
        ch0 = "y"
        ch1 = "z"
        ch2 = "x"

    # ======
    # INITIATE SEQUENCE
    # ======

    seq = pp.Sequence()
    n_shots = int(
        Ny * Nz / ETL
    )  # TODO: Needs to be an int; throw exception else later; finally suggest specific values

    # ======
    # SET SYSTEM CONFIG TODO --> ?
    # ======

    # system = pp.Opts(
    #     max_grad=12,
    #     grad_unit="mT/m",
    #     max_slew=25,
    #     slew_unit="T/m/s",
    #     rf_ringdown_time=20e-6,
    #     rf_dead_time=100e-6,
    #     rf_raster_time=1e-6,
    #     adc_dead_time=20e-6,
    # )

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
    delta_kx = 1 / fovx
    delta_ky = 1 / fovy
    delta_kz = 1 / fovz
    gx = pp.make_trapezoid(
        channel=ch0, flat_area=Nx * delta_kx, flat_time=adc_duration, system=system
    )
    adc = pp.make_adc(
        num_samples=2 * Nx, duration=gx.flat_time, delay=gx.rise_time, system=system
    )

    # crusher_moment = gx.area / 2
    crusher_moment = 0

    gx_pre = pp.make_trapezoid(
        channel=ch0,
        area=gx.area / 2 + crusher_moment,
        system=system,
        duration=pp.calc_duration(gx) / 2,
    )

    gx_crush = pp.make_trapezoid(
        channel=ch0,
        area=crusher_moment,
        duration=pp.calc_duration(gx_pre),
        system=system,
    )
    gy_crush = pp.make_trapezoid(
        channel=ch1,
        area=crusher_moment,
        duration=pp.calc_duration(gx_pre),
        system=system,
    )
    gz_crush = pp.make_trapezoid(
        channel=ch2,
        area=crusher_moment,
        duration=pp.calc_duration(gx_pre),
        system=system,
    )

    pe_order = choose_pe_order(
        ndims=3,
        npe=[dim0, dim1],
        traj=traj,
        save_pe_order=True,
        save_path=pe_order_file,
    )
    npe = pe_order.shape[0]
    phase_areas0 = pe_order[:, 0] * delta_ky
    phase_areas1 = pe_order[:, 1] * delta_kz

    # Gradient spoiling -TODO: Need to see if this is really required based on data
    gx_spoil = pp.make_trapezoid(channel=ch0, area=5 * Nx * delta_kx, system=system)
    gy_spoil = pp.make_trapezoid(channel=ch1, area=5 * Nx * delta_kx, system=system)
    gz_spoil = pp.make_trapezoid(channel=ch2, area=5 * Nx * delta_kx, system=system)

    # ======
    # CALCULATE DELAYS
    # ======
    tau1 = (
        math.ceil(
            (
                TE / 2.0
                - 0.5 * (pp.calc_duration(rf1) + pp.calc_duration(rf2))
                - pp.calc_duration(gx_pre)
            )
            / seq.grad_raster_time
        )
    ) * seq.grad_raster_time

    tau2 = (
        math.ceil(
            (
                TE / 2.0
                - (
                    0.5 * pp.calc_duration(gx)
                    + 0.5 * pp.calc_duration(rf2)
                    + pp.calc_duration(gx_pre)
                )
            )
            / seq.grad_raster_time
        )
    ) * seq.grad_raster_time

    delay_TR = (
        math.ceil(
            (
                TR
                - TE * ETL
                - TE / 2
                - pp.calc_duration(gx_spoil)
                - pp.calc_duration(rf1) / 2
            )
            / seq.grad_raster_time
        )
    ) * seq.grad_raster_time

    duration_gx_pre = pp.calc_duration(gx_pre)

    assert np.all(tau1 >= 0)
    assert np.all(tau2 >= 0)
    assert np.all(delay_TR >= 0)

    dummyshots = inputs["dummy_shots"]

    # ======
    # CONSTRUCT SEQUENCE
    # ======
    # Loop over phase encodes and define sequence blocks
    for avg in range(num_averages):
        for i in range(n_shots + dummyshots):
            # rf1.phase_offset = rf_phase / 180 * np.pi  # TODO: Include later
            # adc.phase_offset = rf_phase / 180 * np.pi
            # rf_inc = divmod(rf_inc + rf_spoiling_inc, 360.0)[1]
            # rf_phase = divmod(rf_phase + rf_inc, 360.0)[1]
            if i < dummyshots:
                is_dummyshot = True
            else:
                is_dummyshot = False

            seq.add_block(rf1)
            for echo in range(ETL):
                if is_dummyshot:
                    pe_idx = 0
                else:
                    pe_idx = (ETL * (i - dummyshots)) + echo

                gy_pre = pp.make_trapezoid(
                    channel=ch1,
                    area=-1.0 * phase_areas0[pe_idx] + crusher_moment,
                    duration=pp.calc_duration(gx_pre),
                    system=system,
                )
                gz_pre = pp.make_trapezoid(
                    channel=ch2,
                    area=-1.0 * phase_areas1[pe_idx] + crusher_moment,
                    duration=pp.calc_duration(gx_pre),
                    system=system,
                )
                gy_rew = pp.make_trapezoid(
                    channel=ch1,
                    area=phase_areas0[pe_idx],
                    duration=pp.calc_duration(gx_pre),
                    system=system,
                )
                gz_rew = pp.make_trapezoid(
                    channel=ch2,
                    area=phase_areas1[pe_idx],
                    duration=pp.calc_duration(gx_pre),
                    system=system,
                )

                if echo == 0:
                    seq.add_block(gx_pre)
                    # seq.add_block(gx_pre, gy_crush, gz_crush)
                else:
                    seq.add_block(pp.make_delay(duration_gx_pre))
                    # seq.add_block(gx_crush, gy_crush, gz_crush)

                seq.add_block(pp.make_delay(tau1))
                seq.add_block(rf2)
                # seq.add_block(gx_crush, gy_pre, gz_pre)
                seq.add_block(gy_pre, gz_pre)
                seq.add_block(pp.make_delay(tau2))
                if is_dummyshot:
                    seq.add_block(gx)
                else:
                    seq.add_block(gx, adc)
                # gy_pre.amplitude = -gy_pre.amplitude
                # gz_pre.amplitude = -gz_pre.amplitude
                seq.add_block(gy_rew, gz_rew)
                seq.add_block(pp.make_delay(tau2))

            seq.add_block(gx_spoil, gy_spoil, gz_spoil)
            seq.add_block(pp.make_delay(delay_TR))

    log.info("=== Seq timing ===")
    log.info(f"Prephase: {pp.calc_duration(gx_pre)}")
    log.info(f"Readout: {pp.calc_duration(gx)}")
    log.info(f"ADC: {pp.calc_duration(adc)}")

    # Check whether the timing of the sequence is correct
    if check_timing:
        ok, error_report = seq.check_timing()
        if ok:
            log.info("Timing check passed successfully")
        else:
            log.info("Timing check failed. Error listing follows:")
            [print(e) for e in error_report]

    if visualize:
        [k_traj_adc, k_traj, t_excitation, t_refocusing, t_adc] = seq.calculate_kspace(
            spoil_val=2 * Nx * delta_kx
        )
        log.info("Completed calculating Trajectory")
        log.info("Generating plots...")
        view_traj.view_traj_3d(k_traj_adc, k_traj, output_folder)

    try:
        seq.write(output_file)
        log.debug("Seq file stored")
    except:
        log.error("Could not write sequence file")
        return False

    return True
