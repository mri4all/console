from util import reading_json_parameter, writing_json_parameter

configuration_data=reading_json_parameter(file_name='config.json')
writing_json_parameter(config_data=configuration_data, file_name='config.json')