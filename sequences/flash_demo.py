import os
from pathlib import Path
from PyQt5 import uic

from . import SequenceBase


class SequenceFlash(SequenceBase, registry_key=Path(__file__).stem):
    @classmethod
    def get_readable_name(self) -> str:
        return "2D Flash Demo"

    def setup_ui(self, widget) -> bool:
        """
        Returns the user inteface of the sequence.
        """
        seq_path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(f"{seq_path}/{self.get_name()}/interface.ui", widget)
        return True
