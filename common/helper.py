from pathlib import Path
import uuid
import asyncio
import inspect
from typing import Optional
import datetime


def generate_uid() -> str:
    """Generate a new UUID and return it as string. The UUID is used to identify exams and scan tasks."""
    new_uuid = str(uuid.uuid1())
    return new_uuid


def get_datetime() -> str:
    """
    Returns the current time as ISO 8601 formatted string, which should be used in JSON files.
    """
    return datetime.datetime.now().isoformat()


class FileLock:
    """Helper class that implements a file lock. The lock file will be removed also from the destructor so that
    no spurious lock files remain if exceptions are raised."""

    def __init__(self, path_for_lockfile: Path):
        self.lockfile = path_for_lockfile
        # TODO: Handle case if lock file cannot be created
        self.lockfile.touch(exist_ok=False)
        self.lockCreated = True

    # Destructor to ensure that the lock file gets deleted
    # if the calling function is left somewhere as result
    # of an unhandled exception
    def __del__(self) -> None:
        self.free()

    def free(self) -> None:
        if self.lockCreated:
            self.lockfile.unlink()
            self.lockCreated = False


# Global variable to broadcast when the process should terminate
terminate_process = False
loop = asyncio.get_event_loop()


def trigger_terminate() -> None:
    """Trigger that the processing loop should terminate after finishing the currently active task."""
    global terminate_process
    terminate_process = True


def is_terminated() -> bool:
    """Checks if the process will terminate after the current task."""
    return terminate_process


class AsyncTimer(object):
    def __init__(self, interval: float, func):
        self.func = func
        self.time = interval
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    def start(self) -> None:
        if not self.is_running:
            self.is_running = True
            # Start task to call func periodically:
            self._task = asyncio.ensure_future(self._run())

    def stop(self) -> None:
        """Signal to stop after the current"""
        self.is_running = False

    async def _run(self) -> None:
        global terminate_process
        while self.is_running:
            await asyncio.sleep(self.time)
            if terminate_process:
                self.stop()

            if not self.is_running:
                break

            if inspect.isawaitable(res := self.func()):
                await res

    def run_until_complete(self, loop=None) -> None:
        self.start()
        loop = loop or asyncio.get_event_loop()
        loop.run_until_complete(self._task)
