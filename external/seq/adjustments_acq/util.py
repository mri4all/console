import json 
from pydanticConfig import Config

def update_json_parameter():
    with open('config_test.json', 'r+') as file:
        data = json.load(file)
        configuration_data = Config(**data)
        
        ### writing ###
        file.seek(0)
        indent_size = 4
        json.dumps(configuration_data.model_dump(mode="json"),
                   file,
                   indent=indent_size)
            
        
        
        