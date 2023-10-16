import os
from pathlib import Path
import math
import numpy as np
from matplotlib import pyplot

from PyQt5 import uic

import pypulseq as pp  # type: ignore

def view_traj(k_traj_adc, k_traj, t_excitation, t_refocusing, t_adc) -> bool:
    [k_traj_adc, k_traj, t_excitation, t_refocusing, t_adc] = sequence_instance.seq.calculate_kspace()

    pyplot.figure()
    pyplot.plot(t_adc,k_traj_adc)

    return True