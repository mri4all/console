from importlib import import_module
from pathlib import Path
from typing import Dict, TypeVar, Generic
import os
import common.logger as logger

log = logger.get_logger()

SequenceVar = TypeVar("SequenceVar")


class SequenceBase(Generic[SequenceVar]):
    """
    Base class for all console sequences, with automatic registration of sequence classes.
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
    problem_list: list[str] = []
    main_widget = None
    info_widget = None

    def __init__(self):
        pass

    @classmethod
    def get_sequence(cls, registry_key):
        return cls._REGISTRY[registry_key]

    @classmethod
    def installed_sequences(cls):
        return list(cls._REGISTRY.keys())

    ## Sequence API functions. Functions that must be implemented by the individual sequence are marked with **

    def get_name(self) -> str:
        """
        Returns the internal name of the sequence.
        """
        return self.seq_name

    @classmethod
    def get_readable_name(self) -> str:
        """
        Returns a human-readable name of the sequence.
        ** Must be implemented by the individual sequence. **
        """
        return "INVALID"

    @classmethod
    def get_description(self) -> str:
        """
        Returns a description that explains what the sequences does. This is shown in the
        tooltip when hovering over a protocol.
        """
        return ""

    def get_parameters(self) -> dict:
        """
        Returns the current sequence parameters as dictionary.
        ** Must be implemented by the individual sequence. **
        """
        return {}

    @classmethod
    def get_default_parameters(self) -> dict:
        """
        Returns a dictionary with default values, used to initialize the protocol.
        ** Must be implemented by the individual sequence. **
        """
        return {}

    def set_parameters(self, parameters, scan_task) -> bool:
        """
        Reads the sequence parameters from the provided dictionary. The sequence must
        validate if the provided parameters can be used to run the sequence. If the
        parameter set is invalid, False is returned. Detected problems should be stored as
        strings in self.problem_list. The scan_task object can be used to access additional
        information about the scan, such as the hardware capabilities.
        ** Must be implemented by the individual sequence. **
        """
        return True

    def init_ui(self, widget, info_widget) -> bool:
        self.main_widget = widget
        self.info_widget = info_widget
        return self.setup_ui(widget)

    def setup_ui(self, widget) -> bool:
        """
        Creates the user interface of the sequence. The UI can be created with Qt Creator
        and loaded with uic.loadUi, or it can be created manually. The UI controls must
        be inserted into the provided widget. info_widget is a label that can be used to
        to display additional information about the sequence, such as acquisition time
        and resolution.
        ** Must be implemented by the individual sequence. **
        """
        return True

    def show_ui_info_text(self, text: str):
        if self.info_widget:
            self.info_widget.setText(text)

    def write_parameters_to_ui(self, widget) -> bool:
        """
        Loads the internal parameters into the sequence-specific UI controls inside the widget.
        This function is called when a scan protocol is opened in the UI editor.
        ** Must be implemented by the individual sequence. **
        """
        return True

    def read_parameters_from_ui(self, widget, scan_task) -> bool:
        """
        Reads the settings from the UI into the sequence and checks that the parameters are valid.
        If invalid, False is returned. The detected problems should be stored as strings in
        self.problem_list. The scan_task object can be used to access additional information about
        the scan, such as the hardware capabilities.
        ** Must be implemented by the individual sequence. **
        """
        return True

    def get_problems(self) -> list[str]:
        """
        Returns the list of problems that were detected by the sequence. These are shown in the UI.
        """
        return self.problem_list

    def calculate_sequence(self, scan_task) -> bool:
        """
        Calculates the sequence instructions using the parameters previously provided to the
        sequence instance.
        ** Must be implemented by the individual sequence. **
        """
        return True

    def run_sequence(self, scan_task) -> bool:
        """
        Executes the sequence instructions. This function is called after calculate_sequence.
        ** Must be implemented by the individual sequence. **
        """
        return True

    def set_working_folder(self, folder: str) -> bool:
        """
        Sets the working folder for the sequence. This function is called by the UI and acquisition
        service when interacting with the sequence.
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
        Returns the working folder for the sequence (provided by the framework)
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
        Returns True if the sequence is calculated and ready to be executed.
        """
        return self.calculated

    def is_valid(self) -> bool:
        """
        Returns True if the sequence parameters are valid. If not, the problems can be
        retrieved with get_problems().
        """
        return len(self.problem_list) == 0


class PulseqSequence(SequenceBase[SequenceVar], registry_key=""):
    """
    Subclass for Pulseq-based sequences, which adds Pulseq-specific functions.
    """

    # Path and name of the .seq for simple sequence that only use one file
    seq_file_path = ""


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
