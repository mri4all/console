"""'
DICOM writing utils for the Reconstruction pipeline
Functions use meta information from the scan json to populate DICOM tags
"""

import numpy as np
import os
from pydicom import dcmwrite
from pydicom import Dataset
from pydicom.uid import generate_uid


def write_dicom(image_ndarray, task, folder):
    """Write DICOMS to a specified holder using information from the scan task"""

    ndarray_dims = image_ndarray.shape
    assert len(ndarray_dims) == 4  # Assumes 4D ndarray: H x W x Slices x Echoes

    SeriesInstanceUID = generate_uid(prefix=None)
    SOPClassUID = generate_uid(prefix=None)
    instance_counter = 1
    for echo_id in range(ndarray_dims[-1]):
        for slc_id in range(ndarray_dims[-2]):
            """Generate magnitude image per slice"""
            pixel_data = np.abs(image_ndarray[..., slc_id, echo_id])
            pixel_data = np.uint16(pixel_data)

            """ Create and populate the DICOM header """
            dicom_hdr = Dataset()
            dicom_hdr.Modality = "MR"
            dicom_hdr.SeriesInstanceUID = SeriesInstanceUID
            dicom_hdr.SOPClassUID = SOPClassUID
            dicom_hdr.SOPInstanceUID = (
                dicom_hdr.SeriesInstanceUID + "." + str(instance_counter)
            )
            dicom_hdr.InstanceNumber = instance_counter
            dicom_hdr.EchoNumbers = echo_id
            dicom_hdr = set_dicom_header(dicom_hdr, task)
            dicom_hdr = set_image_information(dicom_hdr, pixel_data)
            dicom_hdr = set_window_width_level(dicom_hdr, pixel_data)

            dicom_hdr.PixelData = pixel_data.tobytes()
            dicom_filename = (
                dicom_hdr.SeriesInstanceUID
                + "#"
                + str(dicom_hdr.InstanceNumber)
                + ".dcm"
            )
            dicom_file_path = os.path.join(folder, dicom_filename)
            dcmwrite(dicom_file_path, dicom_hdr)
            instance_counter = instance_counter + 1
    return


def set_dicom_header(dicom_dataset, task):
    """
    Create a dicom dataset and populate dicom header fields per slice.
    pixel_data: 2D Pixel array
    task: json object with meta data
    instance_num: Individual slice ID
    echo_num: Individual echo ID
    """
    dicom_dataset.ProtocolName = task.protocol_name
    dicom_dataset.SequenceName = task.sequence
    dicom_dataset = set_patient_information(dicom_dataset, task.patient)
    dicom_dataset = set_exam_information(dicom_dataset, task.exam)
    dicom_dataset = set_system_information(dicom_dataset, task.system)
    dicom_dataset = set_misc_information(dicom_dataset)
    dicom_dataset = set_protocol_information(dicom_dataset, task.processing)
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
    """TO DO: Fill protocol parameters TR/TE/Slice thickness etc"""
    dicom_dataset.ScanningSequence = "SE"
    dicom_dataset.SequenceVariant = ""
    dicom_dataset.ScanOptions = ""
    dicom_dataset.MRAcquisitionType = "2D"
    dicom_dataset.EchoTime = ""
    dicom_dataset.EchoTrainLength = ""
    dicom_dataset.PixelSpacing = [1.0, 1.0]
    dicom_dataset.ImageOrientation = [1, 0, 0, 0, 1, 0]
    dicom_dataset.ImagePosition = [-0.000, 265.000, 0.000]
    dicom_dataset.SliceThickness = ""

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
    dicom_dataset.is_little_endian = False
    dicom_dataset.is_implicit_VR = False
    return dicom_dataset
