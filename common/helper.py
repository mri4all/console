from pathlib import Path
import uuid


def generate_uid() -> str:
    """Generate a new UUID and return it as string. The UUID is used to identify exams and scan tasks."""
    new_uuid = str(uuid.uuid1())
    return new_uuid


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
