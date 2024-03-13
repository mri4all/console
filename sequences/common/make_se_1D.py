import math
import numpy as np

import pypulseq as pp  # type: ignore
import external.seq.adjustments_acq.config as cfg

import common.logger as logger

log = logger.get_logger()


def pypulseq_1dse(
    inputs=None, check_timing=True, output_file="", rf_duration=50e-6
) -> bool:
    if not output_file:
        log.error("No output file specified")
        return False

    # ======
    # DEFAULTS FROM CONFIG FILE              TODO: MOVE DEFAULTS TO UI
    # ======
    #   ======
    rf_duration = 100e-6
    LARMOR_FREQ = cfg.LARMOR_FREQ
    RF_MAX = cfg.RF_MAX
    RF_PI2_FRACTION = cfg.RF_PI2_FRACTION
    alpha1 = cfg.DBG_FA_EXC  # flip angle
    alpha1_duration = rf_duration  # pulse duration
    alpha2 = cfg.DBG_FA_REF  # refocusing flip angle
    alpha2_duration = rf_duration  # pulse duration
    # TE = 20e-3
    # TR = 3000e-3
    # num_averages = 1
    # channel = "y"
    TR = inputs["TR"] / 1000  # ms to s
    TE = inputs["TE"] / 1000
    num_averages = inputs["NSA"]
    fov = inputs["FOV"] / 1000
    Nx = inputs["Base_Resolution"]
    BW = inputs["BW"]
    channel = inputs["Gradient"]

    # fov = 20e-3  # Define FOV and resolution - 37.5e-3
    # Nx = 250
    # BW = 64e3
    # adc_dwell = 1 / BW
    # adc_duration = 2.25e-3 # Nx * adc_dwell  # 6.4e-3
    prephaser_duration = 5e-3  # TODO: Need to define this behind the scenes and optimze
    rise_time = 250e-6  # dG = 200e-6 # Grad rise time

    # ======
    # INITIATE SEQUENCE
    # ======

    seq = pp.Sequence()

    # ======
    # SET SYSTEM CONFIG TODO --> ?
    # ======

    system = pp.Opts(
        max_grad=200,
        grad_unit="mT/m",
        max_slew=4000,
        slew_unit="T/m/s",
        # rf_ringdown_time=100e-6,
        rf_ringdown_time=20e-6,
        rf_dead_time=100e-6,
        rf_raster_time=1e-6,
        # adc_dead_time=10e-6,
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
    # readout_time = 2.5e-3 + (2 * system.adc_dead_time)
    readout_time = 8.0e-3 + (2 * system.adc_dead_time)
    delta_k = 1 / fov
    gx = pp.make_trapezoid(
        channel=channel,
        flat_area=Nx * delta_k,
        flat_time=readout_time,
        rise_time=rise_time,
        system=system,
    )
    gx_pre = pp.make_trapezoid(
        channel=channel,
        area=gx.area / 2,
        duration=prephaser_duration,
        rise_time=rise_time,
        system=system,
    )
    adc = pp.make_adc(
        num_samples=Nx,
        duration=gx.flat_time,
        delay=gx.rise_time,
        phase_offset=np.pi / 2,
        system=system,
    )

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

    # tau2 = (
    #     math.ceil(
    #         (
    #             TE / 2
    #             - 0.5 * (pp.calc_duration(rf2))
    #             - pp.calc_duration(gx_pre)
    #             - 2 * rise_time
    #         )
    #         / seq.grad_raster_time
    #     )
    # ) * seq.grad_raster_time  # TODO: gradient delays need to be calibrated

    tau2 = (
        math.ceil(
            (TE / 2 - 0.5 * (pp.calc_duration(rf2) + pp.calc_duration(gx)))
            / seq.grad_raster_time
        )
    ) * seq.grad_raster_time

    delay_TR = TR - TE - (0.5 * readout_time)
    assert np.all(tau1 >= 0)
    assert np.all(tau2 >= 0)
    assert np.all(delay_TR >= 0)

    # ======
    # CONSTRUCT SEQUENCE
    # ======
    # Loop over phase encodes and define sequence blocks

    # gx_pre.amplitude = 0
    # gx.amplitude = 0

    for avg in range(num_averages):
        seq.add_block(rf1)
        seq.add_block(gx_pre)
        seq.add_block(pp.make_delay(tau1))
        seq.add_block(rf2)
        seq.add_block(pp.make_delay(tau2))
        seq.add_block(gx, adc)  # Projection
        seq.add_block(pp.make_delay(delay_TR))

    # seq.plot(time_range=[0, 2*TR])
    # seq.write("se_1D_local.seq")

    # Check whether the timing of the sequence is correct
    check_timing = True
    if check_timing:
        ok, error_report = seq.check_timing()
        if ok:
            print("Timing check passed successfully")
        else:
            print("Timing check failed. Error listing follows:")
            [print(e) for e in error_report]

    log.debug(output_file)
    try:
        seq.write(output_file)
        log.debug("Seq file stored")
    except:
        log.error("Could not write sequence file")
        return False

    return True
