import common.config as config


def get_ip_address():
    """
    Fetch the current IP address from the MRI4ALL configuration file.
    Note: Because the marcos files import the configuration file via
    "from ... import ...", multiple copied of the variable are created
    within different scopes and it won't be possible to change these
    values during runtime. Thus, changes only become effective after
    restarting the software stack.
    """
    dummy_config = config.Configuration.load_from_file()
    return dummy_config.scanner_ip


## IP address: RP address or 'localhost' if emulating a local server.
## Uncomment one of the lines below.
ip_address = get_ip_address()

## Port: always 11111 for now
port = 11111

## FPGA clock frequency: uncomment one of the below to configure various
## system behaviour. Right now only 122.88 is supported.
# fpga_clk_freq_MHz = 122.88 # RP-122
# fpga_clk_freq_MHz = 125.0 # RP-125
fpga_clk_freq_MHz = 122.88

## Gradient board: uncomment one of the below to configure the gradient data format
# grad_board = "ocra1" or "gpa-fhdo"
grad_board = "gpa-fhdo"

## GPA-FHDO current per volt setting (determined by resistors)
gpa_fhdo_current_per_volt = 2.5

## Flocra-pulseq path, for use of the flocra-pulseq library (optional).
## Uncomment the lines below and adjust the path to suit your
## flocra-pulseq location.
import sys

sys.path.append("/opt/mri4all/external/flocra_pulseq")
