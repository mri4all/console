import os
import time
from pathlib import Path
from PyQt5 import uic

from . import PulseqSequence


class SequenceFlash(PulseqSequence, registry_key=Path(__file__).stem):
    @classmethod
    def get_readable_name(self) -> str:
        return "UI Demo: 2D Flash"

    @classmethod
    def get_description(self) -> str:
        return "Demo sequence that injects fake DICOMs for testing the UI"

    def setup_ui(self, widget) -> bool:
        seq_path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(f"{seq_path}/{self.get_name()}/interface.ui", widget)
        return True

    def read_parameters_from_ui(self, widget, scan_task) -> bool:
        self.problem_list = []
        # self.problem_list.append("TR is too short")
        # self.problem_list.append("Gradient strength is too high")

        return True

    def run_sequence(self, scan_task) -> bool:
        time.sleep(2)
        return True
