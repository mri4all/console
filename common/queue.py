import os
import common.runtime as rt
import common.logger as logger


def check_data_folders() -> bool:
    # Check if data folders exist
    if not os.path.isdir(rt.base_path + "/data"):
        log.error(f"Data folder not found at {rt.base_path}/data")
        return False

    # TODO: Incomplete

    return True
