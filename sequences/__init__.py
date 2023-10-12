from importlib import import_module
from pathlib import Path
from typing import Dict, TypeVar, Generic


SequenceVar = TypeVar("SequenceVar")


class SequenceBase(Generic[SequenceVar]):
    """
    Base class for all console sequences, including automatic registry for sequence classes.
    """

    ## Internal functions for the sequence registry

    _REGISTRY: Dict[str, SequenceVar] = {}

    def __init_subclass__(cls, registry_key, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._REGISTRY[registry_key] = cls
        cls.seq_name = registry_key

    seq_name = "INVALID"

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

    def setup_ui(self, widget) -> bool:
        """
        Returns the user inteface of the sequence.
        """
        return True


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
