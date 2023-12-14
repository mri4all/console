from enum import Enum
import common.runtime as rt


class mri4all_defs:
    SEP = "#"


class mri4all_paths:
    BASE = rt.get_base_path()
    DATA = BASE + "/data"
    DATA_QUEUE_ACQ = DATA + "/acq_queue"
    DATA_ACQ = DATA + "/acq"
    DATA_QUEUE_RECON = DATA + "/recon_queue"
    DATA_RECON = DATA + "/recon"
    DATA_COMPLETE = DATA + "/complete"
    DATA_FAILURE = DATA + "/failure"
    DATA_ARCHIVE = DATA + "/archive"
    DATA_STATE = DATA + "/state"


class mri4all_files:
    LOCK = "LOCK"
    PREPARED = "PREPARED"
    EDITING = "EDITING"
    STOP = "STOP"
    TASK = "scan.json"


class mri4all_scanfiles:
    RAWDATA = "raw.npy"
    PE_ORDER = "pe_order.npy"
    ADC_PHASE = "adc_phase.npy"
    TRAJ = "traj.csv"  # csv format with rows: z phase encode, columns: y phase encodes
    BDATA = "B0.npy"


class mri4all_taskdata:
    SEQ = "seq"
    RAWDATA = "rawdata"
    DICOM = "dicom"
    TEMP = "temp"
    OTHER = "other"


class mri4all_states:
    CREATED = "created"
    SCHEDULED_ACQ = "scheduled_acq"
    ACQ = "acq"
    SCHEDULED_RECON = "scheduled_recon"
    RECON = "recon"
    COMPLETE = "complete"
    FAILURE = "failure"


class Service(Enum):
    ACQ_SERVICE = "mri4all_acq"
    RECON_SERVICE = "mri4all_recon"


class ServiceAction(Enum):
    START = "start"
    STOP = "stop"
    KILL = "kill"
    STATUS = "status"
