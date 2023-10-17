import os
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, Literal, List
import json

from common import runtime
class DicomTarget(BaseModel):
    target_type: Literal["dicom"] = "dicom"
    name: str
    ip: str
    port: int
    aet_target: str
    aet_source: Optional[str] = ""

path = Path(runtime.get_base_path()) / "config/config.json"

class Configuration(BaseModel):
    dicom_targets: List[DicomTarget] = []

    @classmethod
    def load_from_file(cls):
        if not path.exists():
            k = Configuration(dicom_targets=[DicomTarget(name="target 1", ip="127.0.0.1",port=11112,aet_target="target")])
            k.save_to_file()

    
        with open(path,"r") as f:
            return cls.model_validate_json(f.read())
        
    def save_to_file(self):
        with open(path,"w") as f:
            f.write(self.model_dump_json(indent=4))
