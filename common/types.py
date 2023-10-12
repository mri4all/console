from pydantic import BaseModel
import common.helper as helper


class PatientInformation(BaseModel):
    # TODO: Add missing entries from registration form
    first_name: str
    last_name: str
    mrn: str

    @classmethod
    def get_full_name(cls):
        return f"{cls.last_name}, {cls.first_name}"

    @classmethod
    def clear(cls):
        cls.first_name = ""
        cls.last_name = ""
        cls.mrn = ""


class ExamInformation(BaseModel):
    id: str
    scan_counter: int

    @classmethod
    def initialize(cls):
        cls.id = helper.generate_uid()
        cls.scan_counter = 0

    @classmethod
    def clear(cls):
        cls.id = ""
        cls.scan_counter = 0
