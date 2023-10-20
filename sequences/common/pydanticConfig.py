from pydantic import BaseModel
from typing import List

### rf_parameters section
class RfParameters(BaseModel):
    larmor_frequency_MHz: float = 0.0
    rf_maximum_amplitude_Hze: float = 0.0
    rf_pi2_fraction: float = 0.0

### gradients_parameters section
class GradientsParameters(BaseModel):
    gx_maximum: float = 0.0
    gy_maximum: float = 0.0
    gz_maximum: float = 0.0

### shim_parameters section
class ShimParameters(BaseModel):
    shim_x: float = 0.0
    shim_y: float = 0.0
    shim_z: List[float] = []

### marcos_parameters section
class MarcosParameters(BaseModel):
    ip_adress: str = "default_ip_adress"
    port: int = 0
    fpga_clock_frequency_MHz: float = 0.0
    gradient_board_type: str = "default gradient_board_type"
    gpa_fhdo_current_per_volt: float = 2.5
    flocra_pulseq_path: str = "default flocra_pulseq_path"

##############################################
### main definition of the configuration files
class Config(BaseModel):
    rf_parameters: RfParameters
    gradients_parameters: GradientsParameters
    shim_parameters: ShimParameters
    marcos_parameters: MarcosParameters()
