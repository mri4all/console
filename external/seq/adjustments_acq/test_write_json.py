from util import reading_json_parameter, writing_json_parameter

# read
configuration_data=reading_json_parameter(file_name='config.json')

# modify
configuration_data.rf_parameters.larmor_frequency_MHz = 15.58

# write
writing_json_parameter(config_data=configuration_data, file_name='config.json')