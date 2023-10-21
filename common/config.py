import os
from pathlib import Path
from pydantic import BaseModel
from typing import Dict, Optional, Literal, List
import json

from common import runtime


class DicomTarget(BaseModel):
    target_type: Literal["dicom"] = "dicom"
    name: str
    ip: str
    port: int
    aet_target: str
    aet_source: Optional[str] = ""


path = Path(runtime.get_base_path()) / "config/mri4all.json"


class Configuration(BaseModel):
    scanner_ip: str = "10.42.0.251"
    dicom_targets: List[DicomTarget] = []
    # bar_string: str = ""
    # foo_int: int = 0

    @classmethod
    def load_from_file(cls):
        if not path.exists():
            k = Configuration(
                dicom_targets=[
                    DicomTarget(
                        name="Default", ip="127.0.0.1", port=11112, aet_target="target"
                    )
                ]
            )
            k.save_to_file()

        with open(path, "r") as f:
            return cls.model_validate_json(f.read())

    def save_to_file(self):
        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=4))

    def update(self, data: Dict) -> "Configuration":
        update = self.model_dump()
        update.update(data)
        for k, v in (
            self.model_validate(update).model_dump(exclude_defaults=True).items()
        ):
            setattr(self, k, v)
        return self
