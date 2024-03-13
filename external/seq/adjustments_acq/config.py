from sequences.common.util import reading_json_parameter

# Extracting configuration
# TODO: This should be reworked
configuration_data = reading_json_parameter()

# System Larmor Frequency, in MHz
LARMOR_FREQ = configuration_data.rf_parameters.larmor_frequency_MHz
# System maximum RF amplitude, in Hz - 1e4
RF_MAX = configuration_data.rf_parameters.rf_maximum_amplitude_Hze
# Fraction of power to expect a pi/2 pulse
RF_PI2_FRACTION = configuration_data.rf_parameters.rf_pi2_fraction
# System maximum X gradient strength, in Hz/m
GX_MAX = configuration_data.gradients_parameters.gx_maximum
# System maximum Y gradient strength, in Hz/m
GY_MAX = configuration_data.gradients_parameters.gy_maximum
# System maximum Z gradient strength, in Hz/m
GZ_MAX = configuration_data.gradients_parameters.gz_maximum

SHIM_X = configuration_data.shim_parameters.shim_x
SHIM_Y = configuration_data.shim_parameters.shim_y
SHIM_Z = configuration_data.shim_parameters.shim_z
SHIM_MC = configuration_data.shim_parameters.shim_mc

DBG_FA_EXC = 90
DBG_FA_REF = 180


def update():
    global configuration_data
    global LARMOR_FREQ, RF_MAX, RF_PI2_FRACTION, GX_MAX, GY_MAX, GZ_MAX, SHIM_X, SHIM_Y, SHIM_Z, SHIM_MC

    configuration_data = reading_json_parameter()
    LARMOR_FREQ = configuration_data.rf_parameters.larmor_frequency_MHz
    RF_MAX = configuration_data.rf_parameters.rf_maximum_amplitude_Hze
    RF_PI2_FRACTION = configuration_data.rf_parameters.rf_pi2_fraction
    GX_MAX = configuration_data.gradients_parameters.gx_maximum
    GY_MAX = configuration_data.gradients_parameters.gy_maximum
    GZ_MAX = configuration_data.gradients_parameters.gz_maximum
    SHIM_X = configuration_data.shim_parameters.shim_x
    SHIM_Y = configuration_data.shim_parameters.shim_y
    SHIM_Z = configuration_data.shim_parameters.shim_z
    SHIM_MC = configuration_data.shim_parameters.shim_mc


# TODO: Needs to be revised
MGH_PATH = "/tmp"
LOG_PATH = "./server/log/"
SEQ_PATH = "./server/scanner_control/seq/"
DATA_PATH = "../data/scanner_control/data/"


# LARMOR_FREQ = 15.52 # System Larmor Frequency, in MHz
# RF_MAX = 7661.29 # System maximum RF amplitude, in Hz - 1e4
# RF_PI2_FRACTION =0.6744 # Fraction of power to expect a pi/2 pulse

# GX_MAX = 8.0e6 # System maximum X gradient strength, in Hz/m
# GY_MAX = 9.2e6 # System maximum Y gradient strength, in Hz/m
# GZ_MAX = 10e6 # System maximum Z gradient strength, in Hz/m

# SHIM_X = 0
# SHIM_Y = 0
# SHIM_Z = 0
