from typing import Any
from typing_extensions import Literal
from pathlib import Path
from pydantic import BaseModel

import common.helper as helper


class PatientInformation(BaseModel):
    # TODO: Add missing entries from registration form
    first_name: str = ""
    last_name: str = ""
    mrn: str = ""

    # @classmethod
    def get_full_name(self):
        return f"{self.last_name}, {self.first_name}"

    # @classmethod
    def clear(self):
        self.first_name = ""
        self.last_name = ""
        self.mrn = ""


class ExamInformation(BaseModel):
    id: str = ""
    scan_counter: int = 0

    @classmethod
    def initialize(cls):
        cls.id = helper.generate_uid()
        cls.scan_counter = 0

    @classmethod
    def clear(cls):
        cls.id = ""
        cls.scan_counter = 0


class ScanQueueEntry(BaseModel):
    id: str = ""
    sequence: str = ""
    protocol_name: str = "unknown"
    scan_counter: int = -1
    state: Literal[
        "created",
        "scheduled_acq",
        "acq",
        "scheduled_recon",
        "recon",
        "complete",
        "failure",
    ] = "created"
    has_results: bool = False
    folder: Path = Path("")


class ScanTask(BaseModel):
    id: str = ""
    sequence: str = ""
    flags: dict = {}
    exam: dict = {}
    patient: PatientInformation = PatientInformation()
    parameters: dict = {}
    adjustment: dict = {}
    system: dict = {}
    processing: dict = {}
    other: dict = {}
    results: dict = {}
