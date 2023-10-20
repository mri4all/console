import common.logger as logger
import common.runtime as rt
import numpy as np
import recon.kspaceFiltering.kspace_filtering as kFilter
import recon.B0Correction.B0Corrector as b0correction
from recon.DICOM import DICOM_utils as DICOM
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
    log.info("Hello recon team, here is your entry point!")
    log.info(f"Folder where the task is = {folder}")
    log.info(f"JSON information = {task}")
    log.info(f"Access data in the JSON like this: {task.protocol_name}")

    
    ## data_loading{folder}
    ## reshape ksapce using trajectory
    ## if partial_fourier 
    ## test 
    filterType = 'sine_bell'
    kData = np.load('/vagrant/test_data_kspace_d1s1B0_shift49us.npy')
    kData = kFilter.kspace_filtering(kData, filterType, center_correction=True)
    log.info(f"kSpace {filterType} filtering finished.")
    iData = b0correction.correct_Cartesian_basic(kData, kTraj, iB0map)
    log.info(f"B0 correction finished.")
    ## b0correction.correct_Cartesian_basiccorrect_MFI
    DICOM.write_dicom(iData, task, folder)
    log.info(f"DICOM writting finished.")

    # To see what's available in the JSON, take a look at common/types.py

    if task.processing.recon_mode == "fake_dicoms":
        utils.generate_fake_dicoms(folder, task)
        time.sleep(2)

    return True
