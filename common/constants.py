import common.runtime as rt


class mri4all_defs:
    SEP = "#"


class mri4all_paths:
    BASE = rt.get_base_path()
    DATA = BASE + "/data"
    DATA_ACQ = DATA + "/acq"
    DATA_RECON = DATA + "/recon"
    DATA_QUEUE_ACQ = DATA + "/queue_acq"
    DATA_QUEUE_RECON = DATA + "/queue_recon"
    DATA_COMPLETE = DATA + "/complete"
    DATA_FAILURE = DATA + "/failure"
    DATA_ARCHIVE = DATA + "/archive"


class mri4all_files:
    LOCK = "LOCK"
    PREPARED = "PREPARED"
    TASK = "scan.json"


class mri4all_taskdata:
    RAWDATA = "rawdata"
    DICOM = "dicom"
    OTHER = "other"
