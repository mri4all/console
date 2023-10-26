from sequences.common.util import reading_json_parameter

# Extracting configuration
configuration_data=reading_json_parameter()
LARMOR_FREQ = configuration_data.rf_parameters.larmor_frequency_MHz # System Larmor Frequency, in MHz
RF_MAX = configuration_data.rf_parameters.rf_maximum_amplitude_Hze # System maximum RF amplitude, in Hz - 1e4
RF_PI2_FRACTION = configuration_data.rf_parameters.rf_pi2_fraction # Fraction of power to expect a pi/2 pulse

GX_MAX = configuration_data.gradients_parameters.gx_maximum # System maximum X gradient strength, in Hz/m
GY_MAX = configuration_data.gradients_parameters.gy_maximum # System maximum Y gradient strength, in Hz/m
GZ_MAX = configuration_data.gradients_parameters.gz_maximum # System maximum Z gradient strength, in Hz/m

SHIM_X = configuration_data.shim_parameters.shim_x
SHIM_Y = configuration_data.shim_parameters.shim_y
SHIM_Z = configuration_data.shim_parameters.shim_z
SHIM_MC = configuration_data.shim_parameters.shim_mc

# LARMOR_FREQ = 15.52 # System Larmor Frequency, in MHz
# RF_MAX = 7661.29 # System maximum RF amplitude, in Hz - 1e4
# RF_PI2_FRACTION =0.6744 # Fraction of power to expect a pi/2 pulse

# GX_MAX = 8.0e6 # System maximum X gradient strength, in Hz/m
# GY_MAX = 9.2e6 # System maximum Y gradient strength, in Hz/m
# GZ_MAX = 10e6 # System maximum Z gradient strength, in Hz/m

# SHIM_X = 0
# SHIM_Y = 0
# SHIM_Z = 0

# MGH_PATH = 'PATH/TO/mgh/DIR'
# LOG_PATH = 'PATH/TO/PROGRAM/LOG/DIR'
# SEQ_PATH = 'PATH/TO/SEQ/FILES/DIR'
# DATA_PATH = 'PATH/TO/DATA/OUTPUT/DIR'

MGH_PATH = '/Users/sairamgeethanath/Documents/Projects/Tools/Low_field/OSI/console/seq'
LOG_PATH = './server/log/'
SEQ_PATH = './server/scanner_control/seq/'
DATA_PATH = '../data/scanner_control/data/'
