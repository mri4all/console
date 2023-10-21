import numpy as np
from typing import Optional, Any, Mapping, TypedDict

import common.logger as logger

from recon.B0Correction import OCTOPUS as oc
import recon.recon_utils as ru

# from B0Correction import OCTOPUS as oc
# import recon_utils as ru


log = logger.get_logger()

class B0Params(TypedDict):
    '''
    Parameters for B0 correction. 
    '''
    Npoints: int
    Nshots: int
    N: int
    dcf: np.ndarray
    t_vector: np.ndarray
    t_readout: float
    

class B0Corrector:
    '''
    B0 trajectory correction for reconstruction calling from OCTOPUS.
    
    https://github.com/imr-framework/OCTOPUS/tree/master
    '''
    def __init__(self, 
                 Y: np.ndarray, 
                 kt: np.ndarray, 
                 df: Optional[np.ndarray], 
                 Lx: int=1,
                 nonCart: Optional[bool]=None, 
                 params: Optional[B0Params]=None):
        
        self.Y = Y  # raw k-space (rads)
        self.kt = kt  # k-space trajectory, acq times for each frequency encode (s) 
        self.df = df  # delta B0 field map (Hz) 
        self.Lx = Lx  # number of basis images to use for conjugate phase methods
        self.nonCart = nonCart # non-Cartesian trajectory?
        self.params = params  # trajectory parameters for B0 correction
                    
    def __call__(self) -> np.ndarray:
        if self.df is None:  # if no B0, directly perform ifft
            return self.direct_recon()
        
        return self.correct_MFI()  # default method
    
    
    def direct_recon(self) -> np.ndarray: 
        '''
        Directly reconstruct raw k-space data given trajectory.
        '''
        if not self.nonCart: 
            log.info("Performing n-dim IFFT reconstruction")
            return ru.centered_ifft(self.Y)
        
        log.info("Performing non-Cartesian reconstruction") 
        cartesian_opt = 0
        NufftObj = oc.imtransforms.nufft_init(self.kt, self.params)
        return oc.imtransforms.ksp2im(self.Y, cartesian_opt, NufftObj, self.params)
    
    def correct_MFI(self) -> np.ndarray: 
        '''
        Doc from OCTOPUS for MFI: 
        
        Off-resonance Correction by Multi-Frequency Interpolation
        Man, L., Pauly, J. M. and Macovski, A. (1997), Multifrequency interpolation for fast off‐resonance correction. Magn. Reson. Med., 37: 785-792. doi:10.1002/mrm.1910370523

        Parameters
        ----------
        dataIn : numpy.ndarray
            k-space raw data or image data
        dataInType : str
            Can be either 'raw' or 'im'
        kt : numpy.ndarray
            k-space trajectory
        df : numpy.ndarray
            Field map
        Lx : int
            L (frequency bins) factor
        nonCart : int
            Non-cartesian trajectory option. Default is None (Cartesian).
        params : dict
            Sequence parameters. Default is None.
        Returns
        -------
        M_hat : numpy.ndarray
            Corrected image data.
        '''
        log.info("Running multi-frequency interpolation for off-resonance corrected reconstruction")
        if len(self.Y.shape) <= 2:
            return oc.MFI(self.Y, 'raw', self.kt, self.df, Lx=self.Lx, nonCart=self.nonCart, params=self.params) 
        elif len(self.Y.shape)  == 3:
            mfi_img = np.zeros(self.Y.shape)
            for i in range(self.Y.shape[2]):
                 mfi_img[..., i] = oc.MFI(self.Y[..., i], self.kt, self.df[..., i], Lx=1, nonCart=False, params=self.params) 
            return mfi_img
        else:
            raise ValueError(f'Input data shape {self.Y.shape} not supported')
