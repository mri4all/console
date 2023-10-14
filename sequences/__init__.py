from importlib import import_module
from pathlib import Path
from typing import Dict, TypeVar, Generic
import os

import common.logger as logger

log = logger.get_logger()

SequenceVar = TypeVar("SequenceVar")


class SequenceBase(Generic[SequenceVar]):
    """
    Base class for all console sequences, including automatic registry for sequence classes.
    """

    ## Internal functions for the sequence registry

    _REGISTRY: Dict[str, SequenceVar] = {}

    def __init_subclass__(cls, registry_key, **kwargs):
        super().__init_subclass__(**kwargs)
        if registry_key:
            cls._REGISTRY[registry_key] = cls
            cls.seq_name = registry_key

    seq_name = "INVALID"
    parameters: Dict = {}
    working_folder: str = ""
    calculated = False

    def __init__(self):
        pass

    @classmethod
    def get_sequence(cls, registry_key):
        return cls._REGISTRY[registry_key]

    @classmethod
    def installed_sequences(cls):
        return list(cls._REGISTRY.keys())

    ## Sequence API functions

    def get_name(self) -> str:
        """
        Returns the internal name of the sequence.
        """
        return self.seq_name

    @classmethod
    def get_readable_name(self) -> str:
        """
        Returns a human-readable name of the sequence.
        """
        return "INVALID"

    def set_parameters(self, parameters) -> bool:
        """
        Reads the sequence parameters from a JSON dictionary.
        """
        return True

    def get_parameters(self) -> dict:
        """
        Returns the current sequence parameters as JSON dict.
        """
        return {}

    def get_default_parameters(self) -> dict:
        """
        Returns a dict with default values, used to initialize the protocol.
        """
        return {}

    def setup_ui(self, widget) -> bool:
        """
        Creates the user interface of the sequence.
        """
        return True

    def write_parameters_to_ui(self, widget) -> bool:
        """
        Write the internal settings to the UI, which lives inside the widget.
        """
        return True

    def read_parameters_from_ui(self) -> bool:
        """
        Reads the settings from the UI into the sequence.
        """
        return True

    def calculate_sequence(self) -> bool:
        """
        Calculates the sequence instructions.
        """
        return True

    def run_sequence(self) -> bool:
        """
        Executes the sequence instructions (called after calculate_sequence)
        """
        return True

    def set_working_folder(self, folder: str) -> bool:
        """
        Sets the working folder for the sequence.
        """
        self.working_folder = folder

        if not os.path.isdir(folder):
            log.error(f"Sequence working folder {folder} does not exist.")
            return False

        # Check if file named scan.json exists in working_folder
        if not os.path.isfile(folder + "/scan.json"):
            log.warning(f"Could not find scan definition file scan.json in {folder}.")

        try:
            if not os.path.isdir(folder + "/seq"):
                os.mkdir(folder + "/seq")
        except:
            log.error(f"Could not create seq folder in {folder}.")
            return False

        try:
            if not os.path.isdir(folder + "/rawdata"):
                os.mkdir(folder + "/rawdata")
        except:
            log.error(f"Could not create rawdata folder in {folder}.")
            return False

        return True

    def get_working_folder(self) -> str:
        """
        Returns the working folder for the sequence.
        """
        return self.working_folder

    def is_adjustment_sequence(self) -> bool:
        """
        Returns True if the sequence is an adjustment sequence.
        """
        if self.seq_name.startswith("adj_"):
            return True
        return False

    def is_calculated(self) -> bool:
        """
        Returns True if the sequence is calculated.
        """
        return self.calculated


class PulseqSequence(SequenceBase[SequenceVar], registry_key=""):
    """
    Sublayer for all Pulseq-based sequences.
    """

    # Path and name of the .seq for simple sequence that only use one file
    seq_file_path = ""

    pass


# Automatically import all sequence classes existing in the /sequences directory.
# Sequence classes must provide only one Python file in the sequences directory,
# and it must be named the same as the class name. Helper files must be placed in a
# subdirectory to the sequence directory

for f in Path(__file__).parent.glob("*.py"):
    module_name = f.stem
    if (not module_name.startswith("_")) and (module_name not in globals()):
        import_module(f".{module_name}", __package__)
    del f, module_name
del import_module, Path
