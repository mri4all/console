import os
from pathlib import Path
import math
import numpy as np
from matplotlib import pyplot as plt
import matplotlib as mpl
from pypulseq.Sequence import parula

from PyQt5 import uic

def view_sig(sig):
    recon = np.fft.fft(np.fft.fftshift(sig))
    plt.style.use("dark_background")
    fig, ax = plt.subplot(1,2)
    ax[0,0].plot(np.abs(sig))
    ax[0,0].title("acq signal")
    ax[0,1].plot(np.abs(recon))
    ax[0,1].title("fft signal")
    plt.show()

def view_traj_2d(k_traj_adc, k_traj):
    plt.style.use("dark_background")
    # fig, ax = plt.subplots()
    fig = plt.figure()
    ax = fig.gca()
    ax.plot(k_traj[0,:], k_traj[1,:],linewidth=1)
    ax.plot(k_traj_adc[0,:], k_traj_adc[1,:], 'm.',markersize=0.5)
    ax.set_aspect('equal')
    ax.set_xlabel('kx')
    ax.set_ylabel('ky')
    ax.set_title('K-space Trajactory')
    plt.show()  # Display the plots
    # plt.figure()
    # plt.style.use("dark_background")
    # plt.plot(k_traj[0,:], k_traj[1,:],color='b',linewidth=1)
    # plt.plot(k_traj_adc[0,:], k_traj_adc[1,:], color ='r',marker='.',markersize=0.5)
    # plt.axis('equal')
    # plt.xlabel('kx')
    # plt.ylabel('ky')
    # plt.title('K-space Trajactory')
    # plt.show()  # Display the plots

def view_traj_3d(k_traj_adc, k_traj):
    plt.style.use("dark_background")
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    ax.plot(k_traj[0,:], k_traj[1,:], k_traj[2,:],linewidth=1)
    ax.scatter(k_traj_adc[0,:], k_traj_adc[1,:], k_traj_adc[2,:])
    ax.set_aspect('equal')
    ax.set_xlabel('kx')
    ax.set_ylabel('ky')
    ax.set_zlabel('kz')
    ax.set_title('K-space Trajactory')
    plt.show()  # Display the plots