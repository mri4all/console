import math
import numpy as np
import pypulseq as pp  # type: ignore
import external.seq.adjustments_acq.config as cfg
from sequences.common import view_traj
import common.logger as logger

log = logger.get_logger()


def pypulseq_se2D(
    inputs=None, check_timing=True, system=None, output_file="", output_folder="") -> bool:
    if not output_file:
        log.error("No output file specified")
        return False

    # ======
    # DEFAULTS FROM CONFIG FILE              TODO: MOVE DEFAULTS TO UI
    # ======
    rf_duration = 100e-6
    LARMOR_FREQ = cfg.LARMOR_FREQ
    RF_MAX = cfg.RF_MAX
    RF_PI2_FRACTION = cfg.RF_PI2_FRACTION
    alpha1 = 90  # flip angle
    alpha1_duration = rf_duration  # pulse duration
    alpha2 = 180  # refocusing flip angle
    alpha2_duration = rf_duration  # pulse duration
    
    TR = inputs["TR"] / 1000
    TE = inputs["TE"] / 1000
    num_averages = inputs["NSA"]
    Orientation = inputs["Orientation"]
    PE_Ordering = inputs["PE_Ordering"]
    fov = inputs["FOV"] / 1000
    Nx = inputs["Base_Resolution"]
    BW = inputs["BW"]
    visualize = inputs["view_traj"]
    system = inputs["system"]
    adc_duration = (Nx/ BW) # 6.4e-3 - compensating for the oversampling of 2x 
    readout_time = adc_duration # 8.e-3 + (2 * system.adc_dead_time)
    # readout_time = np.max([readout_time, 4e-3])  # limit readout time based on max gradient strength

    prephaser_duration = 0.5 * adc_duration # 5e-3  # TODO: Need to define this behind the scenes and optimze
    rise_time = 250e-6  # dG = 200e-6 # Grad rise time
    rf_spoiling_inc = 0

    # TODO: coordinate the orientation
    ch0 = "x"
    ch1 = "y"
    
    if Orientation == "Axial":
        ch0 = "z"
        ch1 = "x"
        system.max_grad = np.min([cfg.GX_MAX,  cfg.GZ_MAX])
    elif Orientation == "Sagittal":
        ch0 = "z"
        ch1 = "y"
        system.max_grad = np.min([cfg.GY_MAX,  cfg.GZ_MAX])
    elif Orientation == "Coronal":
        ch0 = "y"
        ch1 = "x"
        system.max_grad = np.min([cfg.GX_MAX,  cfg.GY_MAX])
    log.info('Orientation: Ch0 and Ch1', Orientation, ch0, ch1)

    # ======
    # INITIATE SEQUENCE
    # ======

    seq = pp.Sequence()

    
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
        phase_offset= math.pi / 2,
        system=system,
        use="refocusing",
    )

    # Define other gradients and ADC events
    
    delta_k = 1 / fov


    gx = pp.make_trapezoid(
        channel=ch0,
        flat_area=Nx * delta_k,
        flat_time=readout_time,
        rise_time=rise_time,
        system=system,
    )

    
    gx_pre = pp.make_trapezoid(
        channel=ch0,
        area=gx.area / 2,
        duration=prephaser_duration,
        rise_time=rise_time,
        system=system,
    )
    gx_rew = pp.make_trapezoid(
        channel=ch0,
        area=-gx.area / 2,
        duration=prephaser_duration,
        rise_time=rise_time,
        system=system,
    )

    adc = pp.make_adc(
        num_samples= 2 * Nx,
        duration=gx.flat_time,
        delay=gx.rise_time,
        phase_offset= math.pi / 2,
        system=system,
    )


    # Ny = int(Nx * 2) # 2 oversampling in phase direction
    Ny = Nx # 
    phase_areas = -(np.arange(Ny) - Ny / 2) * delta_k 

    # Generate phase areas for inside-out ordering
    if PE_Ordering == "Center_out":
        phase_areas = np.zeros(Ny)
        pe_table = np.zeros(Ny, dtype=int)
        center_index = Ny // 2

        for i in range(Ny - 1):
            if i % 2 == 0:
                phase_areas[i] = -(i // 2) * delta_k
                pe_table[i] = center_index - (i // 2)
            else:
                phase_areas[i] = (i // 2 + 1) * delta_k
                pe_table[i] = center_index + (i // 2 + 1)

        log.info("Phase encoding table created for inside-out ordering")


    # Gradient spoiling -TODO: Need to see if this is really required based on data
    # gx_spoil = pp.make_trapezoid(channel=ch0, area=2 * Nx * delta_k, system=system)

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

    delay_TR = TR - TE - (0.5 * readout_time)- pp.calc_duration(gx_pre)
    assert np.all(tau1 >= 0)
    assert np.all(tau2 >= 0)
    # assert np.all(delay_TR >= pp.calc_duration(gx_spoil))

    # ======
    # CONSTRUCT SEQUENCE
    # ======
    # Loop over phase encodes and define sequence blocks
    dummy_scans = 0
    for dummy in range(dummy_scans):
        seq.add_block(rf1)
        seq.add_block(pp.make_delay(TR))

    rf_phase = rf1.phase_offset
    rf_inc = 0

    for avg in range(num_averages):
        for i in range(Ny):
            rf1.phase_offset = rf_phase / 180 * np.pi  # TODO: Include later
            adc.phase_offset = rf_phase / 180 * np.pi
            rf_inc = divmod(rf_inc + rf_spoiling_inc, 360.0)[1]
            rf_phase = divmod(rf_phase + rf_inc, 360.0)[1]
            
            seq.add_block(rf1)
            gy_pre = pp.make_trapezoid(
                channel=ch1,
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
            # seq.add_block(gx_spoil, gy_pre)  # TODO: Figure if we need spoiling
            seq.add_block(gy_pre, gx_rew)  # TODO: Figure if we need spoiling
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
        log.info("Completed calculating Trajectory")
        log.info("Generating plots...")
        view_traj.view_traj_2d(k_traj_adc, k_traj, output_folder)

    # Save sequence
    log.debug(output_file)
    try:
        seq.write(output_file)
        log.debug("Seq file stored")
    except:
        log.error("Could not write sequence file")
        return False

    return True


# implement 2D radial Trajectory
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
        max_grad=400,
        grad_unit="mT/m",
        max_slew=4000,
        slew_unit="T/m/s",
        rf_ringdown_time=100e-6,
        rf_dead_time=100e-6,
        rf_raster_time=1e-6,
        adc_dead_time=10e-6,
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
    delta_k = 1 / fov  # frequency-oversampling is not implemented - 2 * fov rather than fov 
    gx = pp.make_trapezoid(
        channel=ch0, flat_area=Nx * delta_k, flat_time=adc_duration, system=system
    )
    gy = pp.make_trapezoid(
        channel=ch1, flat_area=Nx * delta_k, flat_time=adc_duration, system=system
    )
    adc = pp.make_adc(
        num_samples=Nx, duration=gx.flat_time, delay=gx.rise_time, system=system
    )
    gx_pre = pp.make_trapezoid(
        channel=ch0, area=gx.area / 2, duration=prephaser_duration, system=system
    )
    gy_pre = pp.make_trapezoid(
        channel=ch1, area=gy.area / 2, duration=prephaser_duration, system=system
    )

    amp_pre_max = gx_pre.amplitude
    amp_enc_max = gx.amplitude

    # Gradient spoiling -TODO: Need to see if this is really required based on data
    # gx_spoil = pp.make_trapezoid(channel=ch0, area=2 * Nx * delta_k, system=system)
    # gy_spoil = pp.make_trapezoid(channel=ch1, area=2 * Nx * delta_k, system=system)

    # gx_spoil = pp.make_trapezoid(channel=ch0, area=0.2 * Nx * delta_k, system=system)
    # gy_spoil = pp.make_trapezoid(channel=ch1, area=0.2 * Nx * delta_k, system=system)

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
                # - np.max(pp.calc_duration(gx_spoil, gx_pre))
                - np.max(pp.calc_duration(gx_pre, gx_pre))
            )
            / seq.grad_raster_time
        )
    ) * seq.grad_raster_time
    assert np.all(tau1 >= 0)
    assert np.all(tau2 >= 0)
    # assert np.all(delay_TR >= pp.calc_duration(gx_spoil))

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
            # seq.add_block(gx_spoil, gy_spoil)  # TODO: Figure if we need spoiling
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
