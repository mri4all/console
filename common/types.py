from typing import List, Union, Optional
from typing_extensions import Literal
from pydantic import BaseModel
import matplotlib.pyplot as plt
import pydicom.uid

import common.helper as helper
from common.constants import *
import common.logger as logger

log = logger.get_logger()


class PatientInformation(BaseModel):
    # TODO: Add missing entries from registration form
    first_name: str = ""
    last_name: str = ""
    mrn: str = ""
    birth_date: str = ""
    gender: str = ""
    weight_kg: int = 0
    height_cm: int = 0
    age: int = 0

    def get_full_name(self):
        return f"{self.last_name}, {self.first_name}"

    def clear(self):
        self.first_name = ""
        self.last_name = ""
        self.mrn = ""
        self.birth_date = ""
        self.age = 0
        self.gender = ""
        self.weight_kg = 0
        self.height_cm = 0


class ExamInformation(BaseModel):
    id: str = ""
    registration_time: str = ""
    scan_counter: int = 0
    dicom_study_uid: str = ""
    patient_position: str = ""
    acc: str = ""

    def initialize(self):
        self.id = helper.generate_uid()
        self.registration_time = helper.get_datetime()
        self.dicom_study_uid: str = pydicom.uid.generate_uid()  # type: ignore
        self.scan_counter = 0
        self.patient_position = ""
        self.acc = ""

    def clear(self):
        self.id = ""
        self.scan_counter = 0
        self.dicom_study_uid = ""
        self.patient_position = ""
        self.acc = ""


class SystemInformation(BaseModel):
    name: str = "unknown"
    model: str = "unknown"
    serial_number: str = ""
    software_version: str = ""


TrajectoryType = Literal["cartesian", "radial"]


class ProcessingConfig(BaseModel):
    trajectory: TrajectoryType = "cartesian"
    recon_mode: str = ""
    denoising_strength: int = 0
    dim: Optional[int] = None
    dim_size: Optional[str] = None
    oversampling_read: Optional[int] = None


ResultTypes = Literal["dicom", "plot", "rawdata", "empty"]


class ResultItem(BaseModel):
    type: ResultTypes = "dicom"
    name: str = ""
    description: str = ""
    file_path: str = ""
    autoload_viewer: int = 0
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


class AdjustmentShim(BaseModel):
    shim_x: float = 0.0
    shim_y: float = 0.0
    shim_z: float = 0.0


class AdjustmentRF(BaseModel):
    larmor_frequency: float = 0.0
    rf_max_amplitude: float = 0.0
    rf_pi2_fraction: float = 0.0


class AdjustmentGradients(BaseModel):
    gx_max: float = 0.0
    gy_max: float = 0.0
    gz_max: float = 0.0


class AdjustmentSettings(BaseModel):
    exam_id: str = ""
    shim: AdjustmentShim = AdjustmentShim()
    rf: AdjustmentRF = AdjustmentRF()
    gradients: AdjustmentGradients = AdjustmentGradients()


class ScanTask(BaseModel):
    id: str = ""
    sequence: str = ""
    protocol_name: str = ""
    scan_number: int = 0
    system: SystemInformation = SystemInformation()
    patient: PatientInformation = PatientInformation()
    exam: ExamInformation = ExamInformation()
    parameters: dict = {}  # Contains sequence parameters (flexible content)
    adjustment: AdjustmentSettings = AdjustmentSettings()
    processing: ProcessingConfig = ProcessingConfig()
    other: dict = {}  # Contains optional parameters, such as prototypic settings
    results: List[ResultItem] = []  # Contains list of generated results
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


class IntensityMapResult(BaseModel):
    type: Literal["intensity_map"] = "intensity_map"
    data: Union[List[List[float]], List[List[List[float]]]]
    xlabel: str = ""
    ylabel: str = ""
    title: str = ""

    def show(self, axes_in=None):
        axes = axes_in
        if not axes:
            axes = plt.axes()
        axes.set_xlabel(self.xlabel)
        axes.set_ylabel(self.ylabel)
        axes.set_title(self.title)
        axes.imshow(self.data)


class TimeSeriesResult(BaseModel):
    type: Literal["time_series_result"] = "time_series_result"
    xlabel: str = ""
    ylabel: str = ""
    title: str = ""
    data: Union[List[List[float]], List[float]]
    fmt: Union[str, list[str]] = []

    def show(self, axes_in=None):
        axes = axes_in
        if not axes:
            axes = plt.axes()

        data = None
        if not isinstance(self.data[0], list):
            data = [self.data]
        else:
            data = self.data

        fmt = None
        if not isinstance(self.fmt, list):
            fmt = [self.fmt]
        else:
            fmt = self.fmt

        for i, data in enumerate(data):
            use_fmt = []
            if i < len(fmt):
                use_fmt = [fmt[i]]
            axes.plot(data, *use_fmt)

        axes.set_xlabel(self.xlabel)
        axes.set_ylabel(self.ylabel)
        axes.set_title(self.title)
        if not axes_in:
            plt.show()
