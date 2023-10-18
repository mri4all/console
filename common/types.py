from typing import Any
from typing_extensions import Literal
from pathlib import Path
from pydantic import BaseModel

import pydicom.uid

import common.helper as helper
from common.constants import *


class PatientInformation(BaseModel):
    # TODO: Add missing entries from registration form
    first_name: str = ""
    last_name: str = ""
    mrn: str = ""
    acc: str = ""
    birth_date: str = ""
    gender: str = ""
    weight_kg: int = 0
    height_cm: int = 0

    def get_full_name(self):
        return f"{self.last_name}, {self.first_name}"

    def clear(self):
        self.first_name = ""
        self.last_name = ""
        self.mrn = ""

        self.acc = ""
        birth_date = ""
        gender = ""
        weight_kg = 0
        height_cm = 0


class ExamInformation(BaseModel):
    id: str = ""
    scan_counter: int = 0
    dicom_study_uid: str = ""

    def initialize(self):
        self.id = helper.generate_uid()
        self.dicom_study_uid: str = pydicom.uid.generate_uid()
        self.scan_counter = 0

    def clear(self):
        self.id = ""
        self.scan_counter = 0
        self.dicom_study_uid = ""


class SystemInformation(BaseModel):
    name: str = "unknown"
    model: str = "unknown"
    serial_number: str = ""
    software_version: str = ""


TrajectoryType = Literal["cartesian", "radial"]


class ProcessingConfig(BaseModel):
    trajectory: TrajectoryType = "cartesian"
    kspace_dim: int = 0
    kspace_ordering: str = ""  # TODO: Decide where this is coming from


ResultTypes = Literal["dicom", "plot", "rawdata"]


class ResultItem(BaseModel):
    type: ResultTypes
    name: str = ""
    file_path: str = ""
    autoload_viewer: int
    primary: bool = False


FailStages = Literal[
    "preparation", "adjustment", "acquisition", "reconstruction", "other", "none"
]


class ScanJournal(BaseModel):
    created_at: str = ""
    prepared_at: str = ""
    acquisition_start: str = ""
    acquisition_end: str = ""
    reconstruction_start: str = ""
    reconstruction_end: str = ""
    failed_at: str = ""
    fail_stage: FailStages = "none"


class ScanTask(BaseModel):
    id: str = ""
    sequence: str = ""
    protocol_name: str = ""
    system: SystemInformation = SystemInformation()
    patient: PatientInformation = PatientInformation()
    exam: ExamInformation = ExamInformation()
    parameters: dict = {}  # TODO
    adjustment: dict = {}  # TODO
    processing: ProcessingConfig = ProcessingConfig()
    other: dict = {}
    results: dict = {}  # TODO
    journal: ScanJournal = ScanJournal()


ScanStatesType = Literal[
    "created",
    "scheduled_acq",
    "acq",
    "scheduled_recon",
    "recon",
    "complete",
    "failure",
    "invalid",
]


class ScanQueueEntry(BaseModel):
    id: str = ""
    sequence: str = ""
    protocol_name: str = "unknown"
    scan_counter: int = -1
    state: ScanStatesType = "created"
    has_results: bool = False
    folder_name: str = ""
    description: str = ""
