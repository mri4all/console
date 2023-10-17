import json 
from pydanticConfig import Config

def update_json_parameter():
    with open('config.json') as file:
        data = json.load(file)
        configuration_data = Config(**data)

    print(configuration_data)
        
    ### writing ###
    #file.seek(0)
    indent_size = 4
    with open('config_test.json', 'w') as outFile:
        outFile.write(json.dumps(configuration_data.model_dump(mode="json"), indent=indent_size))
            
        
        
        