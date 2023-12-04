from asyncio.locks import _ContextManagerMixin
import os
import sys

sys.path.append("/opt/mri4all/console/external/")

import signal
import asyncio
import common.logger as logger
import common.runtime as rt

rt.set_service_name("acq")
log = logger.get_logger()
sys.stdout = logger.LoggerStdCapture(log.info)
sys.stderr = logger.LoggerStdCapture(log.warning)

from common.ipc import Communicator
import common.helper as helper
from common.types import ScanTask, ScanJournal
import common.task as task
from sequences import SequenceBase

from common.version import mri4all_version
import common.queue as queue
from common.constants import *
import common.plotting as plotting
import common.config as config

main_loop = None  # type: helper.AsyncTimer # type: ignore

communicator = Communicator(Communicator.ACQ)


def move_to_fail(scan_name: str) -> bool:
    if not queue.move_task(
        mri4all_paths.DATA_ACQ + "/" + scan_name, mri4all_paths.DATA_FAILURE
    ):
        log.error(f"Failed to move scan {scan_name} to failure folder. Critical Error.")
        return False
    return True


def process_acquisition(scan_name: str) -> bool:
    log.info("Performing acquisition...")

    # Reload the configuration to get the latest settings
    config.load_config()
    plotting.set_plotting_defaults()

    # Check if json file with task definition exists in the scan folder
    if not os.path.isfile(
        mri4all_paths.DATA_ACQ + "/" + scan_name + "/" + mri4all_files.TASK
    ):
        log.error(
            f"Scan {scan_name} does not contain a scan.json file. Unable to process."
        )
        move_to_fail(scan_name)
        return False

    try:
        scan_task = task.read_task(mri4all_paths.DATA_ACQ + "/" + scan_name)
    except:
        log.error(f"Failed to read task file for scan {scan_name}. Unable to process.")
        move_to_fail(scan_name)
        return False

    log.info(f"Requested sequence: {scan_task.sequence}")
    if not (scan_task.sequence in SequenceBase.installed_sequences()):
        log.error(f"Requested sequence not installed. Unable to process.")
        move_to_fail(scan_name)
        return False

    scan_task.journal.acquisition_start = helper.get_datetime()
    task.write_task(mri4all_paths.DATA_ACQ + "/" + scan_name, scan_task)

    # Clear the seq subfolder to remove any .seq file from previous test runs
    task.clear_task_subfolder(
        mri4all_paths.DATA_ACQ + "/" + scan_name, mri4all_taskdata.SEQ
    )

    current_step = ""
    try:
        current_step = "instantiation"
        seq_instance = SequenceBase.get_sequence(scan_task.sequence)()
        current_step = "set_working_folder"
        seq_instance.set_working_folder(str(mri4all_paths.DATA_ACQ + "/" + scan_name))
        current_step = "set_parameters"
        if not seq_instance.set_parameters(scan_task.parameters, scan_task):
            raise Exception("Invalid protocol used to initialize sequence.")
        current_step = "calculate_sequence"
        if not seq_instance.calculate_sequence(scan_task):
            raise Exception("Sequence did not calculate successfully.")
        current_step = "run_sequence"
        if not seq_instance.run_sequence(scan_task):
            raise Exception("Sequence did not run successfully.")
    except Exception as e:
        log.error(
            f"Failed to run sequence {scan_task.sequence}. Failure during step {current_step}."
        )
        log.exception(e)

        scan_task.journal.failed_at = helper.get_datetime()
        scan_task.journal.fail_stage = "acquisition"
        task.write_task(mri4all_paths.DATA_ACQ + "/" + scan_name, scan_task)
        move_to_fail(scan_name)
        communicator.send_status(f"Scan failed.")
        return False

    scan_task.journal.acquisition_end = helper.get_datetime()
    task.write_task(mri4all_paths.DATA_ACQ + "/" + scan_name, scan_task)

    # Clear the tmp subfolder to remove any temporary files from interactive scanning
    task.clear_task_subfolder(
        mri4all_paths.DATA_ACQ + "/" + scan_name, mri4all_taskdata.TEMP
    )

    log.info("Acquisition completed with success.")
    if not queue.move_task(
        mri4all_paths.DATA_ACQ + "/" + scan_name, mri4all_paths.DATA_QUEUE_RECON
    ):
        log.error(f"Failed to move scan {scan_name} to recon queue. Critical Error.")
    return True


def run_acquisition_loop():
    """
    Main processing function that is called continuously by the main loop
    """
    selected_scan = queue.get_scan_ready_for_acq()
    if selected_scan:
        log.info(f"Processing scan: {selected_scan}")
        rt.set_current_task_id(selected_scan)

        if not queue.move_task(
            mri4all_paths.DATA_QUEUE_ACQ + "/" + selected_scan, mri4all_paths.DATA_ACQ
        ):
            log.error(
                f"Failed to move scan {selected_scan} to acq folder. Unable to run acquisition."
            )
        else:
            process_acquisition(selected_scan)

        rt.clear_current_task_id()

    if helper.is_terminated():
        return


async def terminate_process(signalNumber, frame) -> None:
    """
    Triggers the shutdown of the service
    """
    log.info("Shutdown requested")
    # Note: main_loop can be read here because it has been declared as global variable
    if "main_loop" in globals() and main_loop.is_running:
        main_loop.stop()
    helper.trigger_terminate()


def prepare_acq_service() -> bool:
    """
    Prepare the acquisition service
    """
    log.info("Preparing for acquisition...")

    if not queue.check_and_create_folders():
        log.error("Failed to create data folders. Unable to start acquisition service.")
        return False

    # Clear the data acquisition folder, in case a previous instance has crashed. If a task
    # is found there, move it to the failure folder (probably the previous instance crashed)
    if not queue.clear_folder(mri4all_paths.DATA_ACQ, mri4all_paths.DATA_FAILURE):
        return False

    return True


def run():
    log.info(f"-- MRI4ALL {mri4all_version.get_version_string()} --")
    log.info("Acquisition service started")

    if not prepare_acq_service():
        log.error("Error while preparing acquisition service. Terminating.")
        sys.exit(1)

    # Register system signals to be caught
    signals = (signal.SIGTERM, signal.SIGINT)
    for s in signals:
        helper.loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(terminate_process(s, helper.loop))
        )

    # Start the timer that will periodically trigger the scan of the task folder
    global main_loop

    main_loop = helper.AsyncTimer(0.1, run_acquisition_loop)
    try:
        main_loop.run_until_complete(helper.loop)
    except Exception as e:
        log.exception(e)
    finally:
        # Finish all asyncio tasks that might be still pending
        remaining_tasks = helper.asyncio.all_tasks(helper.loop)  # type: ignore[attr-defined]
        if remaining_tasks:
            helper.loop.run_until_complete(helper.asyncio.gather(*remaining_tasks))

    log.info("Acquisition service terminated")
    log.info("-------------")
    sys.exit()


if __name__ == "__main__":
    run()
