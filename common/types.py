from pydantic import BaseModel


class PatientInformation(BaseModel):
    first_name: str
    last_name: str
    mrn: str

    @classmethod
    def get_full_name(cls):
        return f"{cls.last_name}, {cls.first_name}"
