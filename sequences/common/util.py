import json
from sequences.common.pydanticConfig import Config, configCreator
from common import runtime
from pathlib import Path

path = Path(runtime.get_base_path()) / "config/config_acq.json"


def reading_json_parameter():
    if not path.exists():
        configuration_data = configCreator()
        with open(path, "w") as outFile:
            outFile.write(
                json.dumps(configuration_data.model_dump(mode="json"), indent=4)
            )

    with open(path) as file:
        data = json.load(file)
        configuration_data = Config(**data)

    return configuration_data


def writing_json_parameter(config_data):
    with open(path, "w") as outFile:
        outFile.write(json.dumps(config_data.model_dump(mode="json"), indent=4))
        outFile.flush()
