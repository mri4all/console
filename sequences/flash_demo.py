import os
from pathlib import Path
from PyQt5 import uic

from . import PulseqSequence


class SequenceFlash(PulseqSequence, registry_key=Path(__file__).stem):
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

    def read_parameters_from_ui(self, widget) -> bool:
        """
        Reads the settings from the UI into the sequence.
        """
        self.problem_list = []
        self.problem_list.append("TR is too short")
        self.problem_list.append("Gradient strength is too high")

        return False
