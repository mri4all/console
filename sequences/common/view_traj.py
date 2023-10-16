import os
from pathlib import Path
import math
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation

from PyQt5 import uic

def view_traj(k_traj_adc, k_traj, t_excitation, t_refocusing, t_adc) -> bool:

    plt.figure()
    plt.plot(t_adc,k_traj_adc[0,:])
    plt.show()

    plt.figure()
    plt.plot(t_adc,k_traj_adc[1,:])
    plt.show()

    plt.figure()
    plt.plot(t_adc,k_traj_adc[2,:])
    plt.show()

    # First set up the figure, the axis, and the plot element we want to animate
    fig = plt.figure()
    ax = plt.axes(xlim=(), ylim=())
    line, = ax.plot([], [], lw=2)

    # initialization function: plot the background of each frame
    def init():
        line.set_data([], [])
        return line,

    # animation function.  This is called sequentially
    def animate(i):
        y = k_traj_adc(i)
        line.set_data(t_adc, y)
        return line,

    # call the animator.  blit=True means only re-draw the parts that have changed.
    anim = animation.FuncAnimation(fig, animate, init_func=init,
                                frames=200, interval=20, blit=True)

    plt.show()
    return True