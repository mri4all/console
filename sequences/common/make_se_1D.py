import math
import numpy as np
import pypulseq as pp  # type: ignore
import external.seq.adjustments_acq.config as cfg

import common.logger as logger

log = logger.get_logger()


def pypulseq_1dse(
    inputs=None, check_timing=True, output_file="", system=None, rf_duration=100e-6
):
    if not output_file:
        log.info("No output file specified")
        log.error("No output file specified")
        return False

    # ======
    # DEFAULTS FROM CONFIG FILE              TODO: MOVE DEFAULTS TO UI
    # ======
    #   ======
    # LARMOR_FREQ = cfg.LARMOR_FREQ
    # RF_MAX = cfg.RF_MAX
    # RF_PI2_FRACTION = cfg.RF_PI2_FRACTION
    alpha1 = 90  # flip angle
    alpha1_duration = rf_duration  # pulse duration
    alpha2 = 180  # refocusing flip angle
    alpha2_duration = rf_duration  # pulse duration
 
    TR = inputs["TR"] / 1000  # ms to s
    TE = inputs["TE"] / 1000
    num_averages = inputs["NSA"]
    fov = inputs["FOV"] / 1000 # mm to m
    Nx = inputs["Base_Resolution"]
    BW = inputs["BW"]
    channel = inputs["Gradient"]
    system = inputs["system"]

    
    rise_time = 250e-6  # dG = 200e-6 # Grad rise time

    # ======
    # INITIATE SEQUENCE
    # ======

    seq = pp.Sequence()

    # ======
    # SET SYSTEM CONFIG TODO --> ?
    # ======
    # if channel == "x":
    #     max_grad = cfg.GX_MAX
    # elif channel == "y":
    #     max_grad = cfg.GY_MAX
    # elif channel == "z":
    #     max_grad = cfg.GZ_MAX


    # system = pp.Opts(
    #     max_grad=max_grad,  
    #     grad_unit="Hz/m", # 
    #     max_slew=1000,
    #     slew_unit="T/m/s",
    #     #rf_ringdown_time=100e-6,
    #     rf_ringdown_time=20e-6,
    #     rf_dead_time=100e-6,
    #     rf_raster_time=1e-6,
    #     #adc_dead_time=10e-6,
    #     adc_dead_time=20e-6,
    #     grad_raster_time = adc_dwell,
    # )


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
    
    # readout_time = (Nx / BW) + (2 * system.adc_dead_time)
    readout_time = (Nx / BW)
    # readout_time = np.max([readout_time, 4e-3])  # limit readout time based on max gradient strength
    prephaser_duration = 0.5 * readout_time
    delta_k = 1 / fov   
    log.info("**Gradient max amplitude**: ", system.max_grad)
    gx = pp.make_trapezoid(
        channel=channel,
        flat_area=Nx * delta_k,
        flat_time=readout_time,
        rise_time=rise_time,
        system=system,
    )
    log.info("**Gradient amplitude**: ", gx.amplitude)

    gx_pre = pp.make_trapezoid(
        channel=channel,
        area=gx.area / 2,
        duration=prephaser_duration,
        rise_time=rise_time,
        system=system,
    )
    adc = pp.make_adc(
        num_samples=2 * Nx, # oversampling by factor 2
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

    tau2 = (
        math.ceil((TE / 2 - 0.5 * (pp.calc_duration(rf2) + pp.calc_duration(gx))) / seq.grad_raster_time)
    ) * seq.grad_raster_time

    delay_TR = TR - TE - (0.5 * readout_time)
    assert np.all(tau1 >= 0)
    assert np.all(tau2 >= 0)
    assert np.all(delay_TR >= 0)

    # ======
    # CONSTRUCT SEQUENCE
    # ======
    # Loop over phase encodes and define sequence blocks

    for avg in range(num_averages):
        seq.add_block(rf1)
        seq.add_block(gx_pre)
        seq.add_block(pp.make_delay(tau1))
        seq.add_block(rf2)
        seq.add_block(pp.make_delay(tau2))
        seq.add_block(gx, adc)  # Projection
        seq.add_block(pp.make_delay(delay_TR))

    # Check whether the timing of the sequence is correct
    check_timing = False
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
