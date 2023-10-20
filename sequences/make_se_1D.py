import math
import numpy as np

import pypulseq as pp  # type: ignore
import external.seq.adjustments_acq.config as cfg
from external.seq.adjustments_acq.scripts import run_pulseq

import common.logger as logger

log = logger.get_logger()


def pypulseq_1dse(
    inputs=None, check_timing=True, output_file="", rf_duration=100e-6
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
    TR = 250.0
    TE = 70.0
    alpha1 = 90  # flip angle
    alpha1_duration = rf_duration  # pulse duration
    alpha2 = 180  # refocusing flip angle
    alpha2_duration = rf_duration  # pulse duration
    TE = 70e-3
    TR = 250e-3
    num_averages = 1
    adc_num_samples = 4096
    adc_duration = 6.4e-3

    ch0 = "x"
    fov = 140e-3  # Define FOV and resolution
    Nx = 96
    BW = 32e3
    adc_dwell = 1 / BW
    adc_duration = Nx * adc_dwell  # 6.4e-3

    prephaser_duration = 3e-3  # TODO: Need to define this behind the scenes and optimze

    # LARMOR_FREQ = ui_inputs["LARMOR_FREQ"]
    # RF_MAX = ui_inputs["RF_MAX"]
    # RF_PI2_FRACTION = ui_inputs["RF_PI2_FRACTION"]

    # TR = inputs["TR"] / 1000
    # TE = inputs["TE"] / 1000

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

    delta_k = 1 / fov
    gx = pp.make_trapezoid(
        channel=ch0, flat_area=Nx * delta_k, flat_time=adc_duration, system=system
    )
    gx_pre = pp.make_trapezoid(
        channel=ch0, area=gx.area / 2, duration=prephaser_duration, system=system
    )
    # Define ADC events
    # adc = pp.make_adc(num_samples=adc_num_samples, delay=tau2, duration=adc_duration, system=system)
    adc = pp.make_adc(
        num_samples=Nx, duration=gx.flat_time, delay=gx.rise_time, system=system
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
        math.ceil(
            (TE / 2 - 0.5 * (pp.calc_duration(rf2)) - pp.calc_duration(gx_pre))
            / seq.grad_raster_time
        )
    ) * seq.grad_raster_time

    delay_TR = TR - TE - (0.5 * adc_duration)
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
        seq.add_block(gx, adc, pp.make_delay(delay_TR))

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
