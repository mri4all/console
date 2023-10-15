from typing import Any
from typing_extensions import Literal
from pathlib import Path
from pydantic import BaseModel

import common.helper as helper
from common.constants import *


class PatientInformation(BaseModel):
    # TODO: Add missing entries from registration form
    first_name: str = ""
    last_name: str = ""
    mrn: str = ""

    def get_full_name(self):
        return f"{self.last_name}, {self.first_name}"

    def clear(self):
        self.first_name = ""
        self.last_name = ""
        self.mrn = ""


class ExamInformation(BaseModel):
    id: str = ""
    scan_counter: int = 0

    def initialize(self):
        self.id = helper.generate_uid()
        self.scan_counter = 0

    def clear(self):
        self.id = ""
        self.scan_counter = 0


class SystemInformation(BaseModel):
    name: str = "unknown"
    model: str = "unknown"
    serial_number: str = ""
    software_version: str = ""


ScanStatesType = Literal[
    "created", "scheduled_acq", "acq", "scheduled_recon", "recon", "complete", "failure", "invalid"
]


class ScanQueueEntry(BaseModel):
    id: str = ""
    sequence: str = ""
    protocol_name: str = "unknown"
    scan_counter: int = -1
    state: ScanStatesType = "created"
    has_results: bool = False
    folder_name: str = ""


class ScanTask(BaseModel):
    id: str = ""
    sequence: str = ""
    protocol_name: str = ""
    flags: dict = {}  # TODO
    exam: dict = {}  # TODO
    patient: PatientInformation = PatientInformation()
    parameters: dict = {}
    adjustment: dict = {}  # TODO
    system: SystemInformation = SystemInformation()
    processing: dict = {}  # TODO
    other: dict = {}
    results: dict = {}  # TODO
