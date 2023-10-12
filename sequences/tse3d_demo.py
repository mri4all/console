from . import SequenceBase
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore


class SequenceTSE(SequenceBase, registry_key=Path(__file__).stem):
    @classmethod
    def get_readable_name(self) -> str:
        return "3D TSE Demo"

    def setup_ui(self, widget) -> bool:
        """
        Returns the user inteface of the sequence.
        """

        # widget.addWidget(QPushButton("TSE"))
        return True
