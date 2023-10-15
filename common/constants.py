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


class mri4all_files:
    LOCK = "LOCK"
    PREPARED = "PREPARED"
    EDITING = "EDITING"
    TASK = "scan.json"


class mri4all_taskdata:
    RAWDATA = "rawdata"
    DICOM = "dicom"
    OTHER = "other"


class mri4all_states:
    CREATED = "created"
    SCHEDULED_ACQ = "scheduled_acq"
    ACQ = "acq"
    SCHEDULED_RECON = "scheduled_recon"
    RECON = "recon"
    COMPLETE = "complete"
    FAILURE = "failure"
