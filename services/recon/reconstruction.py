import numpy as np
import os
from os import path
import time
import matplotlib.pyplot as plt

import common.logger as logger
from common.constants import *
from common.types import ScanTask
import services.recon.utils as utils

from recon.kspaceFiltering.kspace_filtering import *
from recon.B0Correction import B0Corrector
import recon.DICOM.DICOM_utils as DICOM
from recon.ismrmrd.numpy_to_ismrmrd import create_ismrmrd
from recon.image_filters import denoise

log = logger.get_logger()


def run_reconstruction(folder: str, task: ScanTask) -> bool:
    """
    Perform the reconstruction of the scan contained in the given folder. Scan information such
    as sequence, protocol name, patient information and system information can be found in the
    task object.
    """
    # log.info(f"Folder where the task is = {folder}")
    # log.info(f"JSON information = {task}")

    if task.processing.recon_mode == "bypass":
        log.info("Bypassing reconstruction")
        return True

    if task.processing.recon_mode == "fake_dicoms":
        log.info("Generating fake DICOMs")
        utils.generate_fake_dicoms(folder, task)
        time.sleep(1)
        return True

    if task.processing.recon_mode == "basic3d":
        log.info("Running Basic 3D reconstruction")
        run_reconstruction_basic3d(folder, task)
        return True

    if task.processing.trajectory == "cartesian":
        log.info("Running Cartesian reconstruction")
        run_reconstruction_cartesian(folder, task)
        return True

    log.error(f"Unknown trajectory type: {task.processing.trajectory}")
    return False


def run_reconstruction_basic3d(folder: str, task: ScanTask) -> bool:
    if task.processing.dim != 3:
        log.error(
            "Unable to perform reconstruction. This algorithm only support 3 dimensions"
        )
        return False

    order = np.load(
        folder + "/" + mri4all_taskdata.RAWDATA + "/" + mri4all_scanfiles.PE_ORDER
    )
    adc_phases = np.load(
        folder + "/" + mri4all_taskdata.RAWDATA + "/" + mri4all_scanfiles.ADC_PHASE
    )
    kData = np.load(
        folder + "/" + mri4all_taskdata.RAWDATA + "/" + mri4all_scanfiles.RAWDATA
    )
    dims = task.processing.dim_size.split(",")
    # dim = slices:pe:read

    # Simple recon
    # kData = np.reshape(kData, (int(dims[1]) * int(dims[0]), int(dims[2])))
    # kData = np.reshape(kData, (int(dims[1]), int(dims[0]), int(dims[2])))
    # kData = np.transpose(kData, axes=[2, 0, 1])
    # kSpace = kData.copy()

    # Index-based recon
    kData = np.reshape(kData, (int(dims[1]) * int(dims[0]), int(dims[2])))
    log.info(f"Readout size = {kData.shape}")
    kSpace = np.zeros(dtype=complex, shape=(int(dims[2]), int(dims[1]), int(dims[0])))
    log.info(f"Matrix size = {kSpace.shape}")

    center_slc = kSpace.shape[2] - int(kSpace.shape[2] / 2)
    center_pe = kSpace.shape[1] - int(kSpace.shape[1] / 2)
    max_slc = kSpace.shape[2]
    max_pe = kSpace.shape[1]

    counter = 0
    for line in order:
        # kSpace[200:511, center_pe - line[0], center_slc - line[1]] = kData[
        #     counter, 200:511
        # ]

        # Remove phase offset, if RF spoiling has been used
        adc_phase = adc_phases[counter] / 180.0 * np.pi

        kSpace[
            :, (center_pe - line[0]) % max_pe, (center_slc - line[1]) % max_slc
        ] = kData[counter, :] * np.exp(adc_phase * 1j)
        counter += 1

    fft = np.fft.fftshift(np.fft.fftn(np.fft.fftshift(kSpace)))

    base_res = fft.shape[0]
    for sample in range(0, base_res):
        fft[sample, :, :] = fft[sample, :, :] * np.exp(
            # np.pi * 1j + base_res / 16 * (sample - base_res / 2) / (2 * base_res) * np.pi * 1j
            np.pi * 1j
            + (sample - base_res / 2) / 32 * np.pi * 1j
        )

    if task.processing.oversampling_read > 0:
        offset = int(dims[2]) / 4
        fft = fft[int(offset) : int(3 * offset), :, :]

    DICOM.write_dicom(fft, task, folder + "/" + mri4all_taskdata.DICOM, result_index=0)

    # kSpace = np.angle(kSpace)
    kSpace = 100 * (kSpace - kSpace.min()) / (kSpace.max() - kSpace.min())
    DICOM.write_dicom(
        kSpace,
        task,
        folder + "/" + mri4all_taskdata.DICOM,
        series_offset=1,
        name="k-Space",
        primary_result=False,
        autoload_viewer=2,
        result_index=2,
    )

    DICOM.write_dicom(
        np.angle(fft),
        task,
        folder + "/" + mri4all_taskdata.DICOM,
        series_offset=2,
        name="Phase",
        primary_result=False,
        result_index=3,
        autoload_viewer=3,
    )

    return True


def run_reconstruction_cartesian(folder: str, task: ScanTask):
    """
    Runs the reconstruction pipeline for Cartesian sampling
    """
    fnames = os.listdir(folder)
    if not fnames:
        log.error(f"Folder {folder} is empty.")
        return

    # Load the k-space data
    kData = np.load(
        folder + "/" + mri4all_taskdata.RAWDATA + "/" + mri4all_scanfiles.RAWDATA
    )
    kTraj = np.genfromtxt(
        folder + "/" + mri4all_taskdata.RAWDATA + "/" + mri4all_scanfiles.TRAJ,
        delimiter=",",
    )  # pe_table a lot by 2 # check rotation

    if kTraj.shape[0] > 2:
        kTraj = np.rot90(kTraj)
    # grad_delay_correction(kData, kTraj, delayT, param)

    filterType = "fermi"
    kData = kFilter(kData, filterType, center_correction=True)
    log.info(f"kSpace {filterType} filtering finished.")

    # Preform B0 correction and reconstruct the image
    fname_B0_map = list(filter(lambda x: mri4all_scanfiles.BDATA in x, fnames))
    Y = kData
    kt = kTraj
    df = np.load(path.join(folder, fname_B0_map[0])) if fname_B0_map else None
    Lx = 1
    nonCart = None
    params = None
    b0_corrector = B0Corrector(Y, kt, df, Lx, nonCart, params)
    iData = b0_corrector()
    log.info(f"B0 correction finished.")

    # Denoise the image
    try:
        strength = task.processing.denoising_strength
        iData = denoise.remove_gaussian_noise_complex(
            iData, method="gaussian_filter", strength=strength
        )
        log.info(f"Finished image denoising with strength={strength}.")
    except ValueError:
        log.error(f"Image denoising failed.")

    # Create the DICOM file
    DICOM.write_dicom(iData, task, folder + "/" + mri4all_taskdata.DICOM)
    log.info(f"DICOM writting finished.")

    # Create the ISMRMRD file
    # TODO: Enable ISMRMRD creation after bug fix
    create_ismrmrd(folder, kData, task)
    log.info(f"ISMRMRD format writting finished.")
