import common.logger as logger
import common.runtime as rt
import numpy as np

from recon.kspaceFiltering.kspace_filtering import *

from recon.B0Correction import B0Corrector
import recon.DICOM.DICOM_utils as DICOM
from recon.image_filters import denoise

log = logger.get_logger()

import common.queue as queue
from common.constants import *
import common.task as task
from common.types import ScanTask

import services.recon.utils as utils
import time


def run_reconstruction(folder: str, task: ScanTask) -> bool:
    """
    Perform the reconstruction of the scan contained in the given folder. Scan information such
    as sequence, protocol name, patient information and system information can be found in the
    task object.
    """
    log.info(f"Folder where the task is = {folder}")
    log.info(f"JSON information = {task}")

    log.info(f"Starting reconstruction.")

    if task.processing.recon_mode == "fake_dicoms":
        utils.generate_fake_dicoms(folder, task)
        time.sleep(2)
        return True

    # TODO: Load the k-space data
    kData = np.load(folder + "rawdata" + "/kSpace.npy")
    kTraj = np.genfromtxt(
        r"%s/%s/trajectory.csv" % (folder), delimiter=","
    )  # pe_table a lot by 2 # check rotation

    if kTraj.shape[0] > 2:
        kTraj = np.rot90(kTraj)
    # grad_delay_correction(kData, kTraj, delayT, param)

    filterType = "fermi"
    kData = kFilter(kData, filterType, center_correction=True)
    log.info(f"kSpace {filterType} filtering finished.")

    # TODO(Zach, Shounak): Use the trajectory information and B0 map
    Y = np.ndarray
    kt = np.ndarray
    df = np.ndarray
    Lx = 1
    nonCart = None
    params = None
    b0_corrector = B0Corrector(Y, kt, df, Lx, nonCart, params)
    iData = b0_corrector()
    log.info(f"B0 correction finished.")

    try:
        iData = denoise.remove_gaussian_noise_complex(iData, method="gaussian_filter")
        log.info(f"Finished image denoising.")
    except ValueError:
        log.error(f"Image denoising failed.")

    # TODO(Lavanya): Write the DICOM file to the folder
    DICOM.write_dicom(iData, task, folder)
    log.info(f"DICOM writting finished.")

    # TODO(Radhika): Write ISMRMRD file to the folder

    return True
