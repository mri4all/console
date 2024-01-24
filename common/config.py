from pathlib import Path
from pydantic import BaseModel, Field
from typing import Dict, Optional, Literal, List

from common import runtime


def get_config():
    return mri4all_config_instance


def load_config():
    global mri4all_config_instance
    mri4all_config_instance = Configuration.load_from_file()


class DicomTarget(BaseModel):
    target_type: Literal["dicom"] = "dicom"
    name: str
    ip: str
    port: int
    aet_target: str
    aet_source: Optional[str] = ""


mri4_all_config_path = Path(runtime.get_base_path()) / "config/mri4all.json"


class Configuration(BaseModel):
    """
    Set description to "hidden" to hide the setting in the UI.
    """

    scanner_ip: str = Field(default="10.42.0.251", description="Scanner IP (internal)")
    debug_mode: str = Field(default="False", description="Debug Mode")
    hardware_simulation: str = Field(default="False", description="Hardware Simulation")
    dicom_targets: List[DicomTarget] = []

    @classmethod
    def load_from_file(cls):
        if not mri4_all_config_path.exists():
            k = Configuration(
                dicom_targets=[
                    DicomTarget(
                        name="Default",
                        ip="127.0.0.1",
                        port=11112,
                        aet_target="target",
                        aet_source="mri4all",
                    )
                ]
            )
            k.save_to_file()

        # TODO: Secure file access with LOCK file
        with open(mri4_all_config_path, "r") as f:
            return cls.model_validate_json(f.read())

    def save_to_file(self):
        # TODO: Secure writing of config file with LOCK file
        with open(mri4_all_config_path, "w") as f:
            f.write(self.model_dump_json(indent=4))

    def update(self, data: Dict):
        update = self.model_dump()
        update.update(data)
        for k, v in (
            self.model_validate(update).model_dump(exclude_defaults=True).items()
        ):
            setattr(self, k, v)
        return self

    def is_hardware_simulation(self):
        return self.hardware_simulation == "True"
