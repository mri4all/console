import sys
import signal
import asyncio
import common.logger as logger
import common.runtime as rt
import common.helper as helper
from sequences import rfse, rftse, adj_frequency

rt.set_service_name("acq")
log = logger.get_logger()

from common.version import mri4all_version

main_loop = None  # type: helper.AsyncTimer # type: ignore


def run_acquisition_loop():
    log.debug("Acquisition loop triggered")
    # log.debug("This is a debug message")
    # rt.set_current_task_id("1234")


async def terminate_process(signalNumber, frame) -> None:
    """
    Triggers the shutdown of the service
    """
    log.info("Shutdown requested")
    # Note: main_loop can be read here because it has been declared as global variable
    if "main_loop" in globals() and main_loop.is_running:
        main_loop.stop()
    helper.trigger_terminate()


def run(test_all_sequences: bool = False):
    log.info(f"-- MRI4ALL {mri4all_version.get_version_string()} --")
    log.info("Acquisition service started")

    # Register system signals to be caught
    signals = (signal.SIGTERM, signal.SIGINT)
    for s in signals:
        helper.loop.add_signal_handler(s, lambda s=s: asyncio.create_task(terminate_process(s, helper.loop)))

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
