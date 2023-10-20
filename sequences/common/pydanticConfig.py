from pydantic import BaseModel
from typing import List
from pathlib import Path
from common import runtime

### rf_parameters section
class RfParameters(BaseModel):
    larmor_frequency_MHz: float = 15.58
    rf_maximum_amplitude_Hze: float = 7661.29
    rf_pi2_fraction: float = 0.6744

### gradients_parameters section
class GradientsParameters(BaseModel):
    gx_maximum: float = 8000000.0
    gy_maximum: float = 9000000.0
    gz_maximum: float = 10000000.0

### shim_parameters section
class ShimParameters(BaseModel):
    shim_x: float = 0.0
    shim_y: float = 0.0
    shim_z: float = 0.0
    shim_mc: List[float] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

### marcos_parameters section
class MarcosParameters(BaseModel):
    port: int = 11111
    fpga_clock_frequency_MHz: float = 122.8
    gradient_board_type: str = "gpa-fhdo"
    gpa_fhdo_current_per_volt: float = 2.5
    flocra_pulseq_path: str = "./external/flocra_pulseq"

##############################################
### main definition of the configuration files

path = Path(runtime.get_base_path()) / "config/config_acq.json"

class Config(BaseModel):
    rf_parameters: RfParameters
    gradients_parameters: GradientsParameters
    shim_parameters: ShimParameters
    marcos_parameters: MarcosParameters

def configCreator():
    config_data = Config(rf_parameters={}, gradients_parameters={}, shim_parameters={}, marcos_parameters={})
    config_data.rf_parameters = RfParameters()
    config_data.gradients_parameters = GradientsParameters()
    config_data.shim_parameters = ShimParameters()
    config_data.marcos_parameters = MarcosParameters()
    return config_data

