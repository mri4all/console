from . import SequenceBase


class SequenceTSE(SequenceBase, registry_key="tse"):
    @classmethod
    def get_readable_name(self) -> str:
        return "3D TSE Demo"
