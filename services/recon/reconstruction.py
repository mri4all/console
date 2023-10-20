import common.logger as logger
import common.runtime as rt
import numpy as np
import recon.kspaceFiltering.kspace_filtering as kFilter
from recon.B0Correction import B0Corrector
import recon.DICOM.DICOM_utils as DICOM
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
    log.info(f"Starting reconstruction.")

    if task.processing.recon_mode == "fake_dicoms":
        utils.generate_fake_dicoms(folder, task)
        time.sleep(2)
        return True
    
    # TODO: Load the k-space data
    kData = np.load(folder + 'rawdata' + '/kSpace.npy')

    # TODO(Bingyu): K-space filtering
    filterType = 'sine_bell'
    kData = kFilter.kspace_filtering(kData, filterType, center_correction=True)
    log.info(f"kSpace {filterType} filtering finished.")

    # TODO(Zach, Shounak): Use the trajectory information and B0 map
    Y = np.ndarray  
    kt = np.ndarray 
    df = np.ndarray 
    Lx = 1  
    nonCart = None
    params = None
    b0_corrector = B0Corrector(Y, kt, df, Lx, nonCart, params)
    iData = b0_corrector().correct_Cartesian_basic()
    log.info(f"B0 correction finished.")

    # Image denoising: TO DO

    # Write the DICOM file to the folder 
    DICOM.write_dicom(iData, task, folder)
    log.info(f"DICOM writting finished.")

    # Applicability

    # To see what's available in the JSON, take a look at common/types.py



    return True
