from sequences.common.util import reading_json_parameter
from common.config import Configuration

config = Configuration.load_from_file()
configuration_data=reading_json_parameter()
## IP address: RP address or 'localhost' if emulating a local server.
## Uncomment one of the lines below.
# ip_address = "localhost"
ip_address = config.scanner_ip #"10.42.0.251"

## Port: always 11111 for now
port = configuration_data.marcos_parameters.port #11111
# port =22

## FPGA clock frequency: uncomment one of the below to configure various
## system behaviour. Right now only 122.88 is supported.
fpga_clk_freq_MHz = configuration_data.marcos_parameters.fpga_clock_frequency_MHz #122.88 # RP-122
#fpga_clk_freq_MHz = 125.0 # RP-125

## Gradient board: uncomment one of the below to configure the gradient data format
grad_board = configuration_data.marcos_parameters.gradient_board_type #"gpa-fhdo"
#grad_board = "ocra1"     # "ocra1"

## GPA-FHDO current per volt setting (determined by resistors)
gpa_fhdo_current_per_volt = configuration_data.marcos_parameters.gpa_fhdo_current_per_volt #2.5

## Flocra-pulseq path, for use of the flocra-pulseq library (optional).
## Uncomment the lines below and adjust the path to suit your
## flocra-pulseq location.
import sys
sys.path.append(configuration_data.marcos_parameters.flocra_pulseq_path) #'./external/flocra_pulseq')