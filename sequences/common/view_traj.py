import os
from pathlib import Path
import math
import numpy as np
from matplotlib import pyplot as plt
import matplotlib as mpl
from pypulseq.Sequence import parula

from PyQt5 import uic

def view_traj_2d(k_traj_adc, k_traj) -> bool:
    plt.figure()
    plt.plot(k_traj[0,:], k_traj[1,:],'b',linewidth=1)
    plt.plot(k_traj_adc[0,:], k_traj_adc[1,:], 'r.',markersize=0.5)
    plt.show()  # Display the plots

    return True