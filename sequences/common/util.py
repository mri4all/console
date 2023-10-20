import json 
from sequences.common.pydanticConfig import Config

def reading_json_parameter():
    file_name = './sequences/common/config.json'
    with open(file_name) as file:
        data = json.load(file)
        configuration_data = Config(**data)

    return configuration_data


def writing_json_parameter(config_data):        
    file_name = './sequences/common/config.json'
    indent_size = 4
    with open(file_name, 'w') as outFile:
        outFile.write(json.dumps(config_data.model_dump(mode="json"), indent=indent_size))
            
        
        
        