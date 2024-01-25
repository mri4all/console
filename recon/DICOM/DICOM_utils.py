"""'
DICOM writing utils for the Reconstruction pipeline
Functions use meta information from the scan json to populate DICOM tags
"""

import numpy as np
import os
from pydicom.uid import generate_uid
from pydicom.uid import UID
from pydicom.uid import ImplicitVRLittleEndian
import datetime
from pydicom.dataset import FileDataset, FileMetaDataset
from common.types import ResultItem
from common.constants import *


def write_dicom(
    image_ndarray,
    task,
    folder,
    series_offset=0,
    name="",
    description="",
    primary_result=True,
    autoload_viewer=1,
    result_index=0,
):
    """
    Write DICOMS to a specified holder using information from the scan task

    Parameters:
    image_ndarray: multi-dimensional (3D) reconstructed complex array
    task: scan task object with scan-specific information
    folder: location to save the DICOM data per slice
    """
    ndarray_dims = image_ndarray.shape
    assert len(ndarray_dims) == 3  # Assumes 3D ndarray: H x W x Slices
    studyInstanceUID = task.exam.dicom_study_uid
    seriesInstanceUID = generate_uid()
    # Temporary trick to avoid series collision: multiply scan number by 100 and add offset for addition dicom series
    # TODO: Needs better solution to keep track of all DICOM series
    seriesNumber = task.scan_number * 100 + series_offset

    instance_counter = 1
    print(f"Writing {ndarray_dims[-1]} DICOMs")

    val_max = np.max(np.abs(image_ndarray))

    for slc_id in range(ndarray_dims[-1]):
        # Generate magnitude image per slice
        # Normalize the value range to avoid clipping (max 32k)
        pixel_data = np.abs(image_ndarray[..., slc_id]) / val_max * 30000
        pixel_data = np.uint16(pixel_data)

        """ Create and populate the DICOM header """
        dicom_dataset = set_dicom_header(
            studyInstanceUID, seriesInstanceUID, instance_counter, task
        )
        dicom_dataset = set_image_information(dicom_dataset, pixel_data)
        dicom_dataset = set_window_width_level(dicom_dataset, pixel_data)
        dicom_dataset.PixelData = pixel_data.tobytes()
        dicom_filename = (
            "series"
            + str(seriesNumber).zfill(5)
            + "#"
            + str(instance_counter).zfill(5)
            + ".dcm"
        )
        dicom_dataset.file_meta.TransferSyntaxUID = ImplicitVRLittleEndian
        dicom_file_path = os.path.join(folder, dicom_filename)
        dicom_dataset.save_as(dicom_file_path)
        instance_counter = instance_counter + 1

    result = ResultItem()
    result.name = name
    if not result.name:
        result.name = "Reconstruction"
    result.description = description
    if not result.description:
        result.description = "DICOM series from sequence " + str(task.sequence)
    result.type = "dicom"
    result.primary = primary_result
    result.autoload_viewer = autoload_viewer
    result.file_path = (
        mri4all_taskdata.DICOM + "/" + "series" + str(seriesNumber).zfill(5) + "#"
    )
    task.results.insert(result_index, result)
    return


def set_dicom_header(StudyInstanceUID, SeriesInstanceUID, instance_num, task):
    """
    Create a dicom dataset and populate dicom header fields per slice.
    Parameters:
    StudyInstanceUID: UID for the Study, shared across all scans
    SeriesInstanceUID: UID generated uniquely for the
    instance_num: Individual slice instance
    task: task object
    """

    file_meta = FileMetaDataset()
    SOPInstanceUID = UID(SeriesInstanceUID + "." + str(instance_num))
    file_meta.MediaStorageSOPClassUID = StudyInstanceUID
    file_meta.MediaStorageSOPInstanceUID = SOPInstanceUID
    file_meta.ImplementationClassUID = UID("1.2.3.4")
    SeriesNumber = task.scan_number
    dicom_filename = "Series_" + str(SeriesNumber) + "#" + str(instance_num) + ".dcm"
    dicom_dataset = FileDataset(
        dicom_filename, {}, file_meta=file_meta, preamble=b"\0" * 128
    )

    dicom_dataset.ProtocolName = task.protocol_name
    dicom_dataset.SequenceName = task.sequence
    dicom_dataset.SeriesInstanceUID = SeriesInstanceUID
    dicom_dataset.SOPClassUID = StudyInstanceUID
    dicom_dataset.SOPInstanceUID = SOPInstanceUID
    dicom_dataset.InstanceNumber = instance_num

    dt = datetime.datetime.now()
    dicom_dataset.ContentDate = dt.strftime("%Y%m%d")
    timeStr = dt.strftime("%H%M%S.%f")  # long format with micro seconds
    dicom_dataset.ContentTime = timeStr

    dicom_dataset = set_patient_information(dicom_dataset, task.patient)
    dicom_dataset = set_exam_information(dicom_dataset, task.exam)
    dicom_dataset = set_system_information(dicom_dataset, task.system)
    dicom_dataset = set_parameters(dicom_dataset, task.parameters, instance_num)
    dicom_dataset = set_misc_information(dicom_dataset)
    # dicom_dataset = set_protocol_information(dicom_dataset, task.processing)
    return dicom_dataset


def set_patient_information(dicom_dataset, PatientInformation):
    """Use the Patient information to populate the DICOM header"""
    dicom_dataset.PatientName = PatientInformation.get_full_name()
    dicom_dataset.PatientID = PatientInformation.mrn
    dicom_dataset.PatientBirthDate = PatientInformation.birth_date
    dicom_dataset.Sex = PatientInformation.gender
    dicom_dataset.PatientWeight = PatientInformation.weight_kg
    dicom_dataset.PatientSize = PatientInformation.height_cm
    return dicom_dataset


def set_exam_information(dicom_dataset, ExamInformation):
    """Use the Exam information to populate the DICOM header"""
    dicom_dataset.StudyInstanceUID = ExamInformation.dicom_study_uid
    dicom_dataset.SeriesNumber = ExamInformation.scan_counter
    dicom_dataset.AccessionNumber = ExamInformation.acc
    return dicom_dataset


def set_system_information(dicom_dataset, SystemInformation):
    """Use the System information to populate the DICOM header"""
    dicom_dataset.Manufacturer = SystemInformation.name
    dicom_dataset.ManufacturerModelName = SystemInformation.model
    dicom_dataset.DeviceSerialNumber = SystemInformation.serial_number
    dicom_dataset.SoftwareVersions = SystemInformation.software_version
    return dicom_dataset


def set_protocol_information(dicom_dataset, ProtocolInformation):
    """TO DO: Fill protocol parameters"""

    return dicom_dataset


def set_parameters(dicom_dataset, parameters, instance_num):
    """Fill sequence parameter information in DICOM header"""
    dicom_dataset.Modality = "MR"
    dicom_dataset.MagneticFieldStrength = 0.048
    dicom_dataset.ScanningSequence = "TSE"
    dicom_dataset.SequenceVariant = ""
    dicom_dataset.ScanOptions = ""
    dicom_dataset.MRAcquisitionType = "2D"
    # TODO: Check for existence of parameters in the dict
    # dicom_dataset.EchoTime = parameters['TE']
    # dicom_dataset.RepetitionTime = parameters['TR']
    # dicom_dataset.FlipAngle = parameters['flipangle']
    # dicom_dataset.MRAcquisitionFrequencyEncodingSteps = parameters['baseresolution']
    dicom_dataset.EchoTrainLength = ""
    # These are placeholders and would be updated when shared by the UI
    dicom_dataset.PixelSpacing = [1.0, 1.0]
    dicom_dataset.ImageOrientation = [1, 0, 0, 0, 1, 0]
    dicom_dataset.ImagePosition = [-0.000, 265.000, 0.000]
    dicom_dataset.SliceThickness = 2
    dicom_dataset.SliceLocation = 0.0 + (instance_num * 0.5)
    return dicom_dataset


def set_adjustment_information(dicom_dataset, adjustments):
    """TO DO: Fill information from adjustments if relevant"""

    return dicom_dataset


def set_institution_information(dicom_dataset, InstitutionInformation):
    # TO DO: This information currently does not exist in json
    dicom_dataset.InstitutionName = InstitutionInformation.InstitutionName
    dicom_dataset.InstitutionalDepartmentName = "Department of Radiology"
    dicom_dataset.InstitutionAddress = InstitutionInformation.InstitutionAddress
    dicom_dataset.ReferringPhysicianName = InstitutionInformation.tPerfPhysiciansName
    dicom_dataset.PhysicianOfRecord = InstitutionInformation.tPerfPhysiciansName
    dicom_dataset.PerformingPhysicianName = InstitutionInformation.tPerfPhysiciansName
    return dicom_dataset


def set_window_width_level(dicom_dataset, pixel_data):
    """Calculate the window width and window level for the current image"""
    maxPixel = np.max(pixel_data)
    minPixel = np.min(pixel_data)
    midPixel = (maxPixel + minPixel) / 2
    windowCenter = (midPixel + np.mean(pixel_data)) / 2
    windowWidthL = np.round(windowCenter - minPixel)
    windowWidthR = np.round(maxPixel - windowCenter)
    if windowWidthR > windowWidthL:
        windowWidth = windowWidthR
    else:
        windowWidth = windowWidthL

    dicom_dataset.WindowCenter = windowCenter
    dicom_dataset.WindowWidth = windowWidth
    dicom_dataset.RescaleIntercept = 0
    dicom_dataset.RescaleSlope = 1
    return dicom_dataset


def set_image_information(dicom_dataset, pixel_data):
    """Calculate other image related parameters to be updated in the DICOM header"""
    dicom_dataset.Rows = pixel_data.shape[0]
    dicom_dataset.Columns = pixel_data.shape[1]
    return dicom_dataset


def set_misc_information(dicom_dataset):
    """Image array information
    TO DO: Any post-processed image should have different header informationn"""
    dicom_dataset.ImageType = ["ORIGINAL", "PRIMARY", "OTHER"]
    dicom_dataset.SamplesPerPixel = 1
    dicom_dataset.PhotometricInterpretation = "MONOCHROME2"
    dicom_dataset.PixelRepresentation = 1
    dicom_dataset.BitsAllocated = 16
    dicom_dataset.BitsStored = 16
    dicom_dataset.HighBit = 15
    dicom_dataset.is_little_endian = True
    dicom_dataset.is_implicit_VR = True
    dicom_dataset.SpecificCharacterSet = "ISO_IR 100"
    return dicom_dataset
