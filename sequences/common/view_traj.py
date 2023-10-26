import numpy as np
from matplotlib import pyplot as plt
import pickle


def view_sig(sig, folder=""):
    recon = np.fft.fft(np.fft.fftshift(sig))
    plt.style.use("dark_background")
    fig, ax = plt.subplots(2, 1)
    ax[0].plot(np.abs(sig))
    ax[0].set_title("acq signal")
    ax[1].plot(np.abs(recon))
    ax[1].set_title("fft signal")
    if folder != "":
        file = open(folder + "/other/sig.plot", "wb")
        fig = plt.gcf()
        pickle.dump(fig, file)
        file.close()
    else:
        plt.show()


def view_traj_2d(k_traj_adc, k_traj, folder=""):
    k_traj_adc = evenly_sample_array(k_traj_adc, 10000)
    k_traj = evenly_sample_array(k_traj, 10000)

    plt.style.use("dark_background")
    # fig, ax = plt.subplots()
    fig = plt.figure()
    ax = fig.gca()
    ax.plot(k_traj[0, :], k_traj[1, :], linewidth=1)
    ax.plot(k_traj_adc[0, :], k_traj_adc[1, :], "m.", markersize=0.5)
    ax.set_aspect("equal")
    ax.set_xlabel("kx")
    ax.set_ylabel("ky")
    ax.set_title("K-space Trajactory")

    if folder != "":
        file = open(folder + "/other/traj.plot", "wb")
        fig = plt.gcf()
        pickle.dump(fig, file)
        file.close()
    else:
        plt.show()


def view_traj_3d(k_traj_adc, k_traj, folder=""):
    k_traj_adc = evenly_sample_array(k_traj_adc, 10000)
    k_traj = evenly_sample_array(k_traj, 10000)

    plt.style.use("dark_background")
    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")
    ax.plot(k_traj[0, :], k_traj[1, :], k_traj[2, :], linewidth=1)
    ax.plot(k_traj_adc[0, :], k_traj_adc[1, :], k_traj_adc[2, :], "m.", markersize=0.5)
    ax.set_aspect("equal")
    ax.set_xlabel("kx")
    ax.set_ylabel("ky")
    ax.set_zlabel("kz")
    ax.set_title("K-space Trajactory")

    if folder != "":
        file = open(folder + "/other/traj.plot", "wb")
        fig = plt.gcf()
        pickle.dump(fig, file)
        file.close()
    else:
        plt.show()


def evenly_sample_array(x, y):
    """
    Evenly sample an array 'x' so that its final length does not exceed 'y'.

    Parameters:
    x (numpy.ndarray): The input array to be sampled.
    y (int): The ideal length for the final sampled array.

    Returns:
    numpy.ndarray: The evenly sampled array with a length not exceeding 'y'.
    """
    if len(x[0]) <= y:
        # If 'x' is already shorter than or equal to 'y', return it as is.
        return x

    # Calculate the step size for sampling.
    step = len(x[0]) // y

    # Sample 'x' evenly using the calculated step size.
    sampled_x = x[:, ::step]

    return sampled_x
