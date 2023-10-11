from . import SequenceBase


class SequenceFlash(SequenceBase, registry_key="flash"):
    @classmethod
    def get_readable_name(self) -> str:
        return "2D Flash Demo"
